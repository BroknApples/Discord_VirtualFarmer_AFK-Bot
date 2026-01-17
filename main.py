from src.logger import Logger
from src.element_detector import ElementDetector
from src.app import App


if __name__ == "__main__":
  # Initialize logger and element detector
  Logger.init("logs", True, True)
  ElementDetector.init() 
  
  # Create and run app
  app = App()
  app.mainloop()
  exit()
