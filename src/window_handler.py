import platform
from logger import Logger

class WindowHandler:
  """ TODO
  WindowHandler Class

  **Purpose:**
    does this
  
  **Usage:**
    do this
  ----------
  """

  # ==================== Variables ====================

  # Variables for the type of OS's that can be returned by platform.system
  class OperatingSystems:
    WINDOWS = "Windows"
    LINUX = "Linux"
    MAC_OS = "Darwin"
    FREE_BSD = "FreeBSD"
    OPEN_BSD = "OpenBSD"
    NET_BSD = "NetBSD"
    SUN_OS = "SunOS"
  

  # ================ Private Functions ================

  def _isWindows(self) -> bool: return self.OS == WindowHandler.OperatingSystems.WINDOWS
  def _isLinux(self) -> bool: return self.OS == WindowHandler.OperatingSystems.LINUX
  def _isMacOS(self) -> bool: return self.OS == WindowHandler.OperatingSystems.MAC_OS


  # ================ Constructors ================

  def __init__(self):
    """
    Initalize a WindowHandler class. Gathers the OS type and decides what functions to use later on.
    """

    self.OS: str = platform.system() # What type of OS the script is running on.


  # ================ Public Functions ================

  def gatherOpenWindows(self) -> str:
    if self._isWindows():
      pass
    elif self._isLinux():
      pass
    elif self._isMacOS():
      pass
    else:
      print("Not supported")