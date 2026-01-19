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
  _CROP_RIGHT = 1.0 - (0.20) # How much of the image to crop off the right side | NOTE: Change the parentheses value.
  _CROP_TOP = 0.1 # How much of the image to crop off the top side
  _CROP_BOTTOM = 1.0 - (0.1) # How much of the image to crop off the bottom side | NOTE: Change the parentheses value.
  _MAX_VERTICAL_GAP = 500 # px

  # ================ Private Functions ================

  def _threadedFarm(self):
    """
    Background farming loop with fixed-rate scheduling
    """

    self.is_processing = True
    self.stop_event.clear()
    try:
      interval = random.uniform(self.lower_bound, self.upper_bound)
      next_time = time.time()
      Logger.log(App._LOG_HEADER, f"First run scheduled in {interval:.2f}s")

      while self.running:
        now = time.time()
        sleep_time = next_time - now

        # Wait, but can be interrupted
        if sleep_time > 0:
          self.stop_event.wait(timeout=sleep_time)
        
        # Stop immediately if requested
        if not self.running or self.stop_event.is_set():
          break

        start = time.time()
        clicked = self._autoFarm()
        end = time.time()

        runtime = end - start

        # Schedule next run
        interval = random.uniform(self.lower_bound, self.upper_bound)
        next_time += interval

        # Catch up if OCR ran long
        if next_time < time.time():
          Logger.log(App._LOG_HEADER, f"OCR overran interval (runtime={runtime:.2f}s), rescheduling")
          next_time = time.time() + interval

        delay = max(0.0, next_time - time.time())
        Logger.log(App._LOG_HEADER, f"Cycle done | Clicked={clicked} | Runtime={runtime:.2f}s | Next run in {delay:.2f}s")

    finally:
      self.is_processing = False
      Logger.log(App._LOG_HEADER, "Thread exited cleanly")
  

  def _autoFarm(self) -> bool:
    """
    Autoclicks the Farm button with the given parameters

    :return: Success status of the click?
    :type: bool
    """

    # Check if function should run
    if not self.found: return False

    # Get discord texture & find text
    screenshot = self.window_manager.getWindowTextureFromHwnd(self.target_hwnd)
    img_height, img_width = screenshot.shape[:2]

    # ---- Crop bounds ----
    left   = int(img_width * App._CROP_LEFT)
    right  = int(img_width * App._CROP_RIGHT)
    top    = int(img_height * App._CROP_TOP)       # New: crop top
    bottom = int(img_height * App._CROP_BOTTOM)    # New: crop bottom

    # Crop the screenshot
    cropped_screenshot = screenshot[top:bottom, left:right]

    # Run OCR on cropped image
    all_text = ElementDetector.detectText(cropped_screenshot)
    if not all_text: return False

    # Leave function if stop button was pressed
    if not self.is_processing: return False

    # Shift boxes back to original screenshot coordinates
    chat_elements = []
    for text, box in all_text:
      x_min, y_min, x_max, y_max = box
      shifted_box = (x_min + left, y_min + top, x_max + left, y_max + top)
      chat_elements.append((text, shifted_box))


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

          # One last processing check
          if not self.is_processing or not self.running or (self.stop_event and self.stop_event.is_set()):
            Logger.log(App._LOG_HEADER, "Stopped signal detected, skipping click")
            return False

          self.auto_gui.click(click_target)
          return True  # Found and clicked
    
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

    self.click_interval = None
    self.is_processing = False
    self.stop_event = threading.Event()

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
      Logger.log(App._LOG_HEADER, f"Started Bot ==> Player: {self.target_player} | Lower: {self.lower_bound} | Upper: {self.upper_bound}")
      self.start_time = time.time()
      self.updateButtonText()
      threading.Thread(target=self._threadedFarm, daemon=True).start() # Start running the farm



  def onStop(self):
    """
    Ran when the start/stop button is toggled to the "stop" state
    """

    # Check if timer is valid
    if self.timer_job is not None:
      self.after_cancel(self.timer_job)
      self.timer_job = None

    self.start_time = None
    Logger.log(App._LOG_HEADER, "Stopped Bot")

    # Signal the thread to exit immediately
    self.running = False
    self.stop_event.set()


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
  