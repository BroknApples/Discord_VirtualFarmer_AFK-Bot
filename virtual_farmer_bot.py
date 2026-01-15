from pywinauto import Application

# Connect to a running Notepad window by title
app = Application(backend="uia").connect(title="Untitled - Notepad")
win = app.window(title="Untitled - Notepad")

# Click at a position (x=100, y=100) relative to the window
win.click_input(coords=(100, 100), absolute=False, set_foreground=False)

# Type text
win.type_keys("Hello world!{ENTER}", set_foreground=False)