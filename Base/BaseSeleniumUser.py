import os
import time
import traceback
from typing import Callable, Union, Literal, TypeVar, Tuple
from locust import User, task, between
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

D = TypeVar("D", bound=Union[WebDriver, WebElement])
T = TypeVar("T")
# ===========================================================
# 🏆 抽象基类：封装 Selenium、
# ===========================================================
class BaseSeleniumUser(User):
    wait_time = between(1, 3)
    abstract = True

    # 配置
    @property
    def url(self) -> str:
        return self.on_get_url()

    dept: str = ""
    role: str = ""
    debug: bool = True

    # 常量
    driver = None
    mask_locator = (By.CSS_SELECTOR, "div.bb-mask-backdrop")



    def on_start(self):
        """启动 Selenium 并自动登录"""
        # 不要开VPN,否则密码泄露提示无法关闭
        opts = webdriver.ChromeOptions()
        if not self.debug:
            opts.add_argument("--headless=new") # 不显示浏览器
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--force-device-scale-factor=1")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(options=opts)
        self.driver.set_window_size(1920, 1080)
        self.driver.set_page_load_timeout(15)

        print("🚀 浏览器已启动，开始自动登录...")
        user, pwd = self.on_get_user()
        self.login(self.dept, self.role, user, pwd)


    def on_stop(self):
        """关闭浏览器"""
        self.driver.quit()

    @task
    def _test_task(self):
        start = time.time()
        try:
            self.on_task()
            pass
            # 上报成功
            duration = (time.time() - start) * 1000
            self.environment.events.request.fire(
                request_type="selenium",
                name=self.__class__.__name__,
                response_time=duration,
                response_length=0,
                exception=None,
            )
        except Exception as ex:
            # 上报失败
            duration = (time.time() - start) * 1000
            error_message = traceback.format_exc()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            folder = f"fails/{self.__class__.__name__}"
            os.makedirs(folder, exist_ok=True)  # ← 必须有这句

            filename = f"{folder}/{ex.__class__.__name__}_{timestamp}.png"

            ok = self.driver.save_screenshot(filename)

            print("Screenshot saved:", filename, "success:", ok)
            self.environment.events.request.fire(
                request_type="selenium",
                name=self.__class__.__name__,
                response_time=duration,
                response_length=0,
                exception=error_message,
            )

    def on_task(self) -> None:
        """
        测试任务
        :return:
        :raise: Exception 不返回值, 失败直接抛异常
        """
        pass

    def on_get_user(self) -> Tuple[str, str]:
        """
        获取用户名和密码
        :return: (username, pwd)
        """
        return '009999', '302xxk'

    def on_get_url(self) -> str:
        return "http://192.168.21.61:8062/"
    # ===========================================================
    # 🧩 通用脚本方法
    # ===========================================================
    def open_page(self, path: str):
        self.driver.get(f"{self.url}{path}")

    def sleep(self, t: int=4):
        """
        阻塞等待
        :param t: 等待时间
        :return:
        """
        time.sleep(t)

    def wait_until(self,conditions: Callable[[D], Union[Literal[False], T]], timeout: int=10):
        """
        设置超时操作
        :param conditions: 元素条件
        :param timeout: 超时时间
        :return:
        """
        return WebDriverWait(self.driver, timeout).until(conditions)

    def wait_until_not(self,conditions: Callable[[D], Union[Literal[False], T]], timeout: int=10):
        """
        设置超时操作
        :param conditions: 元素条件
        :param timeout: 超时时间
        :return:
        """
        return WebDriverWait(self.driver, timeout).until_not(conditions)

    def wait_mask(self, appear_timeout: float=3, disappear_timeout: float=5):
        """
        等待遮罩出现和消失
        :param appear_timeout: 出现超时时间
        :param disappear_timeout: 消失超时时间
        :return:
        """
        # 等待遮罩出现
        try:
            WebDriverWait(self.driver, appear_timeout).until(
                EC.presence_of_element_located(self.mask_locator)
            )
        except TimeoutException:
            raise TimeoutException(f"遮罩未在 {appear_timeout}s 内出现！")

        # 等待遮罩消失
        try:
            WebDriverWait(self.driver, disappear_timeout).until_not(
                EC.presence_of_element_located(self.mask_locator)
            )
        except TimeoutException:
            raise TimeoutException(f"遮罩未在 {disappear_timeout}s 内消失！")



    # ===========================================================
    # 🔐 登录流程
    # ===========================================================

    def login(self, dept: str, role: str, username: str='009999', password: str='302xxk'):
        """统一封装好的登录方法"""

        try:
            # 进入首页
            self.driver.get(self.url)

            # 用户名
            username_input = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//label[normalize-space()='用户名']/following-sibling::input"))
            )
            username_input.clear()
            username_input.send_keys(username)

            # 密码
            pwd_input = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//label[normalize-space()='密码']/following-sibling::input"))
            )
            pwd_input.clear()
            pwd_input.send_keys(password)

            # 登录按钮
            button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.TAG_NAME, "button"))
            )
            button.click()

            # 科室
            dept_input = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='检索：']/following-sibling::input"))
            )
            dept_input.send_keys(dept)

            # 角色（第二个输入）
            role_input = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "(//div[text()='检索：']/following-sibling::input)[2]")
                )
            )
            role_input.send_keys(role)
            # 确认
            confirm_button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='确认']]"))
            )
            confirm_button.click()
            time.sleep(2)

            print("✅ 登录成功")

        except Exception as e:
            print("❌ 登录失败:", e)
            raise e