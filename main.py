from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from lxml import etree
import chromedriver_autoinstaller
import pandas as pd
import time
import random

all_properties = set()
columns = [
    "Business_Type",
    "Business_Name",
    "Business_SubType",
    "Business_FullAddressAndPostCode",
    "Business_Booking.com_URL",
    "Business_Hotel_Star",
    "Business_Source",
    "Business_SourceSearch",
    "Booking.com_DoWePriceMatch",
    "Booking.com_Review_NumberOfReviews",
    "Booking.com_Review_Score",
    "Booking.com_Review_SummaryText",
    "Booking.com_Best_Rating_Name",
    "Booking.com_Best_Rating_Score"
]
BNB_Keywords = [
    "B&B",
    "Bed & Breakfast",
    "Inn",
    "Guest House",
    "Lodge",
    "Cottage",
    "Homestay",
    "Pension",
    "Farmhouse",
    "Retreat",
    "Manor",
    "Villa",
    "Country House",
    "Residence",
    "Cabin",
    "Chalet",
    "Estate",
    "House",
    "Barn",
    "Studio"
]
Hotel_Keywords = [
    "Hotel",
    "Motel",
    "Resort",
    "Suites",
    "Inn",
    "Lodge",
    "Hostel",
    "Boutique Hotel",
    "Luxury Hotel",
    "Business Hotel",
    "Conference Hotel",
    "Spa",
    "Retreat",
    "Guesthouse",
    "Stay",
    "Palace",
    "House",
    "Manor",
    "Residence",
    "Accommodation"
]
Apartment_Keywords = [
    "Apartment",
    "Apartments",
    "Flat",
    "Flats"
    "Studio",
    "Studios",
    "Suite",
    "Suites",
    "Residence",
    "Loft",
    "Lofts",
    "Condos",
    "Condominium",
    "Condo",
    "Apart-Hotel",
    "Apartel",
    "Holiday Apartment",
    "Vacation Apartment",
    "Serviced Apartment",
    "Aparthotel"
]
data_for_each_link = {
    "Business_Type": "Hotel",
    "Business_Name": "",
    "Business_SubType": "",
    "Business_FullAddressAndPostCode": "",
    "Business_Booking.com_URL": "",
    "Business_Hotel_Star": "",
    "Business_Source": "Booking.com",
    "Business_SourceSearch": "",
    "Booking.com_DoWePriceMatch": "",
    "Booking.com_Review_NumberOfReviews": "",
    "Booking.com_Review_Score": "",
    "Booking.com_Review_SummaryText": "",
    "Booking.com_Best_Rating_Name": "",
    "Booking.com_Best_Rating_Score": ""
}
all_content_loaded = False
close_button_css = '[aria-label="Dismiss sign in information."]'
current_url = ""


def find_business_type(title):
    for w in BNB_Keywords:
        if w in title:
            return "B&B"
    for w in Hotel_Keywords:
        if w in title:
            return "Hotel"
    for w in Apartment_Keywords:
        if w in title:
            return "Apartment"
    return random.choice(["B&B", "Hotel", "Apartment"])


def initialize_options(options):
    # options.add_argument(r"user-data-dir=C:\Users\Administrator\AppData\Local\Google\Chrome\User Data")
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")


def random_wait(min_secs=2, max_secs=5):
    time.sleep(random.uniform(min_secs, max_secs))


opts = Options()
initialize_options(opts)

chromedriver_autoinstaller.install()
driver = webdriver.Chrome(options=opts)


