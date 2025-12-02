import random
import time
import os
from typing import Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from Base.BaseSeleniumUser import BaseSeleniumUser


class EMRInpatientCaseDelete(BaseSeleniumUser):
    dept = "xwj"
    role = "zyys"  # 住院医生

    def on_get_user(self) -> Tuple[str, str]:
        return '898', '123456'

    def on_task(self):
        try:
            self._execute_case_delete()
        except Exception as e:
            print(f"❌ 执行失败：{e}")
            os.makedirs("screenshots", exist_ok=True)
            self.driver.save_screenshot(f"screenshots/debug_{int(time.time())}.png")
            raise

    def _execute_case_delete(self):
        # 1. 打开页面
        self.open_page("base/1046")
        self.sleep(3)

        # 2. 选择患者（带【】的节点）
        patient_nodes = self.driver.find_elements(
            By.XPATH,
            "//div[@class='tree-node' and .//span[contains(text(), '【') and contains(text(), '】')]]"
        )
        if not patient_nodes:
            raise Exception("患者列表为空")
        selected_patient = random.choice(patient_nodes)
        print(f"👉 选中患者: {selected_patient.text}")
        selected_patient.click()
        self.sleep(1.5)

        # 3. 点击「住院病历」标签
        inpatient_tab = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//a[.//span[text()='住院病历']]")),
            8
        )
        inpatient_tab.click()
        self.sleep(2)

        # 4. 查找并点击“病程记录”（确保展开）
        print("🔍 查找‘病程记录’...")
        course_span = self.driver.find_element(
            By.XPATH,
            "//span[@class='tree-node-text' and text()='病程记录']"
        )
        course_content = course_span.find_element(By.XPATH, "./ancestor::div[@class='tree-content'][1]")

        # 检查是否已展开（看是否有 fa-rotate-90）
        try:
            caret = course_content.find_element(By.CSS_SELECTOR, "i.node-icon.fa-caret-right")
            if "fa-rotate-90" not in caret.get_attribute("class"):
                print("🖱️ 展开‘病程记录’...")
                caret.click()
                self.sleep(2)
        except:
            pass  # 已展开或无图标

        # 5. 点击“日常病程记录”
        print("🔍 查找‘日常病程记录’...")
        daily_span = self.driver.find_element(
            By.XPATH,
            "//span[@class='tree-node-text' and (text()='日常病程记录' or contains(text(), '日常病程'))]"
        )
        print(f"✅ 点击子节点: {daily_span.text}")
        self.driver.execute_script("arguments[0].click();", daily_span)
        self.sleep(1)

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # 6. ⏳ 关键：等待右侧加载出“删除病历”按钮（根据你提供的真实 HTML）
        print("⏳ 等待右侧病历加载，查找‘删除病历’按钮...")
        try:
            delete_button = WebDriverWait(self.driver, 12).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//div[text()='删除病历']]")
                )
            )
            print("✅ 找到‘删除病历’按钮")
        except Exception as e:
            os.makedirs("screenshots", exist_ok=True)
            self.driver.save_screenshot(f"screenshots/delete_btn_missing_{int(time.time())}.png")
            raise Exception("❌ 未找到‘删除病历’按钮，请检查是否有病历数据或权限") from e

        # 7. 点击删除
        self.driver.execute_script("arguments[0].click();", delete_button)
        self.sleep(1)


        # 8. 精准点击弹窗中的“确定”
        print("⚠️ 等待删除确认弹窗...")
        confirm_btn = WebDriverWait(self.driver, 8).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='modal-content']//button[.//span[text()='确定']]")
            )
        )
        print("✅ 点击【确定】确认删除...")
        self.driver.execute_script("arguments[0].click();", confirm_btn)
        self.sleep(2)

        print("🎉 删除操作成功完成！")