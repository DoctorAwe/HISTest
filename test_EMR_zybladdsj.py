import random
import time
from typing import Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from Base.BaseSeleniumUser import BaseSeleniumUser

class EMRInpatientCaseCreate(BaseSeleniumUser):
    dept = "xwj"
    role = "zyys"

    debug = False

    def on_get_user(self) -> Tuple[str, str]:
        return '898', '123456'

    def on_task(self):
        try:
            self._execute_case_create()
        except Exception as e:
            print(f"测试失败：{e}")
            raise

    def _execute_case_create(self):
        self.open_page("base/1046")
        self.sleep(3)

        # 等待全局加载指示器消失
        self.wait_until(
            EC.invisibility_of_element_located((
                By.XPATH,
                "//i[contains(@class, 'node-loading') or contains(@class, 'fa-spinner')]"
            )),
            5
        )

        # 选择患者
        patient_nodes = self.driver.find_elements(
            By.XPATH,
            "//div[@class='tree-node' and .//span[contains(text(), '【') and contains(text(), '】')]]"
        )

        if not patient_nodes:
            raise Exception("患者列表为空")

        selected_patient = random.choice(patient_nodes)
        selected_patient.click()
        self.sleep(1)

        # 住院病历
        inpatient_record_tab = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//a[.//span[text()='住院病历']]")),
            5
        )
        inpatient_record_tab.click()

        # 新建病历
        new_case_btn = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='新建病历']]")),
            5
        )
        new_case_btn.click()
        self.sleep(5)

        # 选择模板（仅选中，不确认）
        self.select_random_template()

        # 点击 确认 关闭弹窗
        print("正在查找‘确认’按钮...")
        modal_root = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.modal.show"))
        )
        confirm_btn = WebDriverWait(modal_root, 10).until(
            EC.element_to_be_clickable((By.XPATH, ".//button[.//span[contains(., '确认')]]"))
        )
        self.driver.execute_script("arguments[0].click();", confirm_btn)
        print("已点击‘确认’，等待弹窗关闭...")

        # 等待弹窗完全消失
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.modal.show"))
        )

        print("等待病历内容加载...")
        time.sleep(3)

        # 点击主页面 保存病历
        print("正在查找‘保存病历’按钮...")
        save_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='保存病历']]"))
        )
        self.driver.execute_script("arguments[0].click();", save_button)
        print("病历已成功保存！")

        # 判断保存结果
        try:
            # 直接等待 class 包含 'alert-success' 的元素出现
            success_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    ".alert.alert-success"  # 直接定位绿色的成功弹窗
                ))
            )

            # 使用 textContent 可以忽略掉 html 注释，直接拿到纯文本
            content = success_element.get_attribute("textContent").strip()
            print(f"捕获到弹窗内容: '{content}'")

            if "成功" in content:
                print("保存成功！流程结束。")
                return
            else:
                raise Exception(f"保存操作收到异常弹窗: {content}")

        except Exception as e:
            print(f"未检测到成功弹窗 (原因: {e})")

            try:
                # 检查有没有红色的错误弹窗 (alert-danger 或类似的)
                error_alert = self.driver.find_element(By.CSS_SELECTOR, ".alert.alert-danger")
                print(f"检测到错误提示: {error_alert.get_attribute('textContent')}")
            except:
                pass

            # 截图
            timestamp = time.strftime("%H%M%S")
            self.driver.save_screenshot(f"fail_alert_{timestamp}.png")

            # 再次检查是不是“请选择一个标签”那种纯文字提示
            if "请选择一个标签" in self.driver.find_element(By.TAG_NAME, "body").text:
                raise Exception("模板已被建立：检测到页面存在阻断提示")

            raise Exception("保存失败：未检测到 class='alert-success' 的成功弹窗") from e

    # 模板选择逻辑
    def select_random_template(self):
        print("开始选择病历模板...")

        # 等待模板选择弹窗出现
        modal_root = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.modal.show"))
        )

        def find_top_level_nodes():
            top_nodes = []
            contents = modal_root.find_elements(By.CSS_SELECTOR, "div.tree-content")
            for content in contents:
                try:
                    style = content.get_attribute("style")
                    if style and "--bb-tree-view-level: 0" in style:
                        tree_node = content.find_element(By.CSS_SELECTOR, "div.tree-node")
                        text_span = tree_node.find_element(By.CSS_SELECTOR, "span.tree-node-text")
                        top_nodes.append({
                            "content": content,
                            "tree_node": tree_node,
                            "text_span": text_span,
                            "text": text_span.text.strip()
                        })
                except Exception:
                    continue
            return top_nodes

        def can_expand(content):
            try:
                content.find_element(By.CSS_SELECTOR, ".node-icon.fa-caret-right")
                return True
            except:
                return False

        def expand_and_wait(content):
            try:
                caret = content.find_element(By.CSS_SELECTOR, ".node-icon.fa-caret-right")
                self.driver.execute_script("arguments[0].click();", caret)
                node_text = content.find_element(By.CSS_SELECTOR, 'span.tree-node-text').text
                print(f"展开节点: {node_text}")

                # 等待加载图标消失
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".node-loading"))
                )

                # 等待新子节点加载（DOM 数量增加）
                old_count = len(modal_root.find_elements(By.CSS_SELECTOR, "div.tree-content"))
                WebDriverWait(self.driver, 5).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.tree-content")) > old_count
                )
                time.sleep(0.3)
                return True
            except Exception as e:
                print(f"展开失败: {e}")
                return False

        def get_child_nodes(parent_content):
            children = []
            all_contents = modal_root.find_elements(By.CSS_SELECTOR, "div.tree-content")
            try:
                parent_level = int(
                    parent_content.get_attribute("style").split("--bb-tree-view-level:")[1].split(";")[0]
                )
            except (IndexError, ValueError):
                return children

            for content in all_contents:
                try:
                    style = content.get_attribute("style")
                    if not style or "--bb-tree-view-level:" not in style:
                        continue
                    level = int(style.split("--bb-tree-view-level:")[1].split(";")[0])
                    if level > parent_level:
                        tree_node = content.find_element(By.CSS_SELECTOR, "div.tree-node")
                        text_span = tree_node.find_element(By.CSS_SELECTOR, "span.tree-node-text")
                        children.append({
                            "content": content,
                            "tree_node": tree_node,
                            "text_span": text_span,
                            "text": text_span.text.strip()
                        })
                except Exception:
                    continue
            return children

        # 主选择逻辑 
        top_nodes = find_top_level_nodes()
        if not top_nodes:
            raise Exception("未找到任何顶级模板节点")

        chosen_parent = random.choice(top_nodes)
        print(f"随机选择顶级模板: {chosen_parent['text']}")

        target = None
        if can_expand(chosen_parent["content"]):
            print("尝试展开...")
            if expand_and_wait(chosen_parent["content"]):
                child_nodes = get_child_nodes(chosen_parent["content"])
                if child_nodes:
                    target = random.choice(child_nodes)
                    print(f"随机选择子模板: {target['text']}")
                else:
                    target = chosen_parent
                    print("无子节点，使用父节点")
            else:
                target = chosen_parent
                print("展开失败，使用父节点")
        else:
            target = chosen_parent
            print("节点不可展开，直接使用")

        if not target:
            raise Exception("未能确定要点击的模板节点")

        # 安全点击选中模板
        print(f"点击选中模板: {target['text']}")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target["tree_node"])
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", target["tree_node"])

        print("模板已选中，等待主流程点击【确认】")

