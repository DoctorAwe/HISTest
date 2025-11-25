"""
author: Dr.Awe
date：2025/11/24
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
import pytest

@pytest.fixture
def browser():
    # 启动 Chrome
    driver = webdriver.Chrome()
    yield driver
    # 测试结束后关闭浏览器
    driver.quit()

def test_google_title(browser):
    browser.get("http://localhost:5000")
    assert "医院信息管理系统" in browser.title

### locust -f locustfile.py
##  locust -f test_EMR_save.py


### locust -f locustfile.py --users 1 --spawn-rate 1 --headless
