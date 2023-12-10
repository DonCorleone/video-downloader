import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

import os
os.environ.get('KEY')

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

# For each gridrow
for gridrow in gridrows:
    # Find the event-datum
    event_datum = gridrow.find('div', class_='gridcolumn small-12 large-12 event-datum')
    if event_datum is not None:
        # This is a day row, store the date and reset found_event
        current_date = event_datum.text.strip()
        found_event = False
    else:
        # This is an event row, check if it contains "Figurentheater Petruschka"
        event = gridrow.find('div', class_='gridcolumn small-10 large-5', string='Figurentheater Petruschka')
        if event is not None:
            # This event is on the current date
            found_event = True
            # Find the seats information
            seats_div = gridrow.find('div', class_='gridcolumn small-offset-2 small-10 large-offset-0 large-6 gridcolumn-last')
            if seats_div is not None:
                seats_text = seats_div.text.strip()
                if seats_text == 'Ausgebucht':
                    seats = 0
                else:
                    # Find all digits in the string
                    seats = int(''.join(re.findall(r'\d', seats_text)))
            else:
                seats = 'No seats information'
            print(f"Date: {current_date}, Event: {event.text.strip()}, Seats: {seats}")