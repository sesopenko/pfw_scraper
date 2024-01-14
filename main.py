from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from typing import List

import logging


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    options = webdriver.FirefoxOptions()
    options.add_argument('--private')
    driver = webdriver.Firefox(options=options)
    main_site = 'https://pathfinderwiki.com'
    geography_page = "https://pathfinderwiki.com/wiki/Portal:Geography"
    driver.get(geography_page)
    expected_text = 'Geography of Golarion'
    logging.info(f'Waiting for "{expected_text}"...')
    wait_for_text(driver, expected_text)
    scrape_queue = []
    scrape_queue = add_golarion_regions(driver, scrape_queue)
    logging.info(f'Scrape queue: {scrape_queue}')


def add_golarion_regions(driver, scrape_queue: List[str]) -> List[str]:
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
    return scrape_queue + region_queue


def wait_for_text(driver, expected_text):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//div[contains(text(), '{expected_text}')]"))
    )


if __name__ == '__main__':
    main()