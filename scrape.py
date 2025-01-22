import json
import csv
import zipfile
import string
import os
import time
import random
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import requests

# Load configuration from JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Set configuration variables
base_dir_path = config["base_directory"]
fb_username = config["fb_username"]
fb_password = config["fb_password"]

# Proxy details
proxy_host = config["proxy"]["host"]
proxy_port = config["proxy"]["port"]
proxy_username = config["proxy"]["username"]
proxy_password = config["proxy"]["password"]
country_code = config["proxy"]["country_code"]

# Function for scraping the real estate listings website
def scrape_website(website):
    print(base_dir_path)


    print("Launching chrome browser...")

    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    listings_data = []
    last_data_index = -1

    try:
        driver.get(website)
        print("Page loaded...")

        # Wait for the main scrollable container to load
        scrollable_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'StyledBox')]"))
        )
        print("Scrollable container found.")

        while True:
            # Scroll down a small step
            driver.execute_script("arguments[0].scrollTop += 300;", scrollable_container)
            time.sleep(4)

            # Wait for the master view div containing listings
            master_view_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'StyledDiv')]"))
            )
            print("Master view div loaded.")

            # Find all listing divs with data-index
            data_index_divs = WebDriverWait(master_view_div, 10).until(
                lambda d: d.find_elements(By.XPATH, "//div[@data-index]")
            )
            time.sleep(4)

            for div in data_index_divs:
                # Get the current data-index
                current_data_index = int(div.get_attribute("data-index"))
                time.sleep(4)

                if current_data_index > last_data_index:
                    last_data_index = current_data_index

                    # Find and process individual listings
                    listings = WebDriverWait(div, 10).until(
                        lambda d: d.find_elements(By.CLASS_NAME, "responsive-card")
                    )

                    for listing in listings:
                        try:
                            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(listing))
                            driver.execute_script("arguments[0].scrollIntoView(true);", listing)
                            listing.click()
                            time.sleep(2)
                            print(f"Clicked on listing with data-index {current_data_index}.")

                            report_div = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "report-TREB"))
                            )

                            addr_div = WebDriverWait(report_div, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "addr"))
                            )
                            property_address = addr_div.find_element(By.TAG_NAME, "h1").text
                            property_type = addr_div.find_element(By.TAG_NAME, "h2").text

                            price_div = WebDriverWait(report_div, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "price"))
                            )
                            price_element = WebDriverWait(price_div, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//span[@style='color:darkblue']"))
                            )
                            property_price = price_element.text.strip()

                            lease_label = WebDriverWait(price_div, 10).until(
                                EC.presence_of_element_located((By.XPATH, ".//label[contains(@class, 'label')]"))
                            )
                            sale_or_rent = lease_label.text.strip().lower()

                            description_div = WebDriverWait(report_div, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-section='Description']"))
                            )
                            description_span = WebDriverWait(description_div, 10).until(
                                EC.presence_of_element_located((By.XPATH, ".//span[@class='description readmore']"))
                            )
                            property_description = description_span.text

                            propertyInfo = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@id='section-property-info']"))
                            )

                            # Additional Information
                            bedrooms = get_property_info(propertyInfo, "Bedrooms")
                            washrooms = get_property_info(propertyInfo, "Washrooms")
                            square_feet = get_property_info(propertyInfo, "Square Feet")
                            square_feet_high = square_feet.split('-')[-1].strip() if '-' in square_feet else square_feet

                            parking_type = get_property_info(propertyInfo, "Garage Type")
                            ac_type = get_property_info(propertyInfo, "A/C")
                            laundry_type = get_property_info(propertyInfo, "Laundry Features")
                            heating_type = get_property_info(propertyInfo, "heating Source")

                            # Collect all extracted data
                            listing_info = {
                                "address": property_address,
                                "property_type": property_type,
                                "price": property_price,
                                "description": property_description,
                                "bedrooms_number": bedrooms,
                                "washrooms_number": washrooms,
                                "square_feet": square_feet_high,
                                "parking_type": parking_type,
                                "ac_type": ac_type,
                                "laundry_type": laundry_type,
                                "heating_type": heating_type,
                                "sale_or_rent": sale_or_rent
                            }

                            listings_data.append(listing_info)
                            print(f"Extracted listing {current_data_index}: {listing_info}")
                            print("-----------------------------------------------------------")

                            # Download images and save to a directory
                            download_listing_images(report_div, property_address)

                            # Navigate back to the main listings page
                            driver.back()

                            # Wait for the master view div to reload
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'StyledDiv')]"))
                            )

                        except Exception as e:
                            print(f"Error processing listing with data-index {current_data_index}: {e}")

                            report_div = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "report-TREB"))
                                )

                            addr_div = WebDriverWait(report_div, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "addr"))
                            )
                            property_address = addr_div.find_element(By.TAG_NAME, "h1").text

                            print("Error processing listing, ", property_address)
                            write_failed_listing(property_address, str(e))

                            driver.back()

            # Check if we have reached the end of the scrollable container
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_container)
            current_scroll = driver.execute_script("return arguments[0].scrollTop", scrollable_container)


            # Check if we've reached the bottom
            if current_scroll + scrollable_container.size['height'] >= new_height:
                # Final pass over any remaining listings after the last scroll
                data_index_divs = WebDriverWait(master_view_div, 10).until(
                    lambda d: d.find_elements(By.XPATH, "//div[@data-index]")
                )

                for div in data_index_divs:
                    current_data_index = int(div.get_attribute("data-index"))
                    if current_data_index > last_data_index:
                        last_data_index = current_data_index

                        listings = WebDriverWait(div, 10).until(
                            lambda d: d.find_elements(By.CLASS_NAME, "responsive-card")
                        )
                        for listing in listings:
                            try:
                                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(listing))
                                driver.execute_script("arguments[0].scrollIntoView(true);", listing)
                                listing.click()
                                time.sleep(2)

                                report_div = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "report-TREB"))
                                )

                                addr_div = WebDriverWait(report_div, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "addr"))
                                )
                                property_address = addr_div.find_element(By.TAG_NAME, "h1").text
                                property_type = addr_div.find_element(By.TAG_NAME, "h2").text

                                price_div = WebDriverWait(report_div, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "price"))
                                )
                                price_element = WebDriverWait(price_div, 10).until(
                                    EC.presence_of_element_located((By.XPATH, "//span[@style='color:darkblue']"))
                                )
                                property_price = price_element.text.strip()

                                lease_label = WebDriverWait(price_div, 10).until(
                                    EC.presence_of_element_located((By.XPATH, ".//label[contains(@class, 'label')]"))
                                )
                                sale_or_rent = lease_label.text.strip().lower()

                                description_div = WebDriverWait(report_div, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-section='Description']"))
                                )
                                description_span = WebDriverWait(description_div, 10).until(
                                    EC.presence_of_element_located((By.XPATH, ".//span[@class='description readmore']"))
                                )
                                property_description = description_span.text

                                propertyInfo = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, "//div[@id='section-property-info']"))
                                )

                                bedrooms = get_property_info(propertyInfo, "Bedrooms")
                                washrooms = get_property_info(propertyInfo, "Washrooms")
                                square_feet = get_property_info(propertyInfo, "Square Feet")
                                square_feet_high = square_feet.split('-')[-1].strip() if '-' in square_feet else square_feet

                                parking_type = get_property_info(propertyInfo, "Garage Type")
                                ac_type = get_property_info(propertyInfo, "A/C")
                                laundry_type = get_property_info(propertyInfo, "Laundry Features")
                                heating_type = get_property_info(propertyInfo, "heating Source")

                                listing_info = {
                                    "address": property_address,
                                    "property_type": property_type,
                                    "price": property_price,
                                    "description": property_description,
                                    "bedrooms_number": bedrooms,
                                    "washrooms_number": washrooms,
                                    "square_feet": square_feet_high,
                                    "parking_type": parking_type,
                                    "ac_type": ac_type,
                                    "laundry_type": laundry_type,
                                    "heating_type": heating_type,
                                    "sale_or_rent": sale_or_rent
                                }

                                listings_data.append(listing_info)
                                print(f"Extracted listing {current_data_index}: {listing_info}")
                                print("-----------------------------------------------------------")

                                download_listing_images(report_div, property_address)
                                time.sleep(2)
                                driver.back()

                                # Wait for the master view div to reload after navigating back
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'StyledDiv')]"))
                                )

                            except Exception as e:
                                print(f"Error processing listing with data-index {current_data_index}: {e}")

                                report_div = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.CLASS_NAME, "report-TREB"))
                                    )

                                addr_div = WebDriverWait(report_div, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "addr"))
                                )
                                property_address = addr_div.find_element(By.TAG_NAME, "h1").text

                                print("Error processing listing, ", property_address)
                                write_failed_listing(property_address, str(e))

                                driver.back()

                break  # Exit the loop after final processing

        # Write data to CSV after all listings are processed
        write_to_csv(listings_data)
        write_to_json(listings_data)
        print("Data successfully written to listings_data.csv")

        return listings_data

    finally:
        driver.quit()

