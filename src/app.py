import time
import random
import tkinter as tk
from tkinter import ttk
from src.logger import Logger


class App(tk.Tk):
  """ TODO
  App Class

  **Purpose:**
    does this
  
  **Usage:**
    do this
  ----------
  """

  # ==================== Variables ====================

  _LOG_HEADER: str = "App"

  # ================ Private Functions ================


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

    if self.start_time is None:  # <-- only set once
      self.start_time = time.time()
      self.update()


    # Get input box variables
    target_player = self.player_entry.get()
    try:
      lower_bound = float(self.min_entry.get())
      upper_bound = float(self.max_entry.get())
    except ValueError:
      Logger.log("Invalid number entered for random bounds!")

    Logger.log(App._LOG_HEADER, f"Started Bot ==> Player: {target_player} | Lower: {lower_bound} | Upper: {upper_bound}")


  def onStop(self):
    """
    Ran when the start/stop button is toggled to the "stop" state
    """

    if self.timer_job is not None:
      self.after_cancel(self.timer_job)
      self.timer_job = None

    self.start_time = None
    Logger.log(App._LOG_HEADER, "Stopped Bot")


  def update(self):
    # Ensure app is actually running
    if not self.running or self.start_time is None: return

    # Calculate elapsed time and update "Stop (time (s))" label
    elapsed = time.time() - self.start_time
    self.toggle_button.config(
        text=f"Stop ({self.formatDuration(elapsed)})"
    )

    # Delay job
    delay: int = 100 if elapsed < 60 else 1_000
    self.timer_job = self.after(delay, self.update)
  

  def formatDuration(self, seconds: float) -> str:
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




