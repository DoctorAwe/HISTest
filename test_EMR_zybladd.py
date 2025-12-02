import random
from typing import Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from Base.BaseSeleniumUser import BaseSeleniumUser


class EMRInpatientCaseCreate(BaseSeleniumUser):
    dept = "xwj"
    role = "zyys"  # 住院医生

    def on_get_user(self) -> Tuple[str, str]:
        return '898', '123456'

    def on_task(self):
        try:
            self._execute_case_create()
        except Exception as e:
            print(f"失败：{e}")
            raise

    def _execute_case_create(self):
        global confirm_btn
        self.open_page("base/1046")
        self.sleep(3)

        self.wait_until(
            EC.invisibility_of_element_located((
                By.XPATH,
                "//i[contains(@class, 'node-loading') or contains(@class, 'fa-spinner')]"
            )),
            5
        )


        patient_nodes = self.driver.find_elements(
            By.XPATH,
            "//div[@class='tree-node' and .//span[contains(text(), '【') and contains(text(), '】')]]"
        )

        if not patient_nodes:
            raise Exception("患者列表为空")

        # 随机选择并点击
        selected_patient = random.choice(patient_nodes)
        selected_patient.click()
        self.sleep(1)


        # 点击住院病历
        inpatient_record_tab = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//a[.//span[text()='住院病历']]")),
            5
        )
        inpatient_record_tab.click()

        # 点击新建病历
        new_case_btn = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='新建病历']]")),
            5
        )
        new_case_btn.click()
        self.sleep(10)

        # 模板选择逻辑 tree-view scroll
        # 定位弹窗
        modal_root = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.modal.show"))
        )
        tree_container = modal_root.find_element(By.CSS_SELECTOR, "div.tree-view.scroll")

        def find_template(text):
            for _ in range(15):
                spans = modal_root.find_elements(By.CSS_SELECTOR, "span.tree-node-text")
                for span in spans:
                    try:
                        if text in span.text:
                            return span
                    except:
                        continue
                self.driver.execute_script("arguments[0].scrollTop += 100;", tree_container)
                self.sleep(0.4)
            return None

        # 找“病程记录”
        target_span = find_template("病程记录")
        if not target_span:
            raise Exception("未找到‘病程记录’")

        # 找到其父级 .tree-content
        parent_content = target_span.find_element(By.XPATH, "./ancestor::div[contains(@class, 'tree-content')][1]")
        print("找到‘病程记录’容器")

        # 找到展开图标（caret）
        try:
            caret = parent_content.find_element(By.CSS_SELECTOR, ".node-icon.fa-caret-right")
        except:
            try:
                caret = parent_content.find_element(By.CSS_SELECTOR, ".node-icon.fa-solid.fa-caret-right")
            except:
                raise Exception("未找到展开图标")

        # 模拟点击 caret 图标
        self.driver.execute_script("""
                const el = arguments[0];
                const rect = el.getBoundingClientRect();
                const evt = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: rect.left + 5,
                    clientY: rect.top + 5
                });
                el.dispatchEvent(evt);
            """, caret)
        print("已点击展开图标，等待子项加载...")
        self.sleep(2.5)

        # 查找“日常病程记录”
        daily_record = find_template("日常病程记录")
        if not daily_record:
            raise Exception("未找到‘日常病程记录’")

        # 点击文字本身（不是父容器）
        print("正在点击‘日常病程记录’文本...")
        self.driver.execute_script("arguments[0].click();", daily_record)
        self.sleep(1.2)

        # 点击“确认”按钮（用 JS 确保触发）
        confirm_btn = WebDriverWait(modal_root, 10).until(
            EC.element_to_be_clickable((By.XPATH, ".//button[.//span[contains(., '确认')]]"))
        )
        print("正在通过 JS 点击‘确认’按钮...")
        self.driver.execute_script("arguments[0].click();", confirm_btn)
        self.sleep(1.5)

        # 等待弹窗关闭
        print("等待模板弹窗关闭...")
        WebDriverWait(self.driver, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.modal.show"))
        )
        print("模板弹窗已关闭")

        # 保存病历
        print("等待‘保存病历’按钮...")
        save_button = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='保存病历']]"))
        )

        try:
            print("原生点击‘保存病历’...")
            save_button.click()
        except Exception as e:
            print(f"回退到 JS 点击: {e}")
            self.driver.execute_script("arguments[0].click();", save_button)

        self.sleep(2)
        print("保存操作已完成")


# locust -f test_EMR_zybladd.py