def write_failed_listing(property_address, error_message):
    with open('failed_listings.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([property_address, error_message])
    print(f"Failed listing written to failed_listings.csv: {property_address}")

def write_to_json(listings_data):
    with open('listings_data.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(listings_data, jsonfile, ensure_ascii=False, indent=4)
    print("Data successfully written to listings_data.json")

def download_listing_images(driver, property_address):
    print(f"Extracting all thumbnail image URLs for listing at {property_address}...")

    image_urls = set()

    base_dir = os.path.join(base_dir_path, property_address)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"Created directory: {base_dir}")
    else:
        print(f"Directory already exists: {base_dir}")

    try:
        thumbnail_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, ".//button[contains(@class, 'image-gallery-thumbnail')]"))
        )

        for i, thumb_button in enumerate(thumbnail_buttons, 1):
            try:
                thumb_button.click()
                time.sleep(2)

                slide_xpath = f".//div[@aria-label='Go to Slide {i}']//img[@class='image-gallery-image']"
                main_image = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, slide_xpath))
                )
                image_url = main_image.get_attribute('src')

                if image_url in image_urls:
                    print(f"Duplicate image {image_url} found, skipping.")
                    continue

                image_urls.add(image_url)
                local_path = os.path.join(base_dir, f"main_image_{i}.jpg")
                download_image(image_url, local_path)
                print(f"Downloaded main image {i} to {local_path}")

            except Exception as e:
                print(f"Error processing main image {i}: {e}")
                continue

    except Exception as main_e:
        print(f"Error processing main images: {main_e}")

def get_property_info(property_info_div, field_name):
    try:
        dt_element = property_info_div.find_element(By.XPATH, f"//dt[text()='{field_name}']")
        dd_element = dt_element.find_element(By.XPATH, "./following-sibling::dd[1]")
        return dd_element.text
    except Exception:
        return ''

def write_to_csv(listings_data):
    fieldnames = [
        'address', 'property_type', 'price', 'description', 
        'bedrooms_number', 'washrooms_number', 'square_feet', 
        'parking_type', 'ac_type', 'laundry_type', 'heating_type', 'sale_or_rent'
    ]

    with open('listings_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Ensure all dictionaries have the same keys
        for listing in listings_data:
            for field in fieldnames:
                if field not in listing:
                    listing[field] = ''  # Assign a default value if the key is missing

            writer.writerow(listing)

# Download the image from URL
def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"Image downloaded: {save_path}")
    else:
        print(f"Failed to download image: {url}")
