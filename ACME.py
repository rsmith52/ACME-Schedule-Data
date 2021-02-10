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

schedule_block_length = 0.5 # in hours

#===================================================================
# Constants
#===================================================================

days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
pay_rates = {
    "Pick 1" : 10.25,
    "Student Technical Writer" : 12.75,
    "Student Developer" : 12.75,
    "Student WiscIT Lead" : 13.75,
    "Student Data & Metrics Lead" : 12.75,
    "Level 2 Student Analyst" : 13.75,
    "Student Team Lead" : 13.75
}
pay_raises = {
    "Advanced Phone Agent" : 0.50,
    "Chat/Email" : 0.50,
    "HDQA" : 0.75
}

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
    def Login(self):
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
    def GetScheduleByDate(self, day=None):
        # Default to today
        if day == None:
            day = self.DateToString(date.today())
        
        # Access page for specified date
        new_url = url + '?date=' + day
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

        return { day: df }
    
    # Get Schedule Tables by Month (and year) - MM, YYYY - defaults to this month
    def GetSchedulesByMonth(self, month=None, year=None):
        # Set starting point, defaulting to this month
        if month == None:
            month = date.today().month;
        if year == None:
            year = date.today().year
        num_days = self.DaysInMonth(month, year)
        start = self.StringToDate(str(year) + '-' + str(month) + '-' + str(1))

        # Get all dates in the month
        dates = []
        for i in range(num_days):
            day = start + timedelta(days=i)
            dates.append(day)

        # Get tables for the month
        tables = {}
        for day in tqdm(dates, desc="Scraping data for month: " + str(month) + ", " + str(year)):
            day_str = self.DateToString(day)
            table = self.GetScheduleByDate(day_str)[day_str]
            tables[day_str] = table

        # Return all the tables in order from start of month
        return tables
    
    # Get tables from all dates in range, returns no data if invalid range, end defaults to today
    def GetSchedulesInRange(self, start_date, end_date=None):
        # Get start date
        start = self.StringToDate(start_date)
        
        # Set end of range as today if not given
        if end_date == None:
            end = date.today()
        else:
            end = self.StringToDate(end_date)

        # Get all dates in provided range
        num_days = (end - start).days;
        if (num_days < 0):
            return {}

        # Get all dates in the range
        dates = []
        for i in range(num_days):
            day = start + timedelta(days=i)
            dates.append(day)

        # Get tables for all dates in range
        tables = {}
        for day in tqdm(dates, desc="Scraping data for date range"):
            day_str = self.DateToString(day)
            table = self.GetScheduleByDate(day_str)[day_str]
            tables[day_str] = table

        # Return all the tables in order from start to end
        return tables
    
    # Get tables from n days (defaults to a week)
    def GetRecentSchedules(self, num_days=7):
        # Get last n days
        today = date.today()
        dates = []
        for i in range(num_days):
            day = today - timedelta(days=i)
            dates.append(day)

        # Get tables for last n days
        tables = {}
        for day in tqdm(dates, desc="Scraping data by day"):
            day_str = self.DateToString(day)
            table = self.GetScheduleByDate(day_str)[day_str]
            tables[day_str] = table

        # Return all the tables
        return tables
    
    # Get hours worked by agent in set of tables
    def GetAgentHours(self, tables, most_first=True):
        # Keep track of all agents as they pop up
        agent_hours = {}
        
        # Iterate through all provided data
        for date in tables.keys():
            for col in tables[date]:
                for entry in tables[date][col]:
                    if entry != None:
                        for agent in entry:
                            # Create entry for agent upon first listing
                            if agent not in agent_hours:
                                agent_hours[agent] = 0
                            # Increment by half hour for each entry
                            agent_hours[agent] += schedule_block_length
        
        # Return list sorted by most to least hours
        agent_hours = {k: v for k, v in sorted(agent_hours.items(), key=lambda item: item[1], reverse=most_first)}
        return agent_hours
             
    # Close the browser
    def Close(self):
        self.browser.close()
    
    #===================================================================
    # Utilities
    #===================================================================

    # URL String to Date: String form = date=YYYY-MM-DD
    def StringToDate(self, string):
        parts = string.split('-')
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        date = datetime.date(year=year, month=month, day=day)
        return date

    # Date to URL String: String form = date=YYYY-MM-DD
    def DateToString(self, date):
        year = date.year
        month = date.month
        day = date.day
        return str(year) + '-' + str(month) + '-' + str(day)
    
    # Get days in month (MM, YYYY)
    def DaysInMonth(self, month, year=None):
        month = int(month) - 1
        if (year == None):
            year = int(date.today().year)
        else:
            year = int(year)
        
        # February Leap Year
        if (month == 1 and year % 4 == 0):
            return days_in_months[month] + 1
        else:
            return days_in_months[month]