def manual_stealth(drv):
    drv.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined})"
    })
    drv.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters)
            );
        """
    })
    drv.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});"
    })
    drv.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});"
    })


def ask_user(to_ask, digital=False, special_term=0):
    user_response = False
    while not user_response:
        time.sleep(1)
        if digital:
            try:
                user_response = int(input(to_ask))
                if user_response > special_term or user_response < 0:
                    user_response = False
                    raise ValueError
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        else:
            user_response = input(f"{to_ask}")
    return user_response


def switch_url(town_name):
    global current_url
    source_search = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="Where are you going?"]')
    for i in range(8):
        source_search.send_keys(Keys.BACKSPACE)
    source_search.send_keys(f"{town_name}")
    time.sleep(1.5)
    source_search.send_keys(Keys.ENTER)
    current_url = driver.current_url
    driver.get(current_url)


def click_buttons(elem):
    is_it_true = False
    try_again = 0
    while not is_it_true:
        try:
            if try_again < 3:
                element = WebDriverWait(driver, 5).until(ec.presence_of_element_located(elem))
                element.click()
                is_it_true = True
                try_again = 0
            else:
                is_it_true = True
        except (exceptions.NoSuchElementException, exceptions.TimeoutException):
            try_again += 1
    return is_it_true


manual_stealth(driver)
url = ask_user("Enter the url you want to scrape:")
driver.get(url)

def save_data_as_csv(data):
    df = pd.DataFrame(data, columns=columns)
    df.to_csv('data.csv', index=False, mode="a", header=False)


def extract_six_common_fields(business, title_text):
    # TODO: Business Type
    data_for_each_link["BusinessType"] = find_business_type(title_text)

    # TODO: Business Name
    data_for_each_link["BusinessName"] = title_text

    # TODO: Business Booking.com URL
    link = business.find('a', class_='PropertyCard__Link').get("href")
    data_for_each_link["BusinessBooking.com_URL"] = f"https://www.agoda.com{link}"


def extract_star_ratings(business):
    # TODO: Rating Stars
    business_dom = etree.HTML(str(business))
    stars = business_dom.xpath("//span[contains(normalize-space(.), 'stars out of')]")
    if len(stars) > 0:
        data_for_each_link["Hotel_Star"] = stars[0].text[0]
    else:
        data_for_each_link["Hotel_Star"] = 0


def extract_business_address(h3_elements, title_text):
    # TODO: Business Complete Address
    for elem in h3_elements:
        if elem.text == title_text:
            elem.click()
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
            WebDriverWait(driver, 60).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, '[data-selenium="hotel-address-map"]')))
            address = driver.find_element(By.CSS_SELECTOR, '[data-selenium="hotel-address-map"]')
            complete_address = address.text.split(",")
            data_for_each_link["BusinessAddress"] = complete_address[0] if len(complete_address) > 0 else ""
            data_for_each_link["BusinessVillageTownCity"] = complete_address[1] if len(complete_address) > 1 else ""
            data_for_each_link["BusinessCountry"] = complete_address[2] if len(complete_address) > 2 else ""
            data_for_each_link["BusinessCountryMain"] = complete_address[3] if len(complete_address) > 3 else ""
            data_for_each_link["BusinessPostCode"] = complete_address[4] if len(complete_address) > 4 else ""
            driver.close()
            if len(driver.window_handles) > 0:
                driver.switch_to.window(driver.window_handles[0])


def manage_data(business, h3_elements):
    title = business.find(attrs={"data-selenium": "hotel-name"})
    title_text = title.text
    extract_six_common_fields(business, title_text)
    extract_star_ratings(business)
    extract_business_address(h3_elements, title_text)
    save_data_as_csv([data_for_each_link])
    for i, key in enumerate(data_for_each_link):
        if i != 5:
            data_for_each_link[key] = ""


def find_data():
    global try_again_count
    try:
        cancel = driver.find_element(By.XPATH, "//button[normalize-space(.)='No thanks']")
        cancel.click()
    except exceptions.NoSuchElementException:
        pass

    # TODO: Scroll and Initialize BS4
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(document.body.scrollHeight, 0);")

    # TODO: Collect On Screen Business List
    WebDriverWait(driver, 30).until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, ".PropertyCardItem")))
    properties = soup.find_all(attrs={"class": "PropertyCardItem"})
    WebDriverWait(driver, 30).until(
        ec.visibility_of_all_elements_located((By.CSS_SELECTOR, '[data-selenium="hotel-name"]')))
    h3_elements = driver.find_elements(By.CSS_SELECTOR, '[data-selenium="hotel-name"]')

    # TODO: Manage Data
    for business in properties:
        if business not in all_properties:
            try:
                print(business.find(attrs={"data-selenium": "hotel-name"}).text)
                manage_data(business, h3_elements)
                try_again_count = 0
            except AttributeError:
                all_properties.add(business)
                continue
            except (exceptions.TimeoutException, exceptions.NoSuchElementException):
                if try_again_count < 5:
                    if len(driver.window_handles) > 0:
                        driver.switch_to.window(driver.window_handles[0])
                    try_again_count += 1
                    manage_data(business, h3_elements)
                else:
                    pass
            all_properties.add(business)
    WebDriverWait(driver, 10).until(
        ec.visibility_of_element_located((By.XPATH, "// span[text() = 'Next']")))
    load_more = driver.find_element(By.XPATH, "// span[text() = 'Next']")
    load_more.click()
    "ALL DATA HAS BEEN SCRAPED"


df = pd.DataFrame(columns=columns)
df.to_csv('data.csv', index=False)
find_data()
