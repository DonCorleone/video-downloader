import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from pymongo import MongoClient
import dateparser
from datetime import datetime

# Get the URL
url = os.environ.get('URL')

# Use the URL
k = requests.get(url).text

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'}
soup=BeautifulSoup(k,'html.parser')
# Find all div tags with class gridrow
gridrows = soup.find_all('div', class_='gridrow')

current_date = None
found_event = False

# Store the data in a database
client = MongoClient(os.environ.get('DB_URL'))
db = client['puppet_theater']
collection = db['events']

# For each gridrow
for gridrow in gridrows:
    # Find the event-datum
    event_datum = gridrow.find('div', class_='gridcolumn small-12 large-12 event-datum')

    if event_datum is not None:
        # This is a day row, store the date and time and reset found_event
        current_date = event_datum.text.strip()
        found_event = False
    else:
        # This is an event row, check if it contains "Figurentheater Petruschka"
        event = gridrow.find('div', class_='gridcolumn small-10 large-5', string='Figurentheater Petruschka')
        event_time = gridrow.find('div', class_='gridcolumn small-2 large-1')  # This is the time element
        seats_div = gridrow.find('div', class_='gridcolumn small-offset-2 small-10 large-offset-0 large-6 gridcolumn-last')
            
        if event is not None and event_time is not None and seats_div is not None:
            # This event is on the current date
            found_event = True
            # Find the seats information
            seats_text = seats_div.text.strip()
            if seats_text == 'Ausgebucht':
                seats = 0
            else:
                # Find all digits in the string
                seats = int(''.join(re.findall(r'\d', seats_text)))

            current_date = current_date + ' ' + event_time.text.strip()
            # Parse the date and time string
            current_date = dateparser.parse(current_date)

            # Create a datetime object with the date and time you want to search for
            search_date = datetime(current_date.year, current_date.month, current_date.day, current_date.hour, current_date.minute)

            # Store the data in the database
            # Use the datetime object to find a record
            record = collection.find_one({'date': search_date})
            if record is not None:
                # The event is already in the database
                # Check if the seats information is different
                if collection.find_one({'date': search_date, 'seats': seats}):
                    # The seats information is the same, do nothing
                    # print the date in the same format as the database
                    print ('Event unchanged: ' + search_date.strftime('%Y-%m-%d %H:%M'))
                    pass
                else:
                    # The seats information is different, update the database
                    result = collection.update_one({'date': search_date}, {'$set': {'seats': seats}})
                    print('Updated event: ' + search_date.strftime('%Y-%m-%d %H:%M'))
            else:
                if (os.environ.get('INSERT') == 'true'):
                    if collection.insert_one({'date': search_date, 'seats': seats}):
                        print('Inserted event: ' + search_date.strftime('%Y-%m-%d %H:%M'))
                else:
                    print('Event not found: ' + search_date.strftime('%Y-%m-%d %H:%M'))
                pass
