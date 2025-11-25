from typing import Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from Base.BaseSeleniumUser import BaseSeleniumUser

class EMRSave(BaseSeleniumUser):
    dept = "xwk"
    role = "mzys"

    debug = False

    def on_get_user(self) -> Tuple[str, str]:
        return '898', '123456'

    def on_task(self):
        self.open_page("base/28")
        self.sleep(5)
        target_input =  self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//label[starts-with(normalize-space(), '已诊')]/preceding-sibling::input")),
            2)
        target_input.click()
        # self.wait_mask()
        self.sleep(3)
        first_card = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "(//div[@class='hover-effect'])[1]")),
            2)
        first_card.click()
        # self.wait_mask()
        self.sleep(4)
        new_case_btn = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='新建病历']]")),
            2)
        new_case_btn.click()
        self.sleep(4)
        mzbl = self.wait_until(
            EC.element_to_be_clickable( (By.XPATH, "//div[contains(@class,'tree-node')][.//span[text()='急诊病历']]")),
            2
        )
        mzbl.click()
        confirm_btn = self.wait_until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[text()='确认'] and .//i[contains(@class, 'fa-check')]]")
            ),
            2
        )
        confirm_btn.click()
        # self.wait_mask()
        self.sleep(4)
        save_button = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='保存']]")),
            2
        )
        save_button.click()

