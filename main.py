import time

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from urllib.parse import urlparse
import os
from pathlib import Path

from typing import List, Set
import re

import logging

store_loc = 'scraped'


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    options = webdriver.FirefoxOptions()
    options.add_argument('--private')
    driver = webdriver.Firefox(options=options)
    driver.implicitly_wait(5)
    destination_url = "https://pathfinderwiki.com/wiki/Portal:Geography"
    get_wait_and_clean(driver, destination_url)

    history = set()
    level1_links = get_contentbox_links(driver, 'Teleport')
    level1_links |= get_contentbox_links(driver, 'Other Continents')
    logging.info(f'Found link urls: %s', level1_links)

    level2_links = set()
    for url in level1_links:
        level2_links |= process_page(driver, url)
        history.add(url)
    level2_links -= history
    driver.quit()


def process_page(driver: RemoteWebDriver, url: str) -> Set[str]:
    found_links = set()
    get_wait_and_clean(driver, url)
    potential_links = driver.find_elements(By.XPATH, "//a[not(@class='new')]")
    for link in potential_links:
        href = link.get_attribute('href')
        if isinstance(href, str):
            href = href.split('#')[0].split('?')[0]
            is_year_url = href.endswith('_AR')
            is_wiki_meta = '/PathfinderWiki' in href or '/Pathfinder_Wiki' in href
            if not href.endswith('.php') and not is_year_url and not is_wiki_meta:
                found_links.add(href.split('#')[0].split('?')[0])

    strip_extra_reading_links(driver)
    current_url = driver.current_url
    path_sections = [section for section in urlparse(current_url).path.split('/') if section]
    path_sections[-1] = path_sections[-1] + '.html'
    store_loc = Path(os.path.join(*(['scraped'] + path_sections)))
    logging.info(f'Writing to: {store_loc}')
    html_content = driver.page_source
    directory = os.path.dirname(store_loc)
    os.makedirs(directory, exist_ok=True)
    with open(store_loc, 'w') as file: file.write(html_content)
    return found_links

def get_wait_and_clean(driver: RemoteWebDriver, destination_url: str):
    driver.get(destination_url)
    wait_for_first_heading(driver)
    strip_garbage(driver)

def strip_garbage(driver: RemoteWebDriver):
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
        // We can't interpret these any ways:
        $('div.image').remove();
        $('#vector-toc-collapsed-button').remove();
        $('#left-navigation').remove();
        $('#right-navigation').remove();
        $('.displaymap').remove();
        $('.mw-table-of-contents-container').remove();
        $('#catlinks').remove();
        $('#References').remove();
        $('.reference-text').remove();
        $('#articleReferences').remove();
        $('.navbox').remove();
        $('#p-search').remove();
        // remove html comments
        $('*').contents().filter(function () {
            return this.nodeType === 8; // Filter for comment nodes
          }).remove(); // Remove comment nodes
    });
    
    """)
    time.sleep(0.1)

def strip_extra_reading_links(driver: RemoteWebDriver):
    driver.execute_script("""
        $('.relarticle').remove();
        
        """)
    time.sleep(0.1)


def get_contentbox_links(driver: RemoteWebDriver, title: str) -> Set[str]:
    link_urls = set()
    content_box = driver.find_element(By.XPATH, f"//*[@class='content-box' and *[@class='title' and text()='{title}']]")
    links = content_box.find_elements(By.TAG_NAME, 'a')
    for link in links:
        url = link.get_attribute('href')
        if url.startswith('https://pathfinderwiki.com') and url not in link_urls:
            link_urls.add(url)
    return link_urls

def wait_for_first_heading(driver: RemoteWebDriver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'firstHeading'))
    )

if __name__ == '__main__':
    main()