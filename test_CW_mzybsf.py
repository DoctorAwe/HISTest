from typing import Tuple
import time
from pynput import mouse
from Base.BaseSeleniumUser import BaseSeleniumUser
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def _click_relative(x_pct: float, y_pct: float):
    try:
        # 获取屏幕尺寸
        import tkinter as tk
        tk_root = tk.Tk()
        screen_w = tk_root.winfo_screenwidth()
        screen_h = tk_root.winfo_screenheight()
        tk_root.destroy()

        x = int(screen_w * x_pct)
        y = int(screen_h * y_pct)
        print(f"[DEBUG] 屏幕分辨率: {screen_w}x{screen_h}")
        print(f"[DEBUG] 目标坐标: ({x}, {y})")

        if not (0 <= x <= screen_w and 0 <= y <= screen_h):
            raise ValueError("坐标超出屏幕范围！")

        controller = mouse.Controller()
        print(f"[DEBUG] 当前鼠标: {controller.position}")

        print("[ACTION] 移动并点击")
        controller.position = (x, y)
        time.sleep(0.15)
        controller.press(mouse.Button.left)
        time.sleep(0.1)
        controller.release(mouse.Button.left)
        time.sleep(1.0)

        print("[SUCCESS] 点击完成")

    except Exception as e:
        print(f"[ERROR] 点击失败: {e}")
        raise


class CreateTempCard(BaseSeleniumUser):
    dept = "cw"
    role = "mz"

    def on_get_user(self) -> Tuple[str, str]:
        return '10054', '302302'

    def on_task(self):
        try:
            self._execute_case_create()
        except Exception as e:
            print(f"任务失败: {e}")
            raise

    def _execute_case_create(self):
        self.open_page("base/35")
        self.sleep(3)

        # 点击读卡按钮
        medicare_button = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='读卡']]")),
            5
        )
        medicare_button.click()

        # 读卡界面点击并输入身份证号流程
        time.sleep(2)
        _click_relative(0.5313, 0.3313)
        time.sleep(2)
        _click_relative(0.3906, 0.3625)
        time.sleep(2)
        _click_relative(0.3906, 0.4250)
        time.sleep(2)
        _click_relative(0.5, 0.3656)

        time.sleep(2)
        from pynput.keyboard import Controller as KeyboardController, Key
        kb = KeyboardController()
        kb.type("522422199208280051")

        # 确定
        time.sleep(2)
        _click_relative(0.4258, 0.6313)

        # 点击保存按钮
        medicare_button = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='保存']]")),
            5
        )
        medicare_button.click()
