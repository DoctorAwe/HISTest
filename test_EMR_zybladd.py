import random
import os
import re
from time import sleep, time
from typing import Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from Base.BaseSeleniumUser import BaseSeleniumUser
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    NoSuchElementException
)


# locust -f test_EMR_zybladd.py

class EMRInpatientCaseCreate(BaseSeleniumUser):
    dept = "xwj"
    role = "zyys"
    #debug = False

    def on_get_user(self) -> Tuple[str, str]:
        return '898', '123456'

    def on_task(self):
        sleep(random.uniform(5, 20))

        # 初始化标识，用于截图命名
        self.error_identity = "初始化阶段"
        start_time = time()
        task_id = int(start_time)

        try:
            self._execute_case_create()
            print(f"✅ [SUCCESS] 耗时 {int(time() - start_time)}s | 标识: {self.error_identity}")
        except Exception as e:
            # 动态生成：床号_姓名_No编号_时间戳.png
            clean_info = re.sub(r'[\\/:*?"<>|【】\s]', '_', self.error_identity)
            error_filename = f"fails/{clean_info}_{task_id}.png"

            print(f"❌ [FAILED] 阶段: {self.error_identity} | 错误: {str(e)[:100]}")

            # 截图
            try:
                if not os.path.exists("fails"): os.makedirs("fails")
                self.driver.save_screenshot(error_filename)
                print(f"📸 异常截图已存至: {error_filename}")
            except:
                pass

            # 失败后刷新页面，防止上一个任务的残留弹窗卡死后续所有任务
            try:
                self.driver.refresh()
                sleep(8)
            except:
                pass

            raise Exception(f"[{self.error_identity}] {str(e)}")

    def _get_random_text(self, min_len=400, max_len=800):
        corpus = [
            "查体：体温36.5℃，脉搏80次/分，呼吸18次/分。",
            "双肺呼吸音清，未闻及干湿性啰音。",
            "腹平软，全腹无压痛、反跳痛及肌紧张。",
            "遵医嘱继续给予抗感染治疗。",
            "密切观察病情变化，注意防跌倒。",
            "向家属交代病情，嘱清淡饮食。"
            "患者今日神志清，精神尚可，主诉无特殊不适。",
            "夜间睡眠良好，二便正常，饮食较前增加。",
            "查体：体温36.5℃，脉搏80次/分，呼吸18次/分，血压120/75mmHg。",
            "双肺呼吸音清，未闻及干湿性啰音。",
            "心律齐，心率78次/分，各瓣膜听诊区未闻及病理性杂音。",
            "腹平软，全腹无压痛、反跳痛及肌紧张，肝脾肋下未触及。",
            "双下肢无水肿，足背动脉搏动良好。",
            "切口敷料干燥清洁，无渗血及渗液，愈合良好。",
            "今日复查血常规及生化指标，未见明显异常。",
            "胸部CT示：双肺纹理增粗，未见明显实质性病变。",
            "遵医嘱继续给予抗感染、化痰、平喘治疗。",
            "给予补液、维持水电解质平衡及营养支持治疗。",
            "密切观察病情变化，注意防跌倒、防坠床。",
            "向患者及家属交代病情，嘱清淡饮食，适当下床活动。",
            "患者情绪稳定，配合治疗。",
            "今日查房，患者诉偶有切口疼痛，予以心理安慰后缓解。",
            "引流管通畅，引流出淡红色液体约50ml。"
        ]
        res = ""
        while len(res) < min_len:
            res += random.choice(corpus)
        return res[:max_len]

    def _safe_wait(self, ec, timeout=40, stage="未知阶段"):
        """带报错信息的等待封装"""
        try:
            return WebDriverWait(self.driver, timeout).until(ec)
        except TimeoutException:
            raise Exception(f"<{stage}> 等待超时，页面响应过慢")

    def _select_last_record_robust(self):
        """强力选中最新病历逻辑：精准锁定病历树滚轮 + 懒加载处理"""
        stage = "定位病历节点"
        print(f"🔍 正在执行: {stage}...")

        # 1. 精准锁定病历树滚动容器
        try:
            scroll_container = self.driver.find_element(By.CSS_SELECTOR, "div.split-left div.tree-view.scroll")
        except:
            raise Exception(f"<{stage}> 未找到病历树专用滚动条")

        # 2. 深度滚动到底部
        last_h = 0
        for i in range(12):
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
            sleep(2.5)  # 给虚拟滚动渲染留出充足时间
            new_h = self.driver.execute_script("return arguments[0].scrollHeight", scroll_container)
            if new_h == last_h: break
            last_h = new_h

        # 3. 锁定最后一条病历并提取 No.
        target_xpath = "(//div[contains(@class,'split-left')]//span[@class='tree-node-text' and contains(text(), '日常病程')])[last()]"

        for attempt in range(5):
            try:
                node = self.driver.find_element(By.XPATH, target_xpath)
                node_text = node.text

                # 更新 error_identity：加入 No 编号
                no_match = re.search(r'No\.(\d+)', node_text)
                no_suffix = f"_No{no_match.group(1)}" if no_match else "_NoUnknown"
                # 拼接：床号姓名 + 编号
                self.error_identity = self.error_identity.split('_No')[0] + no_suffix

                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", node)
                sleep(1.5)

                # 点击并激活焦点
                try:
                    node.click()
                except:
                    self.driver.execute_script("arguments[0].click();", node)

                # 强行按一下右键，确保树节点被物理激活，方便后续 DOWN 键切入
                ActionChains(self.driver).move_to_element(node).click().send_keys(Keys.RIGHT).perform()
                return
            except (StaleElementReferenceException, NoSuchElementException):
                sleep(3)
                continue
        raise Exception(f"<{stage}> 无法点击最新记录")

    def _execute_case_create(self):
        # 1. 首页加载检查
        self.open_page("base/1046")
        # 针对并发环境，大幅延长初始等待，确保 Blazor 环境就绪
        self._safe_wait(
            EC.invisibility_of_element_located((By.XPATH, "//i[contains(@class, 'fa-spinner')]")),
            90, "等待首页加载(Spinner)"
        )
        # 额外检查搜索框是否出现，确保 DOM 已完全挂载
        self._safe_wait(EC.presence_of_element_located((By.CSS_SELECTOR, ".tree-search")), 40, "检查首页DOM就绪")
        sleep(5)

        # 2. 选择患者
        stage_patient = "选择患者阶段"
        target_patient = None
        patient_xpath = "//div[@class='tree-node' and .//span[contains(text(), '【')]]"

        for attempt in range(6):
            try:
                patients = self.driver.find_elements(By.XPATH, patient_xpath)
                if patients:
                    target_patient = random.choice(patients)
                    # 保存床号和姓名到变量
                    self.error_identity = target_patient.text.replace('[', '_').replace(']', '_')
                    break
            except:
                pass
            sleep(4)

        if not target_patient: raise Exception(f"<{stage_patient}> 患者列表始终为空")
        self.driver.execute_script("arguments[0].click();", target_patient)
        sleep(10)  # 选中后给 10 秒加载病历详情

        # 3. 新建流程
        self._safe_wait(EC.element_to_be_clickable((By.XPATH, "//a[.//span[text()='住院病历']]")), 40,
                        "住院页签").click()
        sleep(5)
        self._safe_wait(EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='新建病历']]")), 40,
                        "新建按钮").click()
        sleep(8)

        # 4. 模板弹窗 加入滚动
        modal = self._safe_wait(EC.presence_of_element_located((By.CSS_SELECTOR, "div.modal.show")), 30, "等待模板弹窗")
        scroll_area = modal.find_element(By.CSS_SELECTOR, "div.tree-view.scroll")

        def find_tpl(txt):
            for _ in range(12):
                spans = modal.find_elements(By.CSS_SELECTOR, "span.tree-node-text")
                for s in spans:
                    if txt in s.text: return s
                self.driver.execute_script("arguments[0].scrollTop += 150;", scroll_area)
                sleep(3)
            return None

        # 找分类
        group = find_tpl("病程记录")
        if not group: raise Exception("未找到病程记录分类")
        try:
            parent = group.find_element(By.XPATH, "./ancestor::div[contains(@class, 'tree-content')][1]")
            caret = parent.find_element(By.CSS_SELECTOR, ".node-icon[class*='caret-right']")
            self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", caret)
            sleep(4)
        except:
            pass

        # 选子项
        daily = find_tpl("日常病程记录")
        if not daily: raise Exception("未找到日常病程模板")
        self.driver.execute_script("arguments[0].click();", daily)
        sleep(2)
        modal.find_element(By.XPATH, ".//button[.//span[contains(., '确认')]]").click()

        self._safe_wait(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.modal.show")), 40, "关闭模板弹窗")
        sleep(12)  # 并发时树刷新非常慢，必须多等

        # 5. 选中最新病历 (此处会补齐 No 编号)
        self._select_last_record_robust()
        sleep(4)

        # 6. 输入正文
        print(f"✍️ 正在输入: {self.error_identity}...")
        actions = ActionChains(self.driver)
        # ENTER 强行激活编辑器 -> 停顿 -> DOWN 跳转输入区
        actions.send_keys(Keys.ENTER).pause(2).send_keys(Keys.DOWN).pause(2).perform()
        actions.send_keys(self._get_random_text()).perform()
        sleep(3)

        # 7. 保存并验证
        save_btn = self._safe_wait(EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='保存病历']]")), 30,
                                   "点击保存")
        self.driver.execute_script("arguments[0].click();", save_btn)

        # 验证提示
        success = False
        timeout_limit = time() + 30
        while time() < timeout_limit:
            msgs = self.driver.find_elements(By.CSS_SELECTOR, "div.message, [role='alert'], .ant-message")
            for m in msgs:
                try:
                    if any(kw in m.text for kw in ["成功", "完成", "Saved"]):
                        success = True;
                        break
                except:
                    continue
            if success: break
            sleep(2.5)

        if not success:
            raise Exception("保存验证超时：未监测到成功弹窗")

        sleep(5)
