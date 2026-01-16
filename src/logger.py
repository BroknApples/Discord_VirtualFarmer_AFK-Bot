import os
from datetime import datetime


class Logger:
  """ TODO
  Logger Class

  **Purpose:**
    does this
  
  **Usage:**
    do this
  ----------
  """

  # ==================== Variables ====================

  initialized = False
  terminal = False
  timestamp = False
  logfile = None

  # ================ Private Functions ================

  @classmethod
  def _getCurrentTimeFormatted(cls, format_override: str = "") -> str:
    """
    Gets the current time and returns it in a formatted string
    [YYYY-MM-DD_HH-MM-SS]
    
    :return: Formatted time string
    :rtype: str
    """

    now = datetime.now()
    time_format = format_override if format_override else "%Y/%m/%d %H:%M:%S" # YYYY/MM/DD HH:MM:SS
    return now.strftime(time_format)


  # ================ Public Functions ================

  @classmethod
  def isInit(cls) -> bool: return cls.initialized

  @classmethod
  def setTerminalPrint(cls, val: bool): cls.terminal = val
  @classmethod
  def isTerminalPrint(cls): return cls.terminal

  @classmethod
  def setTimestampPrint(cls, val: bool): cls.timestamp = val
  @classmethod
  def isTimestampPrint(cls): return cls.timestamp


  @classmethod
  def init(cls, log_dir: str, print_to_terminal: bool = True, include_timestamps: bool = True):
    """
    Initialize logger object

    :param log_dir: Directory to create log files in
    :type log_dir: str

    :param print_to_terminal: Should each logger print be sent to the terminal?
    :type print_to_terminal: bool

    :param include_timestamps: Should each logger print include timestamps?
    :type include_timestamps: bool
    """

    # Prevent reinitialization
    if cls.isInit():
      print("[Logger] ERROR: Cannot intialize a new logger")
      return

    cls.terminal = print_to_terminal
    cls.timestamp = include_timestamps

    # Create file in the log directory
    os.makedirs(log_dir, exist_ok=True)
    cls.logfile = open(f"{log_dir}/logfile - {cls._getCurrentTimeFormatted("%Y-%m-%d_%H-%M-%S")}.txt", "a", encoding="utf-8", buffering=1)
    Logger.log("", f"Discord Virtual Farmer AFK Bot Logfile - {cls._getCurrentTimeFormatted()}\n", True)

    # Mark logger as initialized
    cls.initialized = True
    print("[Logger] Logger successfully initialiezd!")


  @classmethod
  def uninit(cls):
    """
    Uninitialze the Logger class
    """

    cls.initialized = False
    cls.terminal = False
    cls.timestamp = False
    if cls.logfile:
      cls.logfile.close()
      cls.logfile = None


  @classmethod
  def log(cls, header: str, message: str, disable_timestamp: bool = False):
    """
    Docstring for log
    
    :param header: Header for the print statement
    :type header: str
    :param message: Data to print/log
    :type message: str
    :param disable_timestamp: Should the timestamp be disable when printing?
    :type disable_timestamp: bool
    """

    # Get the final string to print/log
    header_text = f"[{header}] " if header else "" # Only add a spacer if the header is not an empty string or None
    final_msg: str = f"{header_text}{message}"
    if not disable_timestamp and cls.isTimestampPrint():
      final_msg = f"{cls._getCurrentTimeFormatted()}    {final_msg}"

    # Print to the terminal if set to terminal print mode
    if cls.isTerminalPrint():
      print(final_msg)
    
    # Log to file
    if cls.logfile: cls.logfile.write(final_msg + "\n")
  
  
  @classmethod
  def context(cls, log_dir: str, print_to_terminal: bool = True, include_timestamps: bool = True):
    """
    Context manager for Logger.
    Automatically initializes and uninitializes the logger.

    :param log_dir: Directory to create log files in
    :type log_dir: str

    :param print_to_terminal: Should each logger print be sent to the terminal?
    :type print_to_terminal: bool

    :param include_timestamps: Should each logger print include timestamps?
    :type include_timestamps: bool
    """

    cls.init(log_dir, print_to_terminal, include_timestamps)
    return LoggerContext()
  

class LoggerContext:
  """
  Context helper class used to allow usage of `with Logger.context(dir_name)`
  """


  def __enter__(self):
    """
    Return Logger itself for use inside the `with` block
    """
    return Logger

  def __exit__(self, exc_type, exc_val, exc_tb):
    """
    Automatically uninitialize the logger
    """
    
    #Logger.uninit() # Would create new logfile each time a with-block ends
    return False # Returning False means exceptions propagate