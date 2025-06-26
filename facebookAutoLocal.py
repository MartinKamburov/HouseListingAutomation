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

skipped_file = 'skipped_listings.csv'

# ─── Clear out the old skipped listings (or create the file) ──────────
with open(skipped_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['address'])

def slow_typing(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(0.3) 

def fast_typing(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(0.1) 

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
    print('Connecting to local scraping browser...')

    # Initialize ChromeOptions
    options = Options()
    options.add_argument('--ignore-certificate-errors')

    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 2,  # Block location pop-ups
        "profile.default_content_setting_values.notifications": 2  # Block notifications
    })

    # Uncomment if you wish to run Chrome headless
    # options.add_argument('--headless')

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

        # ── 2. Click the correct “Log In” button (popup OR full page) ─────────────
        login_button = login_form.find_element(
                                    By.XPATH,
                                    ".//div[@role='button' and @aria-label='Log in to Facebook']"
                                    #   └──── inside login_form only (note the dot at the start)
                                )
        
        login_button.click()

        print("Logged into Facebook successfully!")
        input("The program will resume only after you have solved the captcha. Enter something when done: ")
        #------------------------------------------------------------------------------------------------

        # PART 2:  

        for listing in listings_data:

            try:
                # Change the url to create a listing

                driver.get('https://www.facebook.com/marketplace/create/rental/')

                time.sleep(2)

                #-------------------------------------------------------------------------------------------------

                dropdownSaleOrRent_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//label[@role='combobox' and .//span[text()='Home for Sale or Rent']]"
                    ))
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

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    # Dropdown menus

                    try:
                        dropdownRentalType_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH,
                                "//label[@role='combobox' and .//span[text()='Rental type']]"
                            ))
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

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    # Input boxes
                    # Works finds the proper input box and inputs the value ****Model every other input box off this one since it works****
                    bedrooms_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[.//span[normalize-space(text())='Number of bedrooms']]//input[@type='text']"
                        ))
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
                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    bathroom_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[.//span[normalize-space(text())='Number of bathrooms']]//input[@type='text']"
                        ))
                    )

                    # Clear the input field and type the desired value
                    bathroom_input.clear()
                    slow_typing(bathroom_input, listing['washrooms_number'])  # Slowly type the number of bathrooms

                    time.sleep(2)
                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    price_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[.//span[normalize-space(text())='Price per month']]//input[@type='text']"
                        ))
                    )

                    # Clear the input field and type the desired value
                    price_input.clear()
                    slow_typing(price_input, listing['price'])  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    # After typing in the property address

                    PropertyAddress_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR,
                            "input[aria-autocomplete='list'][type='text']"
                        ))
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

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    property_description_label = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[.//span[normalize-space(text())='Rental description']]//textarea"
                        ))
                    )

                    driver.execute_script("arguments[0].scrollIntoView(true);", property_description_label)
                    
                    # Clear the existing text and input the new property description
                    property_description_label.clear()
                    fast_typing(property_description_label, listing['description'])  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    PropertySqft_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[.//span[normalize-space(text())='Property square feet']]//input[@type='text']"
                        ))
                    )

                    # Clear the input field and type the desired value
                    PropertySqft_input.clear()
                    slow_typing(PropertySqft_input, listing['square_feet'])  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    
                    dropdownLaundryType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[@role='combobox' and .//span[text()='Laundry type']]"
                        ))
                    )
                    dropdownLaundryType_button.click()

                    laundry_type = listing.get('laundry_type', '').lower()
                    laundryChoice = ""

                    if "ensuite" in laundry_type or "in-suite" in laundry_type or "in-unit" in laundry_type:
                        laundryChoice = "In-unit laundry"
                    elif "area" in laundry_type:
                        laundryChoice = "Laundry available"
                    elif "building" in laundry_type:
                        laundryChoice = "Laundry in building"
                    elif "none" in laundry_type:
                        laundryChoice = "None"
                    else:
                        laundryChoice = ""

                    if laundryChoice:
                        optionLaundry = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH,
                                f"//span[normalize-space(text())='{laundryChoice}']"
                            ))
                        )
                        optionLaundry.click()
                        print(f"Selected '{laundryChoice}' for laundry_type='{listing['laundry_type']}'")

                    time.sleep(2)

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------

                    dropdownParkingType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[@role='combobox' and .//span[text()='Parking type']]"
                        ))
                    )
                    dropdownParkingType_button.click()

                    parking_type = listing.get('parking_type', '').lower()
                    parkingChoice = ""

                    if "underground" in parking_type or "built-in" in parking_type or "built in" in parking_type or "built" in parking_type:
                        parkingChoice = "Garage parking"
                    elif "street" in parking_type:
                        parkingChoice = "Street parking"
                    elif "off-street" in parking_type or "off street" in parking_type:
                        parkingChoice = "Off-street parking"
                    elif "available" in parking_type:
                        parkingChoice = "Parking available"
                    elif "none" in parking_type:
                        parkingChoice = "None"
                    else:
                        parkingChoice = ""

                    if parkingChoice:
                        optionParking = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH,
                                f"//span[normalize-space(text())='{parkingChoice}']"
                            ))
                        )
                        optionParking.click()
                        print(f"Selected '{parkingChoice}' for parking_type='{listing['parking_type']}'")

                    time.sleep(2)

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------

                    dropdownAcType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[@role='combobox' and .//span[text()='Air conditioning type']]"
                        ))
                    )
                    dropdownAcType_button.click()
                    print("Air conditioning dropdown clicked to reveal options.")

                    # 2) normalize the source field
                    ac_type = listing.get('ac_type', '').lower()
                    acChoice = ""

                    # 3) map your raw JSON values into Facebook’s UI options
                    if "central" in ac_type:
                        acChoice = "Central AC"
                    elif "available" in ac_type:
                        acChoice = "AC available"
                    elif "none" in ac_type:
                        acChoice = "None"
                    else:
                        acChoice = ""  # no selection if unrecognized

                    # 4) click the matching option (if we found one)
                    if acChoice:
                        optionAc = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH,
                                f"//span[normalize-space(text())='{acChoice}']"
                            ))
                        )
                        optionAc.click()
                        print(f"Selected '{acChoice}' for ac_type='{listing.get('ac_type', '')}'")

                    time.sleep(2)

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------

                    dropdownHeatingType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[@role='combobox' and .//span[text()='Heating type']]"
                        ))
                    )
                    dropdownHeatingType_button.click()
                    print("Heating type dropdown clicked to reveal options.")

                    # 2) normalize the source field
                    heating_type = listing.get('heating_type', '').lower()
                    heatingChoice = ""

                    # 3) map your JSON values into FB’s UI options
                    if "forced air" in heating_type or "central" in heating_type:
                        heatingChoice = "Central heating"
                    elif "electric" in heating_type:
                        heatingChoice = "Electric heating"
                    elif "gas" in heating_type:
                        heatingChoice = "Gas heating"
                    elif "radiator" in heating_type:
                        heatingChoice = "Radiator heating"
                    elif "available" in heating_type:
                        heatingChoice = "Heating available"
                    elif "none" in heating_type:
                        heatingChoice = "None"
                    else:
                        heatingChoice = ""

                    # 4) click the matching option (if we found one)
                    if heatingChoice:
                        optionHeating = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH,
                                f"//span[normalize-space(text())='{heatingChoice}']"
                            ))
                        )
                        optionHeating.click()
                        print(f"Selected '{heatingChoice}' for heating_type='{listing['heating_type']}'")

                    time.sleep(2)

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------

                elif "sale" in property_typeSaleOrRent:
                    option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@role='option' and contains(., 'For Sale')]"))
                    )
                    option.click()
                    print("Selected 'For Sale' from the dropdown.")

                    time.sleep(2)

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    # Dropdown menus
                    # Wait for the dropdown to be clickable and click it to reveal the options
                    dropdownPType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[@role='combobox' and .//span[text()='Property type']]"
                        ))
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

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    # Input boxes
                    # Works finds the proper input box and inputs the value
                    bedrooms_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[.//span[normalize-space(text())='Number of bedrooms']]//input[@type='text']"
                        ))
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
                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    bathroom_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[.//span[normalize-space(text())='Number of bathrooms']]//input[@type='text']"
                        ))
                    )

                    # Clear the input field and type the desired value
                    bathroom_input.clear()
                    slow_typing(bathroom_input, listing['washrooms_number'])  # Slowly type the number of bathrooms

                    time.sleep(2)
                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    price_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[.//span[normalize-space(text())='Price']]//input[@type='text']"
                        ))
                    )

                    # Clear the input field and type the desired value
                    price_input.clear()
                    slow_typing(price_input, listing['price'])  # Slowly type the number of bedrooms

                    time.sleep(2)
                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    # After typing in the property address
                    PropertyAddress_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR,
                            "input[aria-autocomplete='list'][type='text']"
                        ))
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

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    property_description_label = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[.//span[normalize-space(text())='Rental description']]//textarea"
                        ))
                    )
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", property_description_label)
                    # Clear the existing text and input the new property description
                    property_description_label.clear()
                    fast_typing(property_description_label, listing['description'])

                    time.sleep(2)
                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------
                    PropertySqft_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//label[@aria-label='Property square feet']//following::input[@type='text'][1]"))
                    )

                    # Clear the input field and type the desired value
                    PropertySqft_input.clear()
                    slow_typing(PropertySqft_input, listing['square_feet'])

                    time.sleep(2)
                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------

                    dropdownLaundryType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[@role='combobox' and .//span[text()='Laundry type']]"
                        ))
                    )
                    dropdownLaundryType_button.click()

                    laundry_type = listing.get('laundry_type', '').lower()
                    laundryChoice = ""

                    if "ensuite" in laundry_type or "in-suite" in laundry_type or "in-unit" in laundry_type:
                        laundryChoice = "In-unit laundry"
                    elif "area" in laundry_type:
                        laundryChoice = "Laundry available"
                    elif "building" in laundry_type:
                        laundryChoice = "Laundry in building"
                    elif "none" in laundry_type:
                        laundryChoice = "None"
                    else:
                        laundryChoice = ""

                    if laundryChoice != "":
                        optionLaundry = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH,
                                f"//span[normalize-space(text())='{laundryChoice}']"
                            ))
                        )
                        optionLaundry.click()
                        print(f"Selected '{laundryChoice}' for laundry_type='{listing['laundry_type']}'")
                    
                    time.sleep(2)

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------

                    dropdownParkingType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[@role='combobox' and .//span[text()='Parking type']]"
                        ))
                    )
                    dropdownParkingType_button.click()

                    parking_type = listing.get('parking_type', '').lower()
                    parkingChoice = ""

                    if "underground" in parking_type or "built-in" in parking_type or "built in" in parking_type or "built" in parking_type:
                        parkingChoice = "Garage parking"
                    elif "street" in parking_type:
                        parkingChoice = "Street parking"
                    elif "off-street" in parking_type or "off street" in parking_type:
                        parkingChoice = "Off-street parking"
                    elif "available" in parking_type:
                        parkingChoice = "Parking available"
                    elif "none" in parking_type:
                        parkingChoice = "None"
                    else:
                        parkingChoice = ""

                    if parkingChoice:
                        optionParking = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH,
                                f"//span[normalize-space(text())='{parkingChoice}']"
                            ))
                        )
                        optionParking.click()
                        print(f"Selected '{parkingChoice}' for parking_type='{listing['parking_type']}'")
                    
                    time.sleep(2)

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------

                    dropdownAcType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[@role='combobox' and .//span[text()='Air conditioning type']]"
                        ))
                    )
                    dropdownAcType_button.click()
                    print("Air conditioning dropdown clicked to reveal options.")

                    # 2) normalize the source field
                    ac_type = listing.get('ac_type', '').lower()
                    acChoice = ""

                    # 3) map your raw JSON values into Facebook’s UI options
                    if "central" in ac_type:
                        acChoice = "Central AC"
                    elif "available" in ac_type:
                        acChoice = "AC available"
                    elif "none" in ac_type:
                        acChoice = "None"
                    else:
                        acChoice = ""  # no selection if unrecognized

                    # 4) click the matching option (if we found one)
                    if acChoice:
                        optionAc = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH,
                                f"//span[normalize-space(text())='{acChoice}']"
                            ))
                        )
                        optionAc.click()
                        print(f"Selected '{acChoice}' for ac_type='{listing.get('ac_type', '')}'")

                    time.sleep(2)

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------

                    dropdownHeatingType_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//label[@role='combobox' and .//span[text()='Heating type']]"
                        ))
                    )
                    dropdownHeatingType_button.click()
                    print("Heating type dropdown clicked to reveal options.")

                    # 2) normalize the source field
                    heating_type = listing.get('heating_type', '').lower()
                    heatingChoice = ""

                    # 3) map your JSON values into FB’s UI options
                    if "forced air" in heating_type or "central" in heating_type:
                        heatingChoice = "Central heating"
                    elif "electric" in heating_type:
                        heatingChoice = "Electric heating"
                    elif "gas" in heating_type:
                        heatingChoice = "Gas heating"
                    elif "radiator" in heating_type:
                        heatingChoice = "Radiator heating"
                    elif "available" in heating_type:
                        heatingChoice = "Heating available"
                    elif "none" in heating_type:
                        heatingChoice = "None"
                    else:
                        heatingChoice = ""

                    # 4) click the matching option (if we found one)
                    if heatingChoice:
                        optionHeating = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH,
                                f"//span[normalize-space(text())='{heatingChoice}']"
                            ))
                        )
                        optionHeating.click()
                        print(f"Selected '{heatingChoice}' for heating_type='{listing['heating_type']}'")

                    time.sleep(2)

                    #-------------------------------------------------------------------------------------------------
                    #-------------------------------------------------------------------------------------------------

                else:
                    print(f"Property type '{property_typeSaleOrRent}' not recognized.")


                # Upload picture stuff here:
                #-------------------------------------------------------------------------------------------------
                #-------------------------------------------------------------------------------------------------
                
                # script_dir    = os.path.dirname(os.path.abspath(__file__))
                # Assume TestingPutImages is a sibling directory
                # base_dir_path = os.path.join(script_dir, "TestingPutImages")

                print(f"Looking for images under: {base_dir_path}")

                if not os.path.isdir(base_dir_path):
                    print(f"❌ Base images directory not found: {base_dir_path}")
                else:
                    print(f"✅ Found base images directory: {base_dir_path}")

                    # find the subfolder that matches the street
                    candidates = os.listdir(base_dir_path)
                    street     = listing['address'].split(',')[0].strip().lower()
                    match      = next((d for d in candidates if d.lower().startswith(street)), None)

                    if not match:
                        print(f"❌ No folder matching '{street}' found. Skipping image upload.")
                    else:
                        base_dir = os.path.join(base_dir_path, match)
                        print(f"✅ Found directory for {listing['address']}: {base_dir}")

                        image_files = [
                            os.path.join(base_dir, f)
                            for f in os.listdir(base_dir)
                            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
                        ]
                        if not image_files:
                            print(f"❌ No images found in {base_dir}.")
                            # record the skip
                            with open(skipped_file, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow([ listing['address'] ])
                            continue  # go to next listing

                        else:
                            print(f"Found {len(image_files)} image(s) in {base_dir} — uploading now…")

                            # Reveal & grab the real <input type="file">
                            file_input = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH,
                                    "//input[@type='file' and contains(@accept,'image') and @multiple]"
                                ))
                            )
                            driver.execute_script(
                                "arguments[0].style.display='block';"
                                "arguments[0].style.opacity=1;"
                                "arguments[0].style.transform='none';",
                                file_input
                            )
                            driver.execute_script("arguments[0].scrollIntoView(true);", file_input)

                            # send all your file paths
                            file_input.send_keys("\n".join(image_files))
                            print(f"📸 Uploaded {len(image_files)} image(s) for {listing['address']}")
                #-------------------------------------------------------------------------------------------------
                #-------------------------------------------------------------------------------------------------

                time.sleep(10)

                # Click of the Next button:
                #-------------------------------------------------------------------------------------------------
                #-------------------------------------------------------------------------------------------------
                try:
                    # Wait for the Next button to be clickable and click it
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Next' and @role='button']"))
                    )
                    next_button.click()
                    print("Clicked the Next button.")
                except Exception as e:
                    print(f"Error occurred while clicking the 'Next' button: {e}")
                #-------------------------------------------------------------------------------------------------
                #-------------------------------------------------------------------------------------------------

                time.sleep(5)

                # Publish button clicking
                #-------------------------------------------------------------------------------------------------
                #-------------------------------------------------------------------------------------------------
                try:
                    # Wait for the Publish button to be clickable and click it
                    publish_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Publish' and @role='button']"))
                    )
                    publish_button.click()
                    print("Clicked the Publish button.")
                except Exception as e:
                    print(f"Error occurred while clicking the 'Publish' button: {e}")

                # Takes about 20-30 seconds to publish the listing so potentially add a time.sleep here
                time.sleep(30)
                #-------------------------------------------------------------------------------------------------
                #-------------------------------------------------------------------------------------------------

            except Exception as e:
                print(f"Error processing listing {listing['address']}: {e}")

    except Exception as e:
        print(f"Error occurred while logging into Facebook or navigating: {e}")

    finally:
        driver.quit()
        print("The driver quit")


# ----------------------------------------------------------------------
#   EXTRA FUNCTIONS
#
# ----------------------------------------------------------------------

# def fb_login(driver, fb_username: str, fb_password: str, timeout: int = 20):
#     """
#     Log into Facebook via the dedicated login page.
#     Raises TimeoutException if login fails within *timeout* seconds.
#     """

#     driver.get("https://www.facebook.com/login.php")
#     print("Opened dedicated Facebook login page")

#     wait = WebDriverWait(driver, timeout)

#     # ── Email / phone box ────────────────────────────────────────────────────
#     email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
#     email_input.clear()
#     slow_typing(email_input, fb_username)

#     # ── Password box ────────────────────────────────────────────────────────
#     password_input = wait.until(EC.presence_of_element_located((By.NAME, "pass")))
#     password_input.clear()
#     slow_typing(password_input, fb_password)

#     # ── Click the blue Log In button ────────────────────────────────────────
#     login_button = wait.until(
#         EC.element_to_be_clickable(
#             (By.XPATH, "//button[@name='login' or @id='loginbutton']")
#         )
#     )
#     login_button.click()

#     print("Logged into Facebook successfully")