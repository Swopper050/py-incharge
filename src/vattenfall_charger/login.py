import logging
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


def find_element_through_shadow(driver, hosts_css_chain, leaf_css, timeout=5):
    """
    Walks a chain of shadow-DOM hosts, returns the element that matches `leaf_css`
    inside the last shadow root.

    hosts_css_chain : list[str]   → CSS selectors for each host in order
    leaf_css        : str         → CSS selector for the final element
    """

    wait = WebDriverWait(driver, timeout)
    root = driver
    for host_css in hosts_css_chain:
        host = wait.until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, host_css))
        )
        root = host.shadow_root

    return root.find_element(By.CSS_SELECTOR, leaf_css)


def get_bearer_token(email: str, password: str) -> str:
    logging.info("Starting the login process to retrieve the bearer token...")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--start-maximized")

    logging.info("Waiting for the login page to load...")
    driver = webdriver.Chrome(options=options)
    driver.get("https://myincharge.vattenfall.com/")

    try:
        logging.info("Filling in the login form...")
        email_input = find_element_through_shadow(
            driver,
            hosts_css_chain=["ic-input[formcontrolname='username']"],
            leaf_css="input",
        )
        email_input.send_keys(email)
        time.sleep(0.1)

        password_input = find_element_through_shadow(
            driver,
            hosts_css_chain=["ic-input[formcontrolname='password']"],
            leaf_css="input",
        )
        password_input.send_keys(password)
        time.sleep(0.2)

        logging.info("Submitting the login form...")
        password_input.send_keys(Keys.RETURN)
        time.sleep(3)

        logging.info("Waiting for the page to load after login...")
        for _ in range(10):
            token = driver.execute_script(
                "return window.sessionStorage.getItem('auth_token');"
            )
            if token:
                logging.info("Bearer token found in session storage.")
                return token

            time.sleep(1)

        driver.quit()

        raise Exception("Token not found in session storage.")
    finally:
        driver.quit()
