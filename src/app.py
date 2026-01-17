import os
import time
import random
import threading
import tkinter as tk
from tkinter import ttk

from src.logger import Logger
from src.auto_gui import AutoGui
from src.window_manager import WindowManager
from src.element_detector import ElementDetector


class App(tk.Tk):
  """
  Main GUI Application for the Virtual Farmer AFK Bot.

  **Purpose:**
    Automates the 'farm' action in Discord by detecting specific player 
    messages and clicking the associated 'farm' button using OCR and 
    simulated mouse input.
  
  **Usage:**
    1. Enter the target Player Name as it appears in Discord.
    2. Set the minimum and maximum random delay bounds.
    3. Ensure Discord is open and click 'Start'.
  """

  # ==================== Variables ====================

  _LOG_HEADER: str = "App"
  _TARGET_EXE = "Discord.exe" # NOTE: Change this if you changed Discord's executable filename

  # Bounds for Discord
  _FARM_BUTTON_TEXT = "farm"
  _DISCORD_COMMAND_TEXT = "used /"
  _CROP_LEFT = 0.15 # How much of the image to crop off the left side
  _CROP_RIGHT = 1.0 - (0.20) # How much of the image to crop off the right side
  _MAX_VERTICAL_GAP = 500 # px

  # ================ Private Functions ================

  def _threadedFarm(self):
    """
    Wrapper that runs in the background thread
    """

    self.is_processing = True
    try:
      self._autoFarm()
    finally:
      # Always set to False, even if _autoFarm crashes
      self.is_processing = False
  

  def _autoFarm(self) -> bool:
    """
    Autoclicks the Farm button with the given parameters

    :return: Success status of the click?
    :type: bool
    """

    # Check if function should run
    if not self.found: return
    if (self.click_interval is not None) and \
      (time.time() - self.last_click < self.click_interval):
      return

    # Calculate new click interval
    self.click_interval = random.uniform(self.lower_bound, self.upper_bound)


    # Get discord texture & find text
    screenshot = self.window_manager.getWindowTextureFromHwnd(self.target_hwnd)
    all_text = ElementDetector.detectText(screenshot)
    if not all_text: return

    img_width = screenshot.shape[1]
    chat_elements = []
    for text, box in all_text:
      # TODO: Update to remove the need for these bounds
      # Adjust these percentages if your Discord layout is different
      # Ignores the left 15% and right 20% of the screen
      x_min = box[0]
      if (img_width * App._CROP_LEFT) < x_min < (img_width * App._CROP_RIGHT):
        chat_elements.append((text, box))


    # Search bottom-up for the most recent message in the chat
    sorted_elements = sorted(chat_elements, key=lambda x: x[1][1])
    for i in range(len(sorted_elements) - 1, -1, -1):
      text, box = sorted_elements[i]
      clean_text = text.lower()
      
      # Avoid headers: Look for the name inside the embed
      if self.target_player not in clean_text or App._DISCORD_COMMAND_TEXT in clean_text:
        continue

      player_y_top = box[1]
      player_x_center = (box[0] + box[2]) / 2
      
      # Look DOWN for the button
      for j in range(i + 1, len(sorted_elements)):
        btn_text, btn_box = sorted_elements[j]
        btn_clean = btn_text.lower().strip()

        # Stop if we leave the embed area
        if (btn_box[1] - player_y_top) > App._MAX_VERTICAL_GAP:
          break
        
        # Ensure the button is the right text
        if btn_clean != App._FARM_BUTTON_TEXT:
          continue

        # Only click if button is horizontally aligned with the name
        btn_x_center = (btn_box[0] + btn_box[2]) / 2
        if abs(btn_x_center - player_x_center) < 200:
          # Define the button's click area (inner 60% of the button to be safe)
          half_width = (btn_box[2] - btn_box[0]) * 0.3
          half_height = (btn_box[3] - btn_box[1]) * 0.3

          # Add random jitter so we don't click the same pixel twice
          jitter_x = random.uniform(-half_width, half_width)
          jitter_y = random.uniform(-half_height, half_height)

          click_target = (
            int(btn_x_center + jitter_x), 
            int(((btn_box[1] + btn_box[3]) / 2) + jitter_y)
          )

          Logger.log(App._LOG_HEADER, f"Clicking with jitter at: {click_target}")
          self.auto_gui.click(click_target)
          self.last_click = time.time()
          return True # Found and clicked
    
    return False


  def _formatDuration(self, seconds: float) -> str:
    """
    Smart duration formatting:
    - < 1 minute: show seconds with 1 decimal (e.g., 12.3s)
    - >= 1 minute and < 1 hour: show m s (e.g., 1m 12s)
    - >= 1 hour: show h m (e.g., 2h 3m)

    :param seconds: Total seconds to format
    :type seconds: float
    :return: String formatting for time
    :rtype: str
    """

    # Do simple formatting for time less than 1 minute   
    if seconds < 60:
      return f"{seconds:.1f}s"

    # Calculate secs, mins, and hours
    total = int(seconds)
    s = total % 60
    m = (total // 60) % 60
    h = total // 3600

    # Use minutes, seconds when time has not passed 1 hour.
    if h > 0:
      return f"{h}h {m}m"
    else:
      return f"{m}m {s}s"


  def _findExeWindow(self, windows, target_exe: str) -> tuple[str, int]:
    """
    Finds a window given it's exe name

    :param windows: List of Windows returned by WindowManager.gatherOpenWindows()
    :param target_exe: Target exe name
    :type target_exe: str
    :return: Title of the discord exe target
    :rtype: str
    """
    # Gather open windows
    

    # Loop through every found window
    for hwnd, title in (w for w in windows if not self.found):
      # Check if the current hwnd's exe is the target exe
      full_exe_path = self.window_manager.getExecutableFromHwnd(hwnd)
      exe = os.path.basename(full_exe_path)

      if exe == target_exe:
        # Mark as found and log
        Logger.log(self._LOG_HEADER, f"Found {target_exe}!")
        self.found = True
        return title, hwnd
    
    # Nothing found, return empty string and 0
    return "", 0


  # ================ Constructors ================


  def __init__(self):
    """
    Setup a new App
    """

    # Init super class
    super().__init__()

    # Set window params
    self.title("Virtual Farmer AFK Bot")
    self.resizable(False, False)
    self.configure(bg="black", padx=15, pady=15)

    # Class-private vars
    self.running = False
    self.start_time = None
    self.timer_job = None

    # ============= ttk Styles =============
    style = ttk.Style(self)
    style.theme_use("default")

    style.configure(
      "Dark.TEntry",
      fieldbackground="#3a3a3a",
      background="#3a3a3a",
      foreground="white",
      insertcolor="white"
    )

    label_style = {"bg": "black", "fg": "white"}

    # --- Player Name ---
    tk.Label(self, text="Player Name =", **label_style).grid(row=0, column=0, sticky="w", pady=(0, 5))
    self.player_entry = ttk.Entry(self, width=25, style="Dark.TEntry")
    self.player_entry.grid(row=0, column=1, columnspan=3, sticky="w", pady=(0, 5))
    self.player_entry.insert(0, "PlayerName") # Starting value

    # --- Rand bounds ---
    tk.Label(self, text="Rand min (s) =", **label_style).grid(row=1, column=0, sticky="w")
    self.min_entry = ttk.Entry(self, width=10, style="Dark.TEntry")
    self.min_entry.grid(row=1, column=1, sticky="w", pady=(0, 5))
    self.min_entry.insert(0, "2.5") # Starting value

    tk.Label(self, text="Rand max (s) =", **label_style).grid(row=2, column=0, sticky="w")
    self.max_entry = ttk.Entry(self, width=10, style="Dark.TEntry")
    self.max_entry.grid(row=2, column=1, sticky="w")
    self.max_entry.insert(0, "4.5") # Starting value

    # --- Start / Stop Button ---
    self.toggle_button = tk.Button(
      self,
      text="Start",
      bg="green",
      fg="white",
      activeforeground="white",
      width=20,
      command=self.toggleStartButton
    )
    self.toggle_button.grid(row=3, column=0, columnspan=4, pady=15)


    # ---------- Find Discord Window ----------

    # Create a window manager
    self.window_manager = WindowManager()

    # Find Discord window
    self.found = False
    windows = self.window_manager.gatherOpenWindows()
    self.target_title, self.target_hwnd = self._findExeWindow(windows, App._TARGET_EXE)
    self.auto_gui = AutoGui(self.target_title) if self.found else None

    self.last_click = time.time()
    self.click_interval = None
    self.is_processing = False

    self.lower_bound = 2.5
    self.upper_bound = 4.5
    self.target_player = "Player"
    


  # ================ Public Functions ================

  def toggleStartButton(self):
    """
    Ran when the start/stop button is toggled
    """

    # Toggle running boolean
    self.running = not self.running

    # Run onStart/onStart depending on running state
    if self.running:
      self.toggle_button.config(bg="red")
      self.onStart()
    else:
      self.toggle_button.config(bg="green", text="Start")
      self.onStop()


  def onStart(self):
    """
    Ran when the start/stop button is toggled to the "start" state
    """

    # Get params
    self.target_player = self.player_entry.get()
    try:
      self.lower_bound = float(self.min_entry.get())
      self.upper_bound = float(self.max_entry.get())
    except ValueError:
      Logger.log(App._LOG_HEADER, "Invalid number entered for random bounds!")
      self.toggleStartButton() # Revert UI state
      return # STOP execution here

    # Start timers
    if self.start_time is None:
      self.start_time = time.time()
      self.updateButtonText()
      self.scheduleNextFarm()

    Logger.log(App._LOG_HEADER, f"Started Bot ==> Player: {self.target_player} | Lower: {self.lower_bound} | Upper: {self.upper_bound}")


  def onStop(self):
    """
    Ran when the start/stop button is toggled to the "stop" state
    """

    # Check if timer is valid
    if self.timer_job is not None:
      self.after_cancel(self.timer_job)
      self.timer_job = None

    # Reset start time
    self.start_time = None
    Logger.log(App._LOG_HEADER, "Stopped Bot")


  def updateButtonText(self):
    """
    Updates the main logic of the game.
    """

    # Ensure app is actually running
    if not self.running or self.start_time is None: return

    elapsed = time.time() - self.start_time
    self.toggle_button.config(text=f"Stop ({self._formatDuration(elapsed)})")

    # Delay job
    delay: int = 100 if elapsed < 60 else 1_000
    self.timer_job = self.after(delay, self.updateButtonText)
  

  def scheduleNextFarm(self):
    """
    Handles 'When' to click
    """
    if not self.running: return

    # If the previous OCR thread is still running, skip this tick
    if not self.is_processing:
      # Create and start the thread
      # daemon=True ensures the thread dies when you close the app
      threading.Thread(target=self._threadedFarm, daemon=True).start()

    # Calculate next delay and schedule
    new_interval = random.uniform(self.lower_bound, self.upper_bound)
    self.after(int(new_interval * 1000), self.scheduleNextFarm)
