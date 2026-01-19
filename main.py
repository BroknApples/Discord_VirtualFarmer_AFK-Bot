from src.logger import Logger
from src.element_detector import ElementDetector
from src.app import App


if __name__ == "__main__":
  LOG_HEADER: str = "Main"

  # Initialize logger and element detector
  Logger.init("logs", True, True)
  ElementDetector.init() 
  
  # Create and run app
  Logger.log(LOG_HEADER, "Opened app.")
  app = App()
  app.mainloop()
  Logger.log(LOG_HEADER, "Closed app.")
