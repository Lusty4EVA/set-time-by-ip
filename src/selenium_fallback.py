from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_timezone_by_selenium(chrome_binary=None):
    options = Options()
    if chrome_binary:
        options.binary_location = chrome_binary
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://proxy6.net/privacy")
        tz = driver.find_element(
            By.XPATH,
            "/html/body/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div[4]/dl[1]/dd"
        ).text
        return tz.strip()
    finally:
        driver.quit()
