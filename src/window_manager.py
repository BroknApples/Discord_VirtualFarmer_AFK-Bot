import platform
import win32gui     # type: ignore
import win32ui      # type: ignore
import win32con     # type: ignore
import win32process # type: ignore
import psutil
import numpy as np
import cv2

from src.logger import Logger

class WindowManager:
  """ TODO
  WindowManager Class

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
  
  # Header to print in the Logger
  _LOG_HEADER: str = "WindowManager"
  

  # ================ Private Functions ================

  def _isWindows(self) -> bool: return self.OS == WindowManager.OperatingSystems.WINDOWS
  def _isLinux(self) -> bool: return self.OS == WindowManager.OperatingSystems.LINUX
  def _isMacOS(self) -> bool: return self.OS == WindowManager.OperatingSystems.MAC_OS


  # ================ Constructors ================

  def __init__(self):
    """
    Initalize a WindowManager class. Gathers the OS type and decides what functions to use later on.
    """

    self.OS: str = platform.system() # What type of OS the script is running on.


  # ================ Public Functions ================

  def gatherOpenWindows(self) -> list[tuple[int, str]]:
    """
    Gathers open windows on the current computer
    
    :return: List of (HWND : WindowName)
    :rtype: list[tuple[int, str]]
    """

    windows = []
    Logger.log(WindowManager._LOG_HEADER, "Gathering open windows...")

    # Windows
    if self._isWindows():
      def enumHandler(hwnd, _):
        # Check styles
        if not win32gui.IsWindowVisible(hwnd): return # Skip invisible windows

        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if style & win32con.WS_EX_TOOLWINDOW: return # Skip toolbar windows
        #if not style & win32con.WS_CAPTION: return # Skip windows with no title bar

        class_name = win32gui.GetClassName(hwnd)
        if class_name in {"ApplicationFrameWindow", "Windows.UI.Core.CoreWindow"}: return # Skip Windows helper class types

        title = win32gui.GetWindowText(hwnd)
        if title: windows.append((hwnd, title)) # Only allow windows with titles to proceed
      win32gui.EnumWindows(enumHandler, None)

    # Linux
    elif self._isLinux():
      Logger.log(Logger._LOG_HEADER, "Linux not implemented yet.")

    # MacOS
    elif self._isMacOS():
      Logger.log(Logger._LOG_HEADER, "MacOS not implemented yet.")

    # Other
    else:
      Logger.log(Logger._LOG_HEADER, f"Operating system [{self.OS}] not supported.")
    
    Logger.log(WindowManager._LOG_HEADER, f"Gathered {len(windows)} open windows.")
    return windows
  

  def getExecutableFromHwnd(self, hwnd: int) -> str:
    """
    Obtain the path to the executable given an hwnd window handle
    
    :param hwnd: Window handle number
    :type hwnd: int
    :return: Executable path
    :rtype: str
    """

    # Get the PID of the process
    _, pid = win32process.GetWindowThreadProcessId(hwnd)

    # Get the executable from the PID
    proc = psutil.Process(pid)
    return proc.exe() # Full path to the exe
  

  def getWindowTextureFromHwnd(self, hwnd: int):
    """
    Gets the window texture for a given hwnd
    
    :param hwnd: Window handle
    :type hwnd: int
    :return: cv2 image
    """

    # Get window client size
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    width = right - left
    height = bottom - top

    # Get device contexts
    hwnd_dc = win32gui.GetDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    # Create bitmap
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    old_bitmap = save_dc.SelectObject(bitmap)  # Save old bitmap

    # Copy window into bitmap
    save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

    # Convert bitmap to numpy array directly (no PIL)
    bmpinfo = bitmap.GetInfo()
    bmpstr = bitmap.GetBitmapBits(True)
    img = np.frombuffer(bmpstr, dtype=np.uint8)
    img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)  # BGRA
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # convert to BGR for OpenCV

    # Cleanup properly
    save_dc.SelectObject(old_bitmap)          # Deselect bitmap before deleting DC
    save_dc.DeleteDC()                        # Delete memory DC first
    mfc_dc.DeleteDC()                         # Delete MFC DC
    win32gui.ReleaseDC(hwnd, hwnd_dc)         # Release window DC
    win32gui.DeleteObject(bitmap.GetHandle()) # Delete bitmap

    return img
