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

    history = set()
    level1_links = set()
    level2_links = set()
    level3_links = set()
    level1_links = get_religion_links(driver, level1_links)
    level1_links = get_creature_level1(driver, level1_links)
    level1_links = get_inhabitant_links(driver, level1_links)
    level1_links = get_geography_links(driver, level1_links)

    logging.info('beginning walk of level1_links')
    for url in level1_links:
        level2_links |= process_page(driver, url)
        history.add(url)
    level2_links -= history
    logging.info('beginning walk of level2_links')
    for url in level2_links:
        level3_links |= process_page(driver, url)
        history.add(url)
    driver.quit()


def get_geography_links(driver, level1_links: Set[str]) -> Set[str]:
    logging.info('getting geography links')
    destination_url = "https://pathfinderwiki.com/wiki/Portal:Geography"
    get_wait_and_clean(driver, destination_url)
    level1_links |= get_contentbox_links(driver, 'Teleport')
    level1_links |= get_contentbox_links(driver, 'Other Continents')
    return level1_links

def get_inhabitant_links(driver: RemoteWebDriver, level1_links: Set[str]) -> Set[str]:
    logging.info('getting inhabitant links')
    destination_url = "https://pathfinderwiki.com/wiki/Portal:Inhabitants"
    get_wait_and_clean(driver, destination_url)

    ancestry_links = get_contentbox_links(driver, 'Ancestries')

    return level1_links | ancestry_links

def get_religion_links(driver: RemoteWebDriver, level1_links: Set[str]) -> Set[str]:
    logging.info('getting religion links')
    destination_url = "https://pathfinderwiki.com/wiki/Portal:Religion"
    get_wait_and_clean(driver, destination_url)

    links = get_contentbox_links(driver, 'Deities & pantheons')
    links = {item for item in links if 'Category' not in str(item)}

    return level1_links | links

def get_creature_level1(driver: RemoteWebDriver, level1_links: Set[str]) -> Set[str]:
    logging.info('Getting creature pages')
    destination_url = "https://pathfinderwiki.com/wiki/Category:Creatures_by_CR"
    get_wait_and_clean(driver, destination_url)
    elem = driver.find_element(By.ID, 'mw-content-text')
    base_links = set()
    potential_links = elem.find_elements(By.XPATH, "//a[not(@class='new')]")
    new_links = set()
    for link in potential_links:
        href = link.get_attribute('href')
        if url_is_useful(href):
            base_links.add(href)
    for inhabitant_link in base_links:
        logging.info(f'Getting create page but not saving: {inhabitant_link}')
        sub_links = process_page(driver, inhabitant_link, False)
        sub_links = {item for item in sub_links if 'Category' not in str(item)}
        new_links |= sub_links
    new_links = {item for item in new_links if 'Category' not in str(item)}
    return level1_links | new_links

def is_empty_page(driver: RemoteWebDriver) -> bool:
    result = driver.execute_script("""
            var my_test_e = document.getElementsByClassName('banner')
            if (my_test_e.length == 0) { return ''; }
            var my_e = my_test_e[0]
            return my_e.textContent
            """)
    if isinstance(result, str):
        if 'This page is a stub' in result:
            return True
    result = driver.execute_script("""
                var my_test_e = document.getElementsByClassName('mw-category-generated')
                if (my_test_e.length == 0) { return ''; }
                var my_e = my_test_e[0]
                return my_e.textContent
                """)
    if isinstance(result, str):
        if 'This category currently contains no pages or media' in result:
            return True
    return False

def process_page(driver: RemoteWebDriver, url: str, write_page=True) -> Set[str]:
    found_links = set()

    get_wait_and_clean(driver, url)
    if is_empty_page(driver):
        return set()
    potential_links = driver.find_elements(By.XPATH, "//a[not(@class='new')]")
    for link in potential_links:
        href = link.get_attribute('href')
        if url_is_useful(href):
            found_links.add(href.split('#')[0].split('?')[0])

    if write_page:
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

def url_is_useful(url) -> bool:
    if isinstance(url, str):
        if 'Pathfinder_campaign_setting' in url:
            # this is meta
            return False
        is_wiki = 'https://pathfinderwiki.com' in url
        if not is_wiki:
            return False
        url = url.split('#')[0].split('?')[0]
        is_year_url = url.endswith('_AR')
        is_wiki_meta = '/PathfinderWiki' in url or '/Pathfinder_Wiki' in url
        if not url.endswith('.php') and not is_year_url and not is_wiki_meta:
            return True
    return False

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
        // Unfortunately this is too much white noise:
        $('.infobox').remove();
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
    links = content_box.find_elements(By.XPATH, "//a[not(@class='new')]")
    for link in links:
        url = link.get_attribute('href')
        if url_is_useful(url):
            link_urls.add(url)
    return link_urls

def wait_for_first_heading(driver: RemoteWebDriver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'firstHeading'))
    )

if __name__ == '__main__':
    main()