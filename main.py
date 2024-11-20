import streamlit as st
import json
from scrape import scrape_website, post_facebook_ads
import time

st.title("Real Estate Listings Scraper and Facebook Poster")

# Input URL for scraping
url = st.text_input("Enter a website URL to scrape:")

# Initialize session state for listings_data if not already set
if 'listings_data' not in st.session_state:
    st.session_state.listings_data = []

# Button to scrape the site
if st.button("Scrape Site"):
    st.write("Scraping the website...")
    time.sleep(4)

    # Perform scraping
    listings_data = scrape_website(url)

    # Store the scraped data in session state to retain between re-runs
    if listings_data:
        st.session_state.listings_data = listings_data
        st.write("Scraping completed! Listings data has been saved.")
    else:
        st.write("No data was scraped.")

# Divider line
st.markdown("---")

# JSON input box
st.write("Alternatively, you can paste JSON data below to use for Facebook posting:")
json_input = st.text_area("Paste JSON data here:")

# Button to initiate Facebook posting
if st.button("Start Facebook Posting"):
    if json_input:
        try:
            # Parse the JSON input
            listings_data = json.loads(json_input)
            # Save data to session state to use in posting
            st.session_state.listings_data = listings_data
            st.write("JSON data loaded successfully. Starting Facebook posting...")

            # Start the posting process
            post_facebook_ads(st.session_state.listings_data)
            st.write("Facebook posting completed!")
        except json.JSONDecodeError:
            st.error("Invalid JSON format. Please correct the JSON data and try again.")
    elif st.session_state.listings_data:
        # Use existing scraped data if no JSON is provided
        st.write("No JSON data provided. Using previously scraped data for Facebook posting...")
        post_facebook_ads(st.session_state.listings_data)
        st.write("Facebook posting completed!")
    else:
        st.write("No data available. Please either scrape a website or provide JSON data.")
