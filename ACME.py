#===================================================================
# Imports
#===================================================================

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# Data Handling Imports
import numpy as np
import pandas as pd

# Datetime Imports
import datetime
from datetime import date, timedelta

# Utility Imports
from tqdm import tqdm

#===================================================================
# Settings
#===================================================================
    
url = "https://acme.wisc.edu/tools/schedule/schedule.php"
login_secret = "login.secret"

#===================================================================
# ACME Class
#===================================================================

class ACME:
    
    #===================================================================
    # Setup
    #===================================================================
    
    def __init__(self, headless = False):
        # Set Mode
        self.options = Options()
        self.options.headless = headless
        
        # Get Secrets
        with open(login_secret) as f:
            self.user = f.readline()[:-1]
            self.password = f.readline()
    
    # Login to ACME
    def login(self):
        browser = webdriver.Chrome(options=self.options)
        browser.get(url)

        # Fill in username
        user_field = browser.find_element_by_id('j_username')
        user_field.send_keys(self.user)

        # Fill in password
        pass_field = browser.find_element_by_id('j_password')
        pass_field.send_keys(self.password)

        # Click login
        login_button = browser.find_element_by_name('_eventId_proceed')
        login_button.click()

        # Return ACME pointed browser
        self.browser = browser
        return self.browser
    
    #===================================================================
    # ACME Functionality
    #===================================================================
    
    # Get Schedule Table by Date (as string)
    def get_schedule_by_date(self, date):
        # Access page for specified date
        new_url = url + '?date=' + date
        browser = self.browser
        browser.get(new_url)

        # Get table headers
        header_html = browser.find_element_by_xpath("//thead[1]/tr").get_attribute('innerHTML')
        headers = []
        header_text = header_html.split(" ")
        for line in header_text:
            if line.startswith('id='):
                parts = line.split('"')
                header = parts[1]
                parts = header.split('_')
                headers.append(parts[1])
        headers.append("total")

        # Get table
        table = browser.find_element_by_id('sch_table_verticle')
        table_html = table.get_attribute('outerHTML')
        df = pd.read_html(table_html)[0]
        df.drop(df.tail(2).index,inplace=True)

        # Set headers of dataframe
        columns = df.columns
        new_names = {}
        for i in range(len(columns)):
            new_names[columns[i]] = headers[i]
        df = df.rename(columns=new_names)
        df = df.set_index('time')
        df = df.drop(columns=['total'])

        # Split up agents
        for col in df:
            data = df[col]
            new_data = []
            for row in data:
                if type(row) != str:
                    new_data.append(None)
                else:
                    agents = [row[i:i+4] for i in range(0, len(row), 4)]
                    new_data.append(agents)
            df[col] = new_data

        return df
    
    # Get tables from last month
    def get_tables_last_n_days(self, num_days=30):
        # Get last n days
        today = date.today()
        dates = []
        for i in range(num_days):
            day = today - timedelta(days=i)
            dates.append(day)

        # Get tables for last n days
        tables = {}
        for day in tqdm(dates, desc="Scraping data by day"):
            day_str = self.date_to_string(day)
            table = self.get_schedule_by_date(day_str)
            tables[day_str] = table

        # Return all the tables
        return tables         
             
             
    # Close the browser
    def close(self):
        self.browser.close()
    
    #===================================================================
    # Utilities
    #===================================================================
    
    # Date conversion functions
    # String form = date=YYYY-MM-DD

    # URL String to Date
    def string_to_date(self, string):
        parts = string.split('-')
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        date = datetime.date(year=year, month=month, day=day)
        return date

    # Date to URL String
    def date_to_string(self, date):
        year = date.year
        month = date.month
        day = date.day
        return str(year) + '-' + str(month) + '-' + str(day)