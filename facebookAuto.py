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

def create_proxy_extension():
    full_proxy_username = f"{proxy_username}-country-{country_code}"
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"76.0.0"
    }
    """
    background_js = string.Template("""
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "${proxy_host}",
                port: parseInt(${proxy_port})
            },
            bypassList: ["localhost"]
        }
    };
    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
    function callbackFn(details) {
        return {
            authCredentials: {
                username: "${proxy_username}",
                password: "${proxy_password}"
            }
        };
    }
    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        {urls: ["<all_urls>"]},
        ['blocking']
    );
    """).substitute(
        proxy_host=proxy_host,
        proxy_port=proxy_port,
        proxy_username=full_proxy_username,
        proxy_password=proxy_password
    )

    plugin_file = 'proxy_auth_plugin.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_file


def slow_typing(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(0.3) 

# Download the image from URL
def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"Image downloaded: {save_path}")
    else:
        print(f"Failed to download image: {url}")

def post_facebook_ads(listings_data):
    print('Connecting to Bright Data Scraping Browser...')

    # Create the proxy extension with Canada as the target
    proxy_extension_file = create_proxy_extension()

    # Initialize ChromeOptions
    options = Options()
    options.add_argument('--ignore-certificate-errors')

    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 2,  # Block location pop-ups
        "profile.default_content_setting_values.notifications": 2  # Block notifications
    })

    # Uncomment if you wish to run Chrome headless
    # options.add_argument('--headless')
    options.add_extension(proxy_extension_file)

    # Initialize the Chrome driver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get('https://www.facebook.com/marketplace/')
        print("Loaded Facebook login page")

        # All for logging bypassing the username and password credential stuff
        #------------------------------------------------------------------------------------------------
        # This is used in case of a cookies pop up
        # try:
        #     # Wait for the cookie consent pop-up to appear and click "Decline optional cookies"
        #     decline_cookies_button = WebDriverWait(driver, 10).until(
        #         EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Decline optional cookies']"))
        #     )
        #     decline_cookies_button.click()
        #     print("Clicked 'Decline optional cookies'.")
        # except Exception as e:
        #     print("Cookie consent pop-up did not appear or was already handled.")

        mainPage = driver.find_element(By.ID, 'facebook')

        time.sleep(2)

        login_form = mainPage.find_element(By.ID, 'login_popup_cta_form')

        time.sleep(2)
        # Proceed with login automation
        email_input = login_form.find_element(By.NAME, 'email')
        email_input.clear()
        slow_typing(email_input, fb_username)

        time.sleep(2)

        password_input = login_form.find_element(By.NAME, 'pass')
        password_input.clear()
        slow_typing(password_input, fb_password)

        time.sleep(2)

        login_button = login_form.find_element(By.XPATH, "//div[@aria-label='Accessible login button']")
        login_button.click()

        # Wait for the page to fully load and confirm login is successful
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@aria-label, 'Your profile')]"))
        )
        print("Logged into Facebook successfully!")
        #------------------------------------------------------------------------------------------------

        # PART 2:  

        for listing in listings_data:

            try:
                # Change the url to create a listing
                driver.get('https://www.facebook.com/marketplace/create/rental/')

                #---------------------

                dropdownSaleOrRent_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Home for Sale or Rent']"))
                )
                dropdownSaleOrRent_button.click()
                print("Property type dropdown clicked to reveal options.")

                time.sleep(2)

                # Get the sale or rent status from the current listing
                property_typeSaleOrRent = listing.get('sale_or_rent', '').lower()
                print("Here is the RENT STATUS!: ", property_typeSaleOrRent)
                time.sleep(2)


                # Dynamically choose the option based on the property_type
                if "rent" in property_typeSaleOrRent or "lease" in property_typeSaleOrRent:
                    print("It got here!")
                    time.sleep(2)

                    try:
                        rent_option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//div[@role='option' and contains(., 'Rent')]"))
                        )
                        ActionChains(driver).move_to_element(rent_option).click().perform()
                        print("Selected 'Rent' from the dropdown.")
                    except Exception as e:
                        print(f"Error selecting 'Rent': {e}")

                    time.sleep(2)

                    #---------------------
                    # Dropdown menus

                    try:
                        dropdownRentalType_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Rental type']"))
                        )
                        dropdownRentalType_button.click()
                        print("Rental type dropdown clicked to reveal options.")
                    except Exception as e:
                        print(f"Error clicking dropdown: {e}")

                    time.sleep(2)

                    # Set the rental type dynamically based on your listing
                    rental_type = listing.get('property_type', '').lower()
                    
                    try:
                        if "apartment" in rental_type:
                            option = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Apartment')]"))
                            )
                            option.click()
                            print("Selected 'Apartment' rental type.")
                        elif "house" in rental_type:
                            option = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'House')]"))
                            )
                            option.click()
                            print("Selected 'House' rental type.")
                        elif "townhouse" in rental_type:
                            option = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Townhouse')]"))
                            )
                            option.click()
                            print("Selected 'Townhouse' rental type.")
                        else:
                            print(f"Rental type '{rental_type}' not recognized.")
                    except Exception as e:
                        print(f"Error selecting rental type '{rental_type}': {e}")

                    time.sleep(2)

                    #---------------------------------------------------------------------
                    # Input boxes
                    # Works finds the proper input box and inputs the value ****Model everyother input box off this one since it works****
                    bedrooms_input = WebDriverWait(driver, 45).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Number of bedrooms']//following::input[@type='text'][1]"))
                    )

                    bedrooms_number = listing.get('bedrooms_number', '').strip()
                    
                    total_bedrooms = ""
                    # Check if it contains a "+" for cases like "1+1"
                    if "+" in bedrooms_number:
                        # Split the parts, convert to integers, and sum them
                        parts = bedrooms_number.split("+")
                        total_bedrooms = sum(int(part.strip()) for part in parts)
                        print(f"Calculated bedrooms (1+1 case): {total_bedrooms}")
                    else:
                        # No "+" sign, just use the number as is
                        total_bedrooms = int(bedrooms_number)
                        print(f"Extracted bedrooms: {total_bedrooms}")

                    # Clear the input field and type the desired value
                    bedrooms_input.clear()
                    slow_typing(bedrooms_input, str(total_bedrooms))  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #---------------------
                    bathroom_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Number of bathrooms']//following::input[@type='text'][1]"))
                    )

                    # Clear the input field and type the desired value
                    bathroom_input.clear()
                    slow_typing(bathroom_input, listing['washrooms_number'])  # Slowly type the number of bathrooms

                    time.sleep(2)
                    #---------------------
                    price_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Price per month']//following::input[@type='text'][1]"))
                    )

                    # Clear the input field and type the desired value
                    price_input.clear()
                    slow_typing(price_input, listing['price'])  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #---------------------
                    # After typing in the property address
                    PropertyAddress_input = WebDriverWait(driver, 10).until( 
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Rental address']//following::input[@type='text'][1]"))
                    )

                    # Clear the input field and type the desired value
                    PropertyAddress_input.clear()
                    slow_typing(PropertyAddress_input, listing['address'])  # Slowly type the address

                    time.sleep(2)

                    # Wait for the first <li> element in the suggestion list to appear and click it
                    try:
                        first_suggestion = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//ul[@role='listbox']//li[1]"))  # Target the first <li> in the <ul>
                        )
                        first_suggestion.click()
                        print("Clicked on the first address suggestion.")
                        time.sleep(2)  # Allow time for the selection to be processed
                    except Exception as e:
                        print(f"Error clicking the first address suggestion: {e}")

                    time.sleep(2)
                    #---------------------
                    property_description_label = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Rental description']"))
                    )
                    
                    # Now find the corresponding textarea within the same container
                    PropertyDescription_input = property_description_label.find_element(By.XPATH, ".//following::textarea[1]")
                    
                    # Clear the existing text and input the new property description
                    PropertyDescription_input.clear()
                    slow_typing(PropertyDescription_input, listing['description'])  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #---------------------
                    PropertySqft_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Property square feet']//following::input[@type='text'][1]"))
                    )

                    # Clear the input field and type the desired value
                    PropertySqft_input.clear()
                    slow_typing(PropertySqft_input, listing['square_feet'])  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #---------------------
                    
                    dropdownLaundryType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Laundry type']"))
                    )
                    dropdownLaundryType_button.click()
                    print("Laundry type dropdown clicked to reveal options.")

                    time.sleep(2)

                    laundry_type = listing.get('laundry_type', '').lower()

                    # Dynamically choose the option based on the laundry_type
                    if "ensuite" in laundry_type.lower() or "in-unit" in laundry_type.lower() or "in-suite" in laundry_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'In-unit laundry')]"))
                        )
                        option.click()
                        print("Selected 'In-unit laundry' from the dropdown.")
                    elif "building" in laundry_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Laundry in building')]"))
                        )
                        option.click()
                        print("Selected 'Laundry in building' from the dropdown.")
                    elif "available" in laundry_type.lower() or "common" in laundry_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Laundry available')]"))
                        )
                        option.click()
                        print("Selected 'Laundry available' from the dropdown.")
                    elif "none" in laundry_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'None')]"))
                        )
                        option.click()
                        print("Selected 'None' from the dropdown.")
                    else:
                        print(f"Laundry type '{laundry_type}' not recognized.")

                    time.sleep(2)

                    #---------------------

                    dropdownParkingType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Parking type']"))
                    )
                    dropdownParkingType_button.click()
                    print("Parking type dropdown clicked to reveal options.")

                    time.sleep(2)

                    # Temporary hardcoded string for testing (replace this with actual data later)
                    parking_type = listing.get('parking_type', '').lower()

                    # Dynamically choose the option based on the parking_type
                    if "underground" in parking_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Garage parking')]"))
                        )
                        option.click()
                        print("Selected 'Garage parking' from the dropdown.")
                    elif "street" in parking_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Street parking')]"))
                        )
                        option.click()
                        print("Selected 'Street parking' from the dropdown.")
                    elif "off-street" in parking_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Off-street parking')]"))
                        )
                        option.click()
                        print("Selected 'Off-street parking' from the dropdown.")
                    elif "available" in parking_type.lower() or "parking available" in parking_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Parking available')]"))
                        )
                        option.click()
                        print("Selected 'Parking available' from the dropdown.")
                    elif "none" in parking_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'None')]"))
                        )
                        option.click()
                        print("Selected 'None' from the dropdown.")
                    else:
                        print(f"Parking type '{parking_type}' not recognized.")

                    time.sleep(2)

                    #---------------------

                    dropdownAcType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Air conditioning type']"))
                    )
                    dropdownAcType_button.click()
                    print("Air conditioning type dropdown clicked to reveal options.")

                    time.sleep(2)

                    # Temporary hardcoded string for testing (replace this with actual data later)
                    ac_type = listing.get('ac_type', '').lower() 

                    # Dynamically choose the option based on the ac_type
                    if "central" in ac_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Central AC')]"))
                        )
                        option.click()
                        print("Selected 'Central AC' from the dropdown.")
                    elif "available" in ac_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'AC available')]"))
                        )
                        option.click()
                        print("Selected 'AC available' from the dropdown.")
                    elif "none" in ac_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'None')]"))
                        )
                        option.click()
                        print("Selected 'None' from the dropdown.")
                    else:
                        print(f"Air conditioning type '{ac_type}' not recognized.")

                    time.sleep(2)

                    #---------------------

                    dropdownHeatingType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Heating type']"))
                    )
                    dropdownHeatingType_button.click()
                    print("Heating type dropdown clicked to reveal options.")

                    time.sleep(2)

                    # Temporary hardcoded string for testing (replace this with actual data later)
                    heating_type = listing.get('heating_type', '').lower()

                    # Dynamically choose the option based on the heating_type
                    if "forced air" in heating_type.lower() or "central" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Central heating')]"))
                        )
                        option.click()
                        print("Selected 'Central heating' from the dropdown.")
                    elif "electric" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Electric heating')]"))
                        )
                        option.click()
                        print("Selected 'Electric heating' from the dropdown.")
                    elif "gas" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Gas heating')]"))
                        )
                        option.click()
                        print("Selected 'Gas heating' from the dropdown.")
                    elif "radiator" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Radiator heating')]"))
                        )
                        option.click()
                        print("Selected 'Radiator heating' from the dropdown.")
                    elif "available" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Heating available')]"))
                        )
                        option.click()
                        print("Selected 'Heating available' from the dropdown.")
                    elif "none" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'None')]"))
                        )
                        option.click()
                        print("Selected 'None' from the dropdown.")
                    else:
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'None')]"))
                        )
                        option.click()
                        print(f"Heating type '{heating_type}' not recognized.")

                    time.sleep(2)

                    #---------------------

                    # cat_friendly = listing.get('cat_friendly', '').lower()

                    # if "yes" in cat_friendly:
                    #     try:
                    #         cat_friendly_switch = WebDriverWait(driver, 10).until(
                    #             EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Cat friendly']"))
                    #         )
                    #         cat_friendly_switch.click()
                    #         print("Cat friendly switch clicked.")
                    #     except Exception as e:
                    #         print(f"Error clicking the Cat friendly switch: {e}")

                    # time.sleep(2)

                    #---------------------
                    
                    #POTENTIALLY ADD A DATE AVAILABLE OPTION!

                    #---------------------

                    # dog_friendly = listing.get('dog_friendly', '').lower()

                    # if "yes" in dog_friendly: 
                    #     try:
                    #         dog_friendly_switch = WebDriverWait(driver, 10).until(
                    #             EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Dog friendly']"))
                    #         )
                    #         dog_friendly_switch.click()
                    #         print("Cat friendly switch clicked.")
                    #     except Exception as e:
                    #         print(f"Error clicking the Cat friendly switch: {e}")

                    # time.sleep(2)

                    #---------------------------------------------------------------------

                elif "sale" in property_typeSaleOrRent:
                    option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'For Sale')]"))
                    )
                    option.click()
                    print("Selected 'For Sale' from the dropdown.")

                    time.sleep(2)

                    #---------------------
                    # Dropdown menus
                    # Wait for the dropdown to be clickable and click it to reveal the options
                    dropdownPType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Property type']"))
                    )
                    dropdownPType_button.click()
                    print("Property type dropdown clicked to reveal options.")

                    time.sleep(2)

                    # Get the property type from the current listing
                    property_type = listing['property_type'].lower()

                    # Dynamically choose the option based on the property_type
                    if "apartment" in property_type or "apt" in property_type:
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Apartment')]"))
                        )
                        option.click()
                        print("Selected 'Apartment' from the dropdown.")
                    elif "townhouse" in property_type:
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Townhouse')]"))
                        )
                        option.click()
                        print("Selected 'Townhouse' from the dropdown.")
                    elif "house" in property_type:
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'House')]"))
                        )
                        option.click()
                        print("Selected 'House' from the dropdown.")
                    else:
                        print(f"Property type '{property_type}' not recognized.")

                    time.sleep(2)

                    #---------------------------------------------------------------------
                    # Input boxes
                    # Works finds the proper input box and inputs the value
                    bedrooms_input = WebDriverWait(driver, 45).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Number of bedrooms']//following::input[@type='text'][1]"))
                    )

                    bedrooms_number = listing.get('bedrooms_number', '').strip()
                    
                    total_bedrooms = ""
                    # Check if it contains a "+" for cases like "1+1"
                    if "+" in bedrooms_number:
                        # Split the parts, convert to integers, and sum them
                        parts = bedrooms_number.split("+")
                        total_bedrooms = sum(int(part.strip()) for part in parts)
                        print(f"Calculated bedrooms (1+1 case): {total_bedrooms}")
                    else:
                        # No "+" sign, just use the number as is
                        total_bedrooms = int(bedrooms_number)
                        print(f"Extracted bedrooms: {total_bedrooms}")

                    # Clear the input field and type the desired value
                    bedrooms_input.clear()
                    slow_typing(bedrooms_input, str(total_bedrooms))  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #---------------------
                    bathroom_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Number of bathrooms']//following::input[@type='text'][1]"))
                    )

                    # Clear the input field and type the desired value
                    bathroom_input.clear()
                    slow_typing(bathroom_input, listing['washrooms_number'])  # Slowly type the number of bathrooms

                    time.sleep(2)
                    #---------------------
                    price_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Price']//following::input[@type='text'][1]"))
                    )

                    # Clear the input field and type the desired value
                    price_input.clear()
                    slow_typing(price_input, listing['price'])  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #---------------------
                    # After typing in the property address
                    PropertyAddress_input = WebDriverWait(driver, 10).until( 
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Property address']//following::input[@type='text'][1]"))
                    )

                    # Clear the input field and type the desired value
                    PropertyAddress_input.clear()
                    slow_typing(PropertyAddress_input, listing['address'])  # Slowly type the address

                    time.sleep(2)

                    # Wait for the first <li> element in the suggestion list to appear and click it
                    try:
                        first_suggestion = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//ul[@role='listbox']//li[1]"))  # Target the first <li> in the <ul>
                        )
                        first_suggestion.click()
                        print("Clicked on the first address suggestion.")
                        time.sleep(2)  # Allow time for the selection to be processed
                    except Exception as e:
                        print(f"Error clicking the first address suggestion: {e}")

                    time.sleep(2)

                    #---------------------
                    PropertySqft_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Property square feet']//following::input[@type='text'][1]"))
                    )

                    # Clear the input field and type the desired value
                    PropertySqft_input.clear()
                    slow_typing(PropertySqft_input, listing['square_feet'])  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #---------------------
                    property_description_label = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Property description']"))
                    )
                    
                    # Now find the corresponding textarea within the same container
                    PropertyDescription_input = property_description_label.find_element(By.XPATH, ".//following::textarea[1]")
                    
                    # Clear the existing text and input the new property description
                    PropertyDescription_input.clear()
                    slow_typing(PropertyDescription_input, listing['description'])  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #---------------------

                    dropdownLaundryType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Laundry type']"))
                    )
                    dropdownLaundryType_button.click()
                    print("Laundry type dropdown clicked to reveal options.")

                    time.sleep(2)

                    laundry_type = listing.get('laundry_type', '').lower()

                    # Dynamically choose the option based on the laundry_type
                    if "ensuite" in laundry_type.lower() or "in-unit" in laundry_type.lower() or "in-suite" in laundry_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'In-unit laundry')]"))
                        )
                        option.click()
                        print("Selected 'In-unit laundry' from the dropdown.")
                    elif "building" in laundry_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Laundry in building')]"))
                        )
                        option.click()
                        print("Selected 'Laundry in building' from the dropdown.")
                    elif "available" in laundry_type.lower() or "common" in laundry_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Laundry available')]"))
                        )
                        option.click()
                        print("Selected 'Laundry available' from the dropdown.")
                    elif "none" in laundry_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'None')]"))
                        )
                        option.click()
                        print("Selected 'None' from the dropdown.")
                    else:
                        print(f"Laundry type '{laundry_type}' not recognized.")

                    time.sleep(2)

                    #---------------------

                    dropdownParkingType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Parking type']"))
                    )
                    dropdownParkingType_button.click()
                    print("Parking type dropdown clicked to reveal options.")

                    time.sleep(2)

                    # Temporary hardcoded string for testing (replace this with actual data later)
                    parking_type = listing.get('parking_type', '').lower()

                    # Dynamically choose the option based on the parking_type
                    if "underground" in parking_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Garage parking')]"))
                        )
                        option.click()
                        print("Selected 'Garage parking' from the dropdown.")
                    elif "street" in parking_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Street parking')]"))
                        )
                        option.click()
                        print("Selected 'Street parking' from the dropdown.")
                    elif "off-street" in parking_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Off-street parking')]"))
                        )
                        option.click()
                        print("Selected 'Off-street parking' from the dropdown.")
                    elif "available" in parking_type.lower() or "parking available" in parking_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Parking available')]"))
                        )
                        option.click()
                        print("Selected 'Parking available' from the dropdown.")
                    elif "none" in parking_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'None')]"))
                        )
                        option.click()
                        print("Selected 'None' from the dropdown.")
                    else:
                        print(f"Parking type '{parking_type}' not recognized.")

                    time.sleep(2)

                    #---------------------

                    dropdownAcType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Air conditioning type']"))
                    )
                    dropdownAcType_button.click()
                    print("Air conditioning type dropdown clicked to reveal options.")

                    time.sleep(2)

                    # Temporary hardcoded string for testing (replace this with actual data later)
                    ac_type = listing.get('ac_type', '').lower() 

                    # Dynamically choose the option based on the ac_type
                    if "central" in ac_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Central AC')]"))
                        )
                        option.click()
                        print("Selected 'Central AC' from the dropdown.")
                    elif "available" in ac_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'AC available')]"))
                        )
                        option.click()
                        print("Selected 'AC available' from the dropdown.")
                    elif "none" in ac_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'None')]"))
                        )
                        option.click()
                        print("Selected 'None' from the dropdown.")
                    else:
                        print(f"Air conditioning type '{ac_type}' not recognized.")

                    time.sleep(2)

                    #---------------------

                    dropdownHeatingType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Heating type']"))
                    )
                    dropdownHeatingType_button.click()
                    print("Heating type dropdown clicked to reveal options.")

                    time.sleep(2)

                    # Temporary hardcoded string for testing (replace this with actual data later)
                    heating_type = listing.get('heating_type', '').lower()

                    # Dynamically choose the option based on the heating_type
                    if "forced air" in heating_type.lower() or "central" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Central heating')]"))
                        )
                        option.click()
                        print("Selected 'Central heating' from the dropdown.")
                    elif "electric" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Electric heating')]"))
                        )
                        option.click()
                        print("Selected 'Electric heating' from the dropdown.")
                    elif "gas" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Gas heating')]"))
                        )
                        option.click()
                        print("Selected 'Gas heating' from the dropdown.")
                    elif "radiator" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Radiator heating')]"))
                        )
                        option.click()
                        print("Selected 'Radiator heating' from the dropdown.")
                    elif "available" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Heating available')]"))
                        )
                        option.click()
                        print("Selected 'Heating available' from the dropdown.")
                    elif "none" in heating_type.lower():
                        option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'None')]"))
                        )
                        option.click()
                        print("Selected 'None' from the dropdown.")
                    else:
                        print(f"Heating type '{heating_type}' not recognized.")

                    time.sleep(2)

                    #---------------------------------------------------------------------

                else:
                    print(f"Property type '{property_typeSaleOrRent}' not recognized.")


                # Upload picture stuff here:
                #---------------------------------------------------------------------
                # Step 1: Find the directory that matches the current property's address and upload the images from that directory.
                safe_addressForDir = listing['address'].replace(',', '').strip()
                
                base_dir = os.path.join(base_dir_path, safe_addressForDir)

                if not os.path.exists(base_dir):
                    print(f"Directory for {listing['address']} does not exist, skipping image upload.")
                else:
                    print(f"Found directory for {listing['address']} at {base_dir}.")

                    # Get the list of image files in the directory
                    image_files = [os.path.join(base_dir, file) for file in os.listdir(base_dir) if file.endswith(('.jpg', '.jpeg', '.png'))]
                    
                    if not image_files:
                        print(f"No images found in the directory {base_dir}.")
                    else:
                        print(f"Found {len(image_files)} image(s) in the directory.")

                        # Step 2: Locate the hidden file input element and upload the files
                        file_input = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                        )

                        # Join the file paths with a newline character to handle multiple files
                        file_input.send_keys("\n".join(image_files))

                        print(f"Image(s) from {base_dir} uploaded successfully.")
                #---------------------------------------------------------------------

                time.sleep(5)

                # Click of the Next button:
                #---------------------------------------------------------------------
                try:
                    # Wait for the Next button to be clickable and click it
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Next' and @role='button']"))
                    )
                    next_button.click()
                    print("Clicked the Next button.")
                except Exception as e:
                    print(f"Error occurred while clicking the 'Next' button: {e}")
                #---------------------------------------------------------------------

                time.sleep(4)

                # Publish button clicking
                #---------------------------------------------------------------------
                try:
                    # Wait for the Publish button to be clickable and click it
                    publish_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Publish' and @role='button']"))
                    )
                    publish_button.click()
                    print("Clicked the Publish button.")
                except Exception as e:
                    print(f"Error occurred while clicking the 'Publish' button: {e}")
                #---------------------------------------------------------------------

            except Exception as e:
                print(f"Error processing listing {listing['address']}: {e}")

    except Exception as e:
        print(f"Error occurred while logging into Facebook or navigating: {e}")

    finally:
        driver.quit()
        print("The driver quit")