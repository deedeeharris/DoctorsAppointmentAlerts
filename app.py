import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import asyncio
import nest_asyncio
from pyppeteer import launch

# Function to strip unnecessary parts of the URL
def strip_url(url):
    # Find the index of 'PageNumber'
    index = url.find('&PageNumber=')
    if index != -1:
        return url[:index+len('&PageNumber=')]
    return url

# Function to scrape HTML content
async def get_html(url):
    browser = await launch(headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    await page.goto(url)
    
    # Wait for the text 'ד"ר ' to appear
    await page.waitForXPath("//*[contains(text(), 'ד\"ר ')]")
    
    html = await page.content()
    await browser.close()
    return html

# Function to extract appointment information from HTML content
def extract_appointment_info(html_content):
    # Initialize lists to store extracted data
    doctors = []
    specialties = []
    areas = []
    appointment_links = []
    addresses = []
    office_appointment_dates = []
    phone_appointment_dates = []

    # Create BeautifulSoup object
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all appointment divs
    appointment_divs = soup.find_all('div', class_='docResualtWrap col-md-12')

    # Loop through each appointment div
    for div in appointment_divs:
        # Extract doctor's name and specialty
        title_list = div.find('div', class_='docResualtTitleList')
        doctor_name = title_list.find('a', class_='docPropTitle').text.strip()

        # Extract doctor's area
        area_div = div.find('div', class_='sectionDoc docPropSubTitle')
        area = area_div.find('li').text.strip()

        # Extract appointment link
        appointment_link = "https://serguide.maccabi4u.co.il/" + title_list.find('a')['href']

        # Find the text "כתובת" and extract the address
        address_text = div.find(text='כתובת')
        if address_text:
            address = address_text.find_next('div').text.strip()
        else:
            address = 'Address not found'

        # Find the image with alt text "במרפאה:"
        office_date_img = div.find('img', alt='במרפאה:')
        if office_date_img:
            # Extract the following div containing the office appointment date
            office_date_div = office_date_img.find_next('div', class_='contactDetailsAns flx-row')
            if office_date_div:
                office_date = office_date_div.text.strip()
            else:
                office_date = 'None'
        else:
            office_date = 'None'

        # Find the image with alt text "מרחוק:"
        phone_date_img = div.find('img', alt='מרחוק:')
        if phone_date_img:
            # Extract the following div containing the phone appointment date
            phone_date_div = phone_date_img.find_next('div', class_='contactDetailsAns flx-row')
            if phone_date_div:
                phone_date = phone_date_div.text.strip()
            else:
                phone_date = 'None'
        else:
            phone_date = 'None'

        # Append extracted data to lists
        doctors.append(doctor_name)
        areas.append(area)
        appointment_links.append(appointment_link)
        addresses.append(address)
        office_appointment_dates.append(office_date)
        phone_appointment_dates.append(phone_date)

    # Create DataFrame from extracted data
    df = pd.DataFrame({
        'Doctor': doctors,
        'Area': areas,
        'Appointment_Link': appointment_links,
        'Address': addresses,
        'Office_Appointment_Date': office_appointment_dates,
        'Phone_Appointment_Date': phone_appointment_dates
    })


    return df

# Function to run the scraping and extraction process
def scrape_and_extract(url):
    url = strip_url(url)
    nest_asyncio.apply()
    dfs = []
    for i in range(1, 4):
        page_url = f'{url}{i}'
        html = asyncio.get_event_loop().run_until_complete(get_html(page_url))
        df = extract_appointment_info(html)
        dfs.append(df)
    result_df = pd.concat(dfs, ignore_index=True)
    return result_df

# Streamlit app
def main():
    st.title('Maccabi Appointment Scraper')
    st.write("Enter the URL (up to 'PageNumber'):")
    url = st.text_input('URL')

    if st.button('Scrape and Analyze'):
        if url:
            df = scrape_and_extract(url)
            st.dataframe(df)
        else:
            st.write("Please enter a valid URL.")

if __name__ == "__main__":
    main()
