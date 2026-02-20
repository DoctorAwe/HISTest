import time
import random
import string
from typing import Tuple
from pynput import mouse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from Base.BaseSeleniumUser import BaseSeleniumUser


def _click_relative(x_pct: float, y_pct: float):
    """全局辅助函数：按屏幕百分比点击"""
    try:
        import tkinter as tk
        tk_root = tk.Tk()
        screen_w = tk_root.winfo_screenwidth()
        screen_h = tk_root.winfo_screenheight()
        tk_root.destroy()

        x = int(screen_w * x_pct)
        y = int(screen_h * y_pct)

        if not (0 <= x <= screen_w and 0 <= y <= screen_h):
            raise ValueError("坐标超出屏幕范围")

        controller = mouse.Controller()
        controller.position = (x, y)
        time.sleep(0.15)
        controller.press(mouse.Button.left)
        time.sleep(0.1)
        controller.release(mouse.Button.left)
        time.sleep(1.0)

    except Exception as e:
        print(f"[ERROR] 屏幕点击失败: {e}")
        raise

def generate_random_name(length: int = 6) -> str:
    """生成随机字符串作为姓名（数字+字母）"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class CreateTempCard(BaseSeleniumUser):
    dept = "cw"
    role = "mz"

    def __init__(self, environment):
        super().__init__(environment)
        self.random_name = None

    def on_get_user(self) -> Tuple[str, str]:
        return '10054', '302302'

    def _fill_field_in_panel(self, panel, label_text: str, value: str):
        """在指定 panel 内填写单个字段"""
        label = panel.find_element(By.XPATH, f".//label[normalize-space()='{label_text}']")
        input_id = label.get_attribute("for")
        if not input_id:
            raise ValueError(f"Label '{label_text}' 没有 'for' 属性")
        input_elem = panel.find_element(By.ID, input_id)
        input_elem.clear()
        input_elem.send_keys(str(value))

    def _fill_fields_in_panel(self, panel, fields: dict):
        """批量填写多个字段"""
        for label_text, value in fields.items():
            self._fill_field_in_panel(panel, label_text, value)

    def on_task(self):
        #随机生成姓名
        self.random_name = generate_random_name()
        print(f"本次任务使用的随机姓名: {self.random_name}")

        # 打开临时卡申领页面
        self.open_page("base/195")

        # 点击临时卡
        tabs = self.wait_until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[@role='tab']")),
            5
        )

        target_index = None
        for i, tab in enumerate(tabs):
            if "临时卡" in tab.text:
                target_index = i
                tab.click()
                break
        else:
            raise Exception("未找到‘临时卡’Tab")

        if target_index is None:
            raise Exception("未能确定临时卡索引")

        # 等待对应面板激活
        def panel_is_active(driver):
            panels = driver.find_elements(By.CSS_SELECTOR, "div.tabs-body > div.tabs-body-content")
            if len(panels) <= target_index:
                return False
            return "d-none" not in panels[target_index].get_attribute("class")

        self.wait_until(panel_is_active, 2)
        panels = self.driver.find_elements(By.CSS_SELECTOR, "div.tabs-body > div.tabs-body-content")
        active_panel = panels[target_index]

        # 填写临时卡信息
        self._fill_fields_in_panel(active_panel, {
            "姓名": self.random_name,
            "地址": "1",
            "电话": "1"
        })
        time.sleep(2)

        # 点击保存
        save_button = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='保存']]")),
            5
        )
        save_button.click()
        print("临时卡信息已保存")

        #打印弹窗
        time.sleep(1)
        _click_relative(0.625, 0.5875) #取消打印按钮
        self.sleep(1)

        # 跳转到挂号页面
        self.open_page("base/2")
        self.sleep(3)

        # 点击自费
        medicare_button = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='自费']]")),
            5
        )
        medicare_button.click()

        # 弹窗中点击患者信息
        time.sleep(2)
        _click_relative(0.5313, 0.3344)

        # 点击姓名输入框
        time.sleep(2)
        _click_relative(0.4961, 0.3688)

        # 输入姓名
        time.sleep(2)
        from pynput.keyboard import Controller as KeyboardController, Key
        kb = KeyboardController()
        kb.type(self.random_name)
        kb.press(Key.enter)
        kb.release(Key.enter)
        kb.press(Key.space)
        kb.release(Key.space)
        time.sleep(2)

        # 随机选择科室和医生
        time.sleep(2)
        try:
            import random

            # 点击科室输入框
            dept_input = self.wait_until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//td[div[text()='科室：']]/following-sibling::td//input[@class='form-control']")
                ),
                5
            )
            dept_input.click()
            time.sleep(1.5)

            # 获取科室选项
            dept_options = self.wait_until(
                lambda _: self.driver.find_elements(
                    By.XPATH,
                    "//td[div[text()='科室：']]/following-sibling::td//div[contains(@class, 'dropdown-menu')]//tr[@class='dropdown-item']//td"
                ),
                5
            )
            if not dept_options:
                raise Exception("未找到科室选项")

            selected_dept = random.choice(dept_options)
            print(f"随机选择科室: {selected_dept.text.strip()}")
            self.driver.execute_script("arguments[0].click();", selected_dept)
            time.sleep(2)

            # 点击医生输入框
            doctor_input = self.wait_until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//td[div[text()='医生：']]/following-sibling::td//input[@class='form-control']")
                ),
                5
            )
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

            selected_doctor = random.choice(doctor_options)
            print(f"随机选择医生: {selected_doctor.text.strip()}")
            self.driver.execute_script("arguments[0].click();", selected_doctor)

        except Exception as e:
            print(f"选择科室或医生失败: {e}")
            raise

        time.sleep(2)

        # 再次点击保存
        final_save = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='保存']]")),
            5
        )
        final_save.click()
        print("挂号信息已保存,姓名: {self.random_name}")

        self.sleep(2)

        #收费弹窗
        try:
            print("正在处理挂号收费弹窗...")

            # 等待挂号收费弹窗出现（通过标题判断）
            self.wait_until(
                EC.presence_of_element_located((By.XPATH, "//h5[contains(@class, 'modal-title') and text()='挂号收费']")),
                5
            )

            # 定义支付方式的文本列表
            payment_options = ["聚合POS", "挂账", "现金"]

            # 随机选择一个
            selected_payment = random.choice(payment_options)
            print(f"随机选择支付方式: {selected_payment}")

            # 定位对应行
            target_row = self.wait_until(
                EC.element_to_be_clickable((By.XPATH, f"//tr[.//div[text()='{selected_payment}']]")),
                5
            )
            target_row.click()
            time.sleep(0.5)

            # 按回车确认
            from pynput.keyboard import Controller as KeyboardController, Key
            kb = KeyboardController()
            kb.press(Key.enter)
            kb.release(Key.enter)
            print("已选择 '{selected_payment}' 并按回车")

            # 等待弹窗关闭或跳转
            time.sleep(2)

        except Exception as e:
            print(f"[WARNING] 挂号收费弹窗处理失败（可能未弹出或结构变化）: {e}")
        # locust -f test_CW_mzghsjlsk.py