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

        # 选择患者（带【】标识）
        patient_nodes = self.driver.find_elements(
            By.XPATH,
            "//div[@class='tree-node' and .//span[contains(text(), '【') and contains(text(), '】')]]"
        )

        if not patient_nodes:
            raise Exception("患者列表为空")

        selected_patient = random.choice(patient_nodes)
        selected_patient.click()
        self.sleep(1)

        # 点击“住院病历”标签
        inpatient_record_tab = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//a[.//span[text()='住院病历']]")),
            5
        )
        inpatient_record_tab.click()

        # 点击“新建病历”按钮
        new_case_btn = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='新建病历']]")),
            5
        )
        new_case_btn.click()
        self.sleep(5)

        # 1. 选择模板（仅选中，不确认）
        self.select_random_template()

        # 2. 点击 确认 关闭弹窗
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

        # 3. 点击主页面 保存病历
        print("正在查找‘保存病历’按钮...")
        save_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='保存病历']]"))
        )
        self.driver.execute_script("arguments[0].click();", save_button)
        print("病历已成功保存！")

        # 4. 判断保存结果
        try:
            # 先检查是否出现“请选择一个标签” —— 表示病历已存在
            try:
                warning_elements = self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(text(), '请选择一个标签')]"
                )
                if warning_elements:
                    msg_text = warning_elements[0].text.strip()
                    print(f"检测到提示: {msg_text}")
                    raise Exception(
                        "模板已被建立：系统提示‘请选择一个标签’，说明该患者在此病历类型下已存在病历，无法重复新建")
            except Exception as inner_e:
                if "模板已被建立" in str(inner_e):
                    raise  # 重新抛出我们的业务异常
                # 否则继续检查其他情况

            # 再检查是否保存成功
            success_msg = WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[contains(@class, 'ant-message')]//span[contains(text(), '成功') or contains(text(), '保存成功')]"
                ))
            )
            print(f"🎉 保存成功！提示信息: {success_msg.text.strip()}")
            return  # 流程结束

        except Exception as e:
            if "模板已被建立" in str(e):
                raise  # 直接抛出，不走下面的兜底

            print("未检测到‘保存成功’提示，可能存在异常或失败。")
            # 收集其他错误线索
            error_hints = []

            # 检查错误提示
            try:
                err_msg = self.driver.find_element(By.XPATH, "//div[contains(@class, 'ant-message-error')]")
                error_hints.append(f"错误提示: {err_msg.text}")
            except:
                pass

            # 检查是否有 modal 弹窗
            try:
                modal = self.driver.find_element(By.CSS_SELECTOR, "div.ant-modal-content")
                error_hints.append(f"弹窗内容: {modal.text[:100]}...")
            except:
                pass

            if error_hints:
                print("检测到以下异常线索:")
                for hint in error_hints:
                    print(f"   • {hint}")
            else:
                print("未发现明显错误，但也未收到成功提示。")

            raise Exception("保存病历失败：未收到成功提示，且非‘模板已存在’场景") from e


    # 模板选择逻辑
    def select_random_template(self):
        print("📂 开始选择病历模板...")

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
                print(f"  → 展开节点: {node_text}")

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
                print(f"  × 展开失败: {e}")
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

        # === 主选择逻辑 ===
        top_nodes = find_top_level_nodes()
        if not top_nodes:
            raise Exception("未找到任何顶级模板节点")

        chosen_parent = random.choice(top_nodes)
        print(f"  → 随机选择顶级模板: {chosen_parent['text']}")

        target = None
        if can_expand(chosen_parent["content"]):
            print("  → 尝试展开...")
            if expand_and_wait(chosen_parent["content"]):
                child_nodes = get_child_nodes(chosen_parent["content"])
                if child_nodes:
                    target = random.choice(child_nodes)
                    print(f"  → 随机选择子模板: {target['text']}")
                else:
                    target = chosen_parent
                    print("  → 无子节点，使用父节点")
            else:
                target = chosen_parent
                print("  → 展开失败，使用父节点")
        else:
            target = chosen_parent
            print("  → 节点不可展开，直接使用")

        if not target:
            raise Exception("未能确定要点击的模板节点")

        # 安全点击选中模板
        print(f"  → 点击选中模板: {target['text']}")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target["tree_node"])
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", target["tree_node"])

        # ✅ 关键：此处不关闭弹窗！不点击保存！
        print("✅ 模板已选中，等待主流程点击【确认】")