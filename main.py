import os
from src.window_manager import WindowManager
from src.logger import Logger
from src.auto_gui import AutoGui
from src.element_detector import ElementDetector
from src.app import App
import cv2


if __name__ == "__main__":
  # Constants
  LOG_HEADER = "Main"
  TARGET_EXE = "Discord.exe" # NOTE: Change this if you changed Discord's executable filename

  # Create logger, element_detector, and window_handler
  Logger.init("logs", True, True)
  ElementDetector.init()
  window_manager = WindowManager()
  windows = window_manager.gatherOpenWindows()

  app = App()
  app.mainloop()
  exit()


  # Loop through every found window
  found: bool = False
  discord_win_title: str = ""
  for hwnd, title in (w for w in windows if not found):
    # If executable is discord, then open AutoGui instance
    full_exe_path = window_manager.getExecutableFromHwnd(hwnd)
    exe = os.path.basename(full_exe_path)
    if exe == TARGET_EXE:
      # Mark as found and log
      Logger.log(LOG_HEADER, f"Found {TARGET_EXE}!")
      found = True
      discord_win_title = title
      break


  # Open 'Discord.exe' with AutoGui
  if found:
    # Create auto_gui
    auto_gui = AutoGui(discord_win_title)
    
    # Get discord texture
    screenshot = window_manager.getWindowTextureFromHwnd(hwnd)
    # cv2.imshow("Discord Screenshot", screenshot)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # 1. Detect all text
    all_text = ElementDetector.detectText(screenshot)

    if all_text:
        img_width = screenshot.shape[1]
        
        # 1. Pre-filter: Ignore text in the Member List (right side) 
        # and Channel List (left side)
        chat_elements = []
        for text, box in all_text:
            x_min = box[0]
            # Adjust these percentages if your Discord layout is different
            # Ignores the left 15% and right 20% of the screen
            if (img_width * 0.15) < x_min < (img_width * 0.80):
                chat_elements.append((text, box))

        # 2. Sort top-to-bottom
        sorted_elements = sorted(chat_elements, key=lambda x: x[1][1])

        target_name = "dak"
        click_target_tuple = None
        MAX_VERTICAL_GAP = 300 

        # 3. Search bottom-up for the most recent message in the chat
        for i in range(len(sorted_elements) - 1, -1, -1):
            text, box = sorted_elements[i]
            clean_text = text.lower()
            
            # Avoid headers: Look for the name inside the embed
            if target_name in clean_text and "used /" not in clean_text:
                player_y_top = box[1]
                player_x_center = (box[0] + box[2]) / 2
                
                # 4. Look DOWN for the button
                for j in range(i + 1, len(sorted_elements)):
                    btn_text, btn_box = sorted_elements[j]
                    btn_clean = btn_text.lower().strip()

                    # Safety: Stop if we leave the embed area
                    if (btn_box[1] - player_y_top) > MAX_VERTICAL_GAP:
                        break
                    
                    if btn_clean == "farm":
                        btn_x_center = (btn_box[0] + btn_box[2]) / 2
                        
                        # Only click if button is horizontally aligned with the name
                        if abs(btn_x_center - player_x_center) < 200:
                            # TODO
                            # import random
                            # # Instead of clicking the perfect center (cx, cy)
                            # jitter_x = random.randint(-5, 5) # Small random shift left/right
                            # jitter_y = random.randint(-3, 3) # Small random shift up/down
                            # human_click_tuple = (
                            #     click_target_tuple[0] + jitter_x,
                            #     click_target_tuple[1] + jitter_y
                            # )

                            # auto_gui.click(human_click_tuple)
                            click_target_tuple = (
                                int(btn_x_center),
                                int((btn_box[1] + btn_box[3]) / 2)
                            )
                            break
                
                if click_target_tuple:
                    break

        # 5. Execute Click
        if click_target_tuple:
            Logger.log(LOG_HEADER, f"Clicking Chat Button at: {click_target_tuple}")
            auto_gui.click(click_target_tuple)
        else:
            Logger.log(LOG_HEADER, f"No Farm button found for {target_name} in the chat area.")
  
  # Log that the process was never found
  if not found:
    Logger.log(LOG_HEADER, f"ERROR: {TARGET_EXE} is not a running process.")