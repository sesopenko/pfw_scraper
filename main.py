from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from typing import List

import logging


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    options = webdriver.FirefoxOptions()
    options.add_argument('--private')
    driver = webdriver.Firefox(options=options)
    driver.implicitly_wait(5)
    geography_page = "https://pathfinderwiki.com/wiki/Portal:Geography"
    driver.get(geography_page)
    strip_garbage(driver)
    expected_text = 'Geography of Golarion'
    logging.info(f'Waiting for "{expected_text}"...')
    wait_for_first_heading(driver)

    main_geography_urls = get_contentbox_links(driver, 'Teleport')
    logging.info(f'Found link urls: %s', main_geography_urls)
    other_contentbox_links = get_contentbox_links(driver, 'Other Continents')
    logging.info(f'Found link urls: %s', other_contentbox_links)
    driver.quit()


def strip_garbage(driver):
    driver.execute_script("""
    $('document').ready(function(){
        $('#mw-navigation').remove();
        $('#footer').remove();
        $('#mw-navigation').remove();
        $('#footer').remove();
        $('#ca-view').remove();
        $('#ca-viewsource').remove();
        $('#ca-history').remove();
        $('#pt-createaccount-2').remove();
    });
    """)


def get_contentbox_links(driver: RemoteWebDriver, title: str) -> List[str]:
    link_urls = []
    content_box = driver.find_element(By.XPATH, f"//*[@class='content-box' and *[@class='title' and text()='{title}']]")
    links = content_box.find_elements(By.TAG_NAME, 'a')
    for link in links:
        url = link.get_attribute('href')
        if url.startswith('https://pathfinderwiki.com') and url not in link_urls:
            link_urls.append(url)
    return link_urls

def get_golarion_regions(driver: RemoteWebDriver) -> List[str]:
    logging.info('Scraping for regions')
    region_elements = driver.find_elements(By.CLASS_NAME, 'mw-headline')
    region_queue = []
    for region_element in region_elements:
        link = region_element.find_element(By.TAG_NAME, 'a')
        local_link = link.get_attribute('href')
        if local_link.startswith('/'):
            logging.error(f'Skipping {local_link} local link')
        if local_link.startswith('https://'):
            region_queue.append(local_link)
    logging.info(f'Adding {len(region_queue)} pages to scrape_queue')
    return region_queue

def get_other_continents(driver: RemoteWebDriver) -> List[str]:
    logging.info('Scraping for other continents')
    links = driver.find_elements(By.XPATH, "//div[contains(text(), 'Other Continents')]/following-sibling::div[@class='content']//a")
    local_queue = []
    for link in links:
        local_queue.append(link.get_attribute('href'))
    logging.info(f'Adding {len(local_queue)} links for other continents')
    return local_queue




def wait_for_text(driver, expected_text):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//div[contains(text(), '{expected_text}')]"))
    )

def wait_for_first_heading(driver: RemoteWebDriver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.Id, 'firstHeading'))
    )

if __name__ == '__main__':
    main()