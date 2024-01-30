import logging
import os
import re
from datetime import datetime
import schedule
import time
import psycopg2
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests

DB_USER = "YOUR_USER"
DB_PASSWORD = "YOUR_PASSWORD"
DB_HOST = "YOUR_HOST"
DB_PORT = "YOUR_PORT"
DB_NAME = "YOUR_DB_NAME"
MAX_WORKERS = 5

logging.basicConfig(level=logging.INFO)


def get_database_connection():
    return psycopg2.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=DB_NAME)


def create_dumps_folder():
    if not os.path.exists("dumps"):
        os.makedirs("dumps")


def perform_database_dump():
    dump_filename = f"dumps/db_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    dump_command = f"pg_dump -h {DB_HOST} -U {DB_USER} -W {DB_PASSWORD} -d {DB_NAME} -Fc > '{dump_filename}'"
    os.system(dump_command)


def insert_into_database(data):
    try:
        connection = get_database_connection()
        with connection, connection.cursor() as cursor:
            insert_query = """
                INSERT INTO YOURTABLE (url, title, price_usd, odometer, username, phone_number, image_url, images_count, car_number, car_vin, datetime_found)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            cursor.execute(insert_query, (
                data['url'],
                data['title'],
                data['price_usd'],
                data['odometer'],
                data['username'],
                data['phone_number'],
                data['image_url'],
                data['images_count'],
                data['car_number'],
                data['car_vin'],
                data['datetime_found']
            ))
    except (Exception, psycopg2.Error) as error:
        logging.error("Error while connecting to PostgreSQL: %s", error)


def get_vin_car(driver):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "label-vin"))
        )
        return element.text
    except Exception as e:
        return ""


def parse_price(price_text):
    digits_only = re.sub(r'\D', '', price_text)
    if digits_only:
        return int(digits_only)
    else:
        return None


def get_element_text(driver, selector):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element.text.strip()
    except Exception as e:
        return ""


def get_odometer(driver):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.base-information span.size18'))
        )
        value = element.text.strip().replace(' тыс.', '').replace(',', '')
        return int(value) * 1000
    except Exception as e:
        return 0


def get_car_number(driver, class_name):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_name))
        )
        return element.text.strip().split(' ', 1)[1]
    except Exception as e:
        return ""


def get_image_url(driver, selector):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element.get_attribute("src")
    except Exception as e:
        return ""


def get_photo_count(driver, class_name):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_name))
        )
        count_text = element.text
        return int(count_text.split()[-1])
    except Exception as e:
        return 0


def get_phone_number(driver, show_button_class, phones_item_class, phone_class):
    try:
        show_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, show_button_class))
        )
        show_button.click()

        phone_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, phones_item_class))
        ).find_element(By.CLASS_NAME, phone_class)

        return phone_element.get_attribute("data-phone-number")
    except Exception as e:
        return ""


def parse_phone_number(phone_text):
    digits_only = re.sub(r'\D', '', phone_text)
    return digits_only


def parse_car_info(car_link):
    with webdriver.Chrome() as driver:
        driver.get(car_link)
        data = {
            'url': car_link,
            'title': get_element_text(driver, 'h1.head'),
            'price_usd': parse_price(get_element_text(driver, 'div.price_value')),
            'odometer': get_odometer(driver),
            'username': get_element_text(driver, 'div.seller_info_name.bold'),
            'car_number': get_car_number(driver, 'state-num'),
            'image_url': get_image_url(driver, 'img.outline.m-auto'),
            'images_count': get_photo_count(driver, 'count'),
            'car_vin': get_vin_car(driver),
            'datetime_found': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'phone_number': parse_phone_number(get_phone_number(driver, 'phone_show_link', 'phones_item', 'phone'))
        }
        insert_into_database(data)


def process_page(page_number):
    url = f"https://auto.ria.com/uk/car/used/?page={page_number}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', class_='m-link-ticket')]
    return links


def main():
    all_links = []
    page_number = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while True:
            futures = [executor.submit(process_page, page_number + i) for i in range(MAX_WORKERS)]
            for future in futures:
                links = future.result()
                if not links:
                    break
                all_links.extend(links)
            if not links:
                break
            page_number += MAX_WORKERS
    logging.info("Total links: %s", len(all_links))
    for car_link in all_links:
        parse_car_info(car_link)


if __name__ == "__main__":
    schedule.every().day.at("00:00").do(create_dumps_folder)
    schedule.every().day.at("00:00").do(perform_database_dump)
    schedule.every().day.at("12:00").do(main)

    while True:
        schedule.run_pending()
        time.sleep(1)
