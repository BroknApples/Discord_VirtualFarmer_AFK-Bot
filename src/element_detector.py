import cv2
from rapidocr_onnxruntime import RapidOCR
from src.logger import Logger


class ElementDetector:
  """ TODO
  ElementDetector Class

  **Purpose:**
    does this
  
  **Usage:**
    do this
  ----------
  """

  # ==================== Variables ====================

  _LOG_HEADER: str = "ElementDetector"

  language = ""
  engine = None
  initialized = False

  # ================ Private Functions ================


  # ================ Public Functions ================

  @classmethod
  def isInit(cls) -> bool: return cls.initialized


  @classmethod
  def init(cls):
    """
    Initialize PaddleOCR for use
    """

    # Already initialized, just return
    if cls.isInit(): return 

    # Initialize OCR
    cls.engine = RapidOCR()

    # Mark as initialized
    cls.initialized = True
    Logger.log(cls._LOG_HEADER, "Successfully initialized module.")
  

  @classmethod
  def uninit(cls):
    """
    Uninitialize the ElementDetector Class
    """

    cls.language = ""
    cls.engine = None
    cls.initialized = True
  

  @classmethod
  def detectText(cls, img, min_score: float = 0.6) -> list[str] | None:
    """
    Finds all text regions in an image
    
    :param img: Image to read (cv2.imread or image_path)
    :param min_score: Minimum confidence score to be accepted.
    :type min_scoreimg: float
    :return: List of found text & their positions
    :rtype: list[str]
    """

    # Ensure the image passed is loaded as a cv2 image
    if isinstance(img, str):
      img = cv2.imread(img)
    
    # Returns: [result, elapsed_time]
    result, _ = cls.engine(img)
    if result is None: return []

    ret = []
    for line in result: # Line structure ==> [ [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], text, confidence ]
      # Check if score is at required minimum
      score = float(line[2])
      if score < min_score: continue


      # Create box
      box_points = line[0]
      xs = [p[0] for p in box_points]
      ys = [p[1] for p in box_points]
      box = (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))

      # Get text
      text = line[1]
      
      # Append to list
      ret.append((text, box))

    return ret