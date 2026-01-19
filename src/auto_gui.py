from pywinauto import Application
from src.logger import Logger

class AutoGui:
  """ TODO
  WindowManager Class

  **Purpose:**
    Class used to automate tasks on windows.
  
  **Usage:**
    do this
  ----------
  """

  # ==================== Variables ====================
  
  _LOG_HEADER: str = "AutoGui"


  # ================ Constructors ================

  def __init__(self, target_window_title: str):
    """
    Initialize a new AutoGui object
    
    :param target_window: Target window's title
    :type target_window: str
    """

    # Connect to target application
    self.setTarget(target_window_title)


  # ================ Public Functions ================

  def setTarget(self, target_window_title: str):
    """
    Sets the target application
    
    :param target_window_title: Target window's title
    :type target_window_title: str
    """
    
    Logger.log(AutoGui._LOG_HEADER, f"Setting target to '{target_window_title}'")
    self.target = target_window_title
    self.app = Application(backend="uia").connect(title=self.target)
    self.win = self.app.window(title=self.target)
    


  def click(self, pos: tuple[int, int], absolute: bool = False):
    """
    Click at a position on the window
    
    :param pos: Position on the screen to click (RELATIVE when using 'absolute = False', MONITOR COORDINATES when using 'absolute = True')
    :type pos: tuple[int, int]
    :param absolute: Should the pos coordinates be relative to the monitor or window
    :type absolute: bool
    """

    Logger.log(AutoGui._LOG_HEADER, f"Clicking at position {pos} | absolute={absolute}")
    self.win.click_input(coords=pos, absolute=absolute)


  def type(self, text: str):
    """
    Type keys on the targeted application
    
    :param text: Text to type
    :type text: str
    """

    Logger.log(AutoGui._LOG_HEADER, f"Typing \"{text}\"")
    self.win.type_keys(text)