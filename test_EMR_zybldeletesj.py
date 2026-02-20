import random
import time
from typing import Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from Base.BaseSeleniumUser import BaseSeleniumUser


class EMRInpatientCaseDelete(BaseSeleniumUser):
    dept = "xwj"
    role = "zyys"

    def on_get_user(self) -> Tuple[str, str]:
        return '898', '123456'

    def on_task(self):
        try:
            self._execute_case_delete()
        except Exception as e:
            print(f"删除失败：{e}")
            raise

    def _execute_case_delete(self):
        self.open_page("base/1046")
        self.sleep(3)

        # 等待全局加载完成
        self.wait_until(
            EC.invisibility_of_element_located((
                By.XPATH,
                "//i[contains(@class, 'node-loading') or contains(@class, 'fa-spinner')]"
            )),
            5
        )

        # 随机选择患者
        patient_nodes = self.driver.find_elements(
            By.XPATH,
            "//div[@class='tree-node' and .//span[contains(text(), '【') and contains(text(), '】')]]"
        )
        if not patient_nodes:
            raise Exception("患者列表为空")

        selected_patient = random.choice(patient_nodes)
        print(f"随机选中患者: {selected_patient.text.strip()}")
        selected_patient.click()
        self.sleep(1)

        # 点击住院病历
        inpatient_tab = self.wait_until(
            EC.element_to_be_clickable((By.XPATH, "//a[.//span[text()='住院病历']]")),
            5
        )
        inpatient_tab.click()
        self.sleep(2)

        # 获取所有顶级病历分类
        print("获取所有顶级病历分类（level=0）")

        all_contents = self.driver.find_elements(By.CSS_SELECTOR, "div.tree-content")
        top_level_nodes = []

        for content in all_contents:
            try:
                style = content.get_attribute("style")
                if not style or "--bb-tree-view-level:" not in style:
                    continue
                level = int(style.split("--bb-tree-view-level:")[1].split(";")[0])
                if level == 0:
                    tree_node = content.find_element(By.CSS_SELECTOR, "div.tree-node")
                    text_span = tree_node.find_element(By.CSS_SELECTOR, "span.tree-node-text")
                    node_text = text_span.text.strip()
                    if node_text and node_text not in ["", "加载中..."]:
                        top_level_nodes.append({
                            "content": content,
                            "tree_node": tree_node,
                            "text_span": text_span,
                            "text": node_text
                        })
            except Exception as e:
                continue

        if not top_level_nodes:
            raise Exception("未找到任何顶级病历分类")

        # 随机选择一个顶级目录
        selected_top = random.choice(top_level_nodes)
        print(f"随机选中顶级目录: {selected_top['text']}")

        # 判断是否可展开（有子节点）
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
                print(f"展开: {content.find_element(By.CSS_SELECTOR, 'span.tree-node-text').text}")
                # 等待加载完成
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".node-loading"))
                )
                time.sleep(1)
                return True
            except Exception as e:
                print(f"展开失败: {e}")
                return False

        def get_direct_children(parent_content):
            children = []
            parent_level = 0
            try:
                style = parent_content.get_attribute("style")
                parent_level = int(style.split("--bb-tree-view-level:")[1].split(";")[0])
            except:
                return children

            for content in all_contents + self.driver.find_elements(By.CSS_SELECTOR, "div.tree-content"):
                try:
                    style = content.get_attribute("style")
                    if not style or "--bb-tree-view-level:" not in style:
                        continue
                    level = int(style.split("--bb-tree-view-level:")[1].split(";")[0])
                    if level == parent_level + 1:
                        tree_node = content.find_element(By.CSS_SELECTOR, "div.tree-node")
                        text_span = tree_node.find_element(By.CSS_SELECTOR, "span.tree-node-text")
                        node_text = text_span.text.strip()
                        if node_text and node_text not in ["", "加载中..."]:
                            children.append({
                                "content": content,
                                "tree_node": tree_node,
                                "text_span": text_span,
                                "text": node_text
                            })
                except:
                    continue
            return children

        target_node = None

        if can_expand(selected_top["content"]):
            print("尝试展开并选择子项")
            if expand_and_wait(selected_top["content"]):
                # 重新获取所有 contents（因为 DOM 可能更新）
                time.sleep(1)
                child_nodes = get_direct_children(selected_top["content"])
                if child_nodes:
                    target_node = random.choice(child_nodes)
                    print(f"随机选中子项: {target_node['text']}")
                else:
                    target_node = selected_top
                    print("无子节点，使用父节点")
            else:
                target_node = selected_top
                print("展开失败，使用父节点")
        else:
            target_node = selected_top
            print("节点不可展开，直接使用")

        # 点击最终选中的节点
        print(f"点击病历节点: {target_node['text']}")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_node["tree_node"])
        time.sleep(0.5)
        self.driver.execute_script("arguments[0].click();", target_node["tree_node"])
        self.sleep(2)

        # 等待加载病历
        print("等待右侧病历列表加载")
        delete_buttons = WebDriverWait(self.driver, 12).until(
            lambda d: d.find_elements(By.XPATH, "//button[.//div[text()='删除病历']]")
        )

        if not delete_buttons:
            raise Exception("当前患者无‘日常病程记录’可删除")

        print(f"找到 {len(delete_buttons)} 条可删除的病历")

        # 随机选择一条删除
        target_button = random.choice(delete_buttons)
        print("随机选择一条病历进行删除")
        self.driver.execute_script("arguments[0].click();", target_button)
        self.sleep(1)

        # 点击弹窗中的确定
        print("等待确认弹窗")
        confirm_btn = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='modal-content']//button[.//span[text()='确定']]")
            )
        )
        self.driver.execute_script("arguments[0].click();", confirm_btn)
        print("已点击确定")


