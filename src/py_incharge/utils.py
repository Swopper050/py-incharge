from selenium.webdriver.common.by import By
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
