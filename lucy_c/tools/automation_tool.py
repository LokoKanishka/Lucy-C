import logging
import pyautogui

class SystemHands:
    def __init__(self):
        self.log = logging.getLogger("SystemHands")
        # Safety feature: move mouse to corner to abort
        pyautogui.FAILSAFE = True

    def type_text(self, text: str):
        """Type text into the focused window."""
        self.log.info("Typing: %s", text)
        pyautogui.write(text, interval=0.01)
        return f"Escribí: {text}"

    def press_key(self, key: str):
        """Press a specific key (e.g., 'enter', 'tab', 'f5')."""
        self.log.info("Pressing key: %s", key)
        pyautogui.press(key)
        return f"Presioné la tecla: {key}"

    def hotkey(self, *keys: str):
        """Press a combination of keys (e.g., 'ctrl', 'c')."""
        self.log.info("Pressing hotkey: %s", keys)
        pyautogui.hotkey(*keys)
        return f"Ejecuté el atajo: {' + '.join(keys)}"

    def click(self, x: int = None, y: int = None, button: str = 'left', clicks: int = 1):
        """Click at (x, y) or current position."""
        if x is not None and y is not None:
            self.log.info("Clicking %s at (%d, %d) x%d", button, x, y, clicks)
            pyautogui.click(x, y, button=button, clicks=clicks, duration=0.2)
            return f"Hice {clicks} clic(s) {button} en ({x}, {y})"
        else:
            self.log.info("Clicking %s at current position x%d", button, clicks)
            pyautogui.click(button=button, clicks=clicks)
            return f"Hice {clicks} clic(s) {button} en la posición actual"

    def move_to(self, x: int, y: int):
        """Move mouse to (x, y) with easing."""
        self.log.info("Moving mouse to (%d, %d)", x, y)
        pyautogui.moveTo(x, y, duration=0.5, tween=pyautogui.easeInOutQuad)
        return f"Moví el mouse a ({x}, {y})"

    def wait(self, seconds: float):
        """Wait for a certain amount of time."""
        import time
        self.log.info("Waiting for %.2f seconds", seconds)
        time.sleep(seconds)
        return f"Esperé {seconds} segundos"

    def get_info(self):
        """Get screen size and mouse position."""
        size = pyautogui.size()
        pos = pyautogui.position()
        return f"Pantalla: {size.width}x{size.height}, Mouse: {pos.x},{pos.y}"
