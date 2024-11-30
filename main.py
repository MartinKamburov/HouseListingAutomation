import streamlit as st
import json
import os
from scrape import scrape_website
import time

# Load configuration
CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

# Initialize Streamlit app
st.title("Real Estate Listings Scraper")

# Load existing configuration
config = load_config()

# Display and update base directory
st.subheader("Set Base Directory")
current_base_dir = config.get("base_directory", "")
new_base_dir = st.text_input("Enter Base Directory:", value=current_base_dir)

if st.button("Update Base Directory"):
    sanitized_base_dir = new_base_dir.replace("\\", "/")  # Convert backward slashes to forward slashes
    if os.path.isdir(sanitized_base_dir):
        config["base_directory"] = sanitized_base_dir
        save_config(config)
        st.success(f"Base directory updated to: {sanitized_base_dir}")
    else:
        st.error(f"Invalid directory: {sanitized_base_dir}. Please enter a valid directory path.")

# Input URL for scraping
url = st.text_input("Enter a website URL:")

# Initialize session state for listings_data if not already set
if 'listings_data' not in st.session_state:
    st.session_state.listings_data = []

# Button to scrape the site
if st.button("Scrape Site"):
    print("Wait for 4 seconds")
    time.sleep(4)
    st.write("Scraping the website...")

    # Perform scraping
    listings_data = scrape_website(url)

    print("this is the length of the listings data:")
    print(listings_data)
    
    print("Now going to post the facebook ads")

    # Store the scraped data in session state to retain between re-runs
    if len(listings_data) != 0:
        st.session_state.listings_data = listings_data
        st.write("Scraping completed! Listings data has been saved.")
    else:
        st.write("No data was scraped.")

# JSON input box
# st.write("Alternatively, you can paste JSON data below to use for Facebook posting:")
# json_input = st.text_area("Paste JSON data here:")

# # Button to initiate Facebook posting
# if st.button("Start Facebook Posting"):
#     if json_input:
#         try:
#             # Parse the JSON input
#             listings_data = json.loads(json_input)
#             # Save data to session state to use in posting
#             st.session_state.listings_data = listings_data
#             st.write("JSON data loaded successfully. Starting Facebook posting...")

#             # Start the posting process
#             post_facebook_ads(st.session_state.listings_data)
#             st.write("Facebook posting completed!")
#         except json.JSONDecodeError:
#             st.error("Invalid JSON format. Please correct the JSON data and try again.")
#     elif st.session_state.listings_data:
#         # Use existing scraped data if no JSON is provided
#         st.write("No JSON data provided. Using previously scraped data for Facebook posting...")
#         post_facebook_ads(st.session_state.listings_data)
#         st.write("Facebook posting completed!")
#     else:
#         st.write("No data available. Please either scrape a website or provide JSON data.")
