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
        self.open_page("base/2")
        self.sleep(3)

        #点击医保按钮
        medicare_button = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='医保']]")),
            10
        )
        medicare_button.click()

        #医保界面点击身份证输入的位置
        time.sleep(5)
        _click_relative(0.6445, 0.45)

        #点击身份证输入框
        time.sleep(5)
        _click_relative(0.4844, 0.4813)


        # 输入身份证号
        time.sleep(2)
        from pynput.keyboard import Controller as KeyboardController, Key
        kb = KeyboardController()
        kb.type("52250120020820121x")

        #回车
        kb.press(Key.enter)
        kb.release(Key.enter)

        time.sleep(2)

        #输入密码后回车
        kb.type("123456")
        kb.press(Key.enter)
        kb.release(Key.enter)

        #回车确认关闭窗口
        kb.press(Key.enter)
        kb.release(Key.enter)

        #选择科室和医生
        time.sleep(5)

        try:
            import random

            # 定位科室输入框并点击
            dept_input = self.wait_until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//td[div[text()='科室：']]/following-sibling::td//input[@class='form-control']")
                ),
                5
            )
            dept_input.click()
            time.sleep(1.5)

            # 获取科室下拉选项
            dept_options = self.wait_until(
                lambda _: self.driver.find_elements(
                    By.XPATH,
                    "//td[div[text()='科室：']]/following-sibling::td//div[contains(@class, 'dropdown-menu')]//tr[@class='dropdown-item']//td"
                ),
                5
            )
            if not dept_options:
                raise Exception("未找到科室选项")

            #随机选择科室
            selected_dept = random.choice(dept_options)
            dept_text = selected_dept.text.strip()
            print(f"随机选择科室: {dept_text}")
            self.driver.execute_script("arguments[0].click();", selected_dept)
            time.sleep(2)

            # 定位医生输入框
            doctor_input = self.wait_until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//td[div[text()='医生：']]/following-sibling::td//input[@class='form-control']")
                ),
                10
            )

            # 如果医生下拉未展开定位并点击
            try:
                dropdown = self.driver.find_element(
                    By.XPATH,
                    "//td[div[text()='医生：']]/following-sibling::td//div[contains(@class, 'dropdown-menu')]"
                )
                if not dropdown.is_displayed():
                    doctor_input.click()
                    time.sleep(1)
            except:
                doctor_input.click()
                time.sleep(1)

            # 获取医生选项
            doctor_options = self.wait_until(
                lambda _: self.driver.find_elements(
                    By.XPATH,
                    "//td[div[text()='医生：']]/following-sibling::td//div[contains(@class, 'dropdown-menu')]//tr[@class='dropdown-item']//td[1]"
                ),
                5
            )
            if not doctor_options:
                raise Exception("未找到医生选项")

            #随机选择医生
            selected_doctor = random.choice(doctor_options)
            doctor_text = selected_doctor.text.strip()
            print(f"随机选择医生: {doctor_text}")
            self.driver.execute_script("arguments[0].click();", selected_doctor)
            print("科室与医生选择完成")

        except Exception as e:
            print(f"选择失败: {e}")
            raise

        time.sleep(5)
        # 点击保存
        try:
            save_button = self.wait_until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//div[text()='保存']]")
                ),
                5
            )
            save_button.click()
            print("已点击保存")
        except Exception as e:
            print(f"无法点击保存按钮: {e}")

        time.sleep(5)
        #点击病种框确认
        _click_relative(0.5703, 0.4688)

        #点击结算
        time.sleep(5)
        _click_relative(0.6250, 0.5625)

        #结算后等待保存
        time.sleep(10)
        print("医保挂号流程结束")
        # locust -f test_CW_mzghyb.py
