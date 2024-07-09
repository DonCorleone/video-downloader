import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import dateparser
from datetime import datetime
from selenium import webdriver
from dotenv import load_dotenv

def get_external_ip():
    response = requests.get("https://api.ipify.org?format=json")
    if response.status_code == 200:
        data = response.json()
        return data.get("ip")
    else:
        return "Unknown"

external_ip = get_external_ip()
print("External IP:", external_ip)

# Get the URL from user input
url = input('Enter the URL: ')

# get the label from user input
label = input('Enter the label: ')

# if label is empty, set it to 'default'
if label == '':
    label = 'Others'

# get the category from user input
category = input('Enter the category: ')

# get the imageUrl from user input
imageUrl = input('Enter the imageUrl: ')

load_dotenv()

# get the cookies from .env file
cookieOneKey = os.getenv('COOKIE_ONE_KEY')
cookieOneValue = os.getenv('COOKIE_ONE_VALUE')
cookieTwoKey = os.getenv('COOKIE_TWO_KEY')
cookieTwoValue = os.getenv('COOKIE_TWO_VALUE')
time.sleep(2)

cookies = {
    cookieOneKey: cookieOneValue,
    cookieTwoKey: cookieTwoValue
}


# Initialize the WebDriver (replace 'path_to_webdriver' with the actual path)
driver = webdriver.Firefox()

# Open the URL
driver.get(url)

# Add cookies
for name, value in cookies.items():
    driver.add_cookie({'name': name, 'value': value})

# Refresh the page to apply the cookies
driver.refresh()
# Wait for 5 seconds
time.sleep(2)
# Get the page source
html = driver.page_source

# Parse the response with BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'}

videos = soup.find_all(id=os.getenv('ID_VIDEOS'))

title = soup.find('h2').text

filename = label + '-' + category + ' - ' + title 

# Find the iframe
iframe = soup.find('iframe')

# Get the source URL of the iframe
iframe_url = 'https:' + iframe['src']

# Send a request to the iframe's URL
# Open the URL
driver.get(iframe_url)

# Add cookies
for name, value in cookies.items():
    driver.add_cookie({'name': name, 'value': value})

# Refresh the page to apply the cookies
driver.refresh()
# Wait for 5 seconds
time.sleep(2)

html = driver.page_source
# Parse the response with BeautifulSoup
iframe_soup = BeautifulSoup(html, 'html.parser')

videowrapper =  iframe_soup.find(id=os.getenv('ID_VIDEO_WRAPPER'))

# loop through the contents of the videowrapper
for content in videowrapper.contents:
    # check if the content is a video tag
    if content.name == 'video':
        # get the video tag
        video = content
        break

poster_src = 'https:' + video['poster']

biggest_source = ''
biggest_width = 0
# loop through the contents of the video
for source in video.contents:
    # check if the content is a source tag
    if source.name == 'source':
        # get the source tag
        source_url = source['src']
        # remove '/?embed=true' from the source URL
        source_url = source_url.replace('/?embed=true', '')
        if biggest_source == '':
            biggest_source = source_url

        # get the width of the video (marked as _xy.mp4 in the videosource)
        width = re.search(r'(\d+)p.mp4', source_url)
        if width:
            width = int(width.group(1))
            if width > biggest_width:
                biggest_width = width
                biggest_source = source['src']
        # if there is 'mp4' in the source URL and the biggestwidth is less than 720, the source URL is the biggest source
        if 'mp4' in source_url and biggest_width < 720:
            biggest_source = source['src']

#download the poster
# if the image URL is empty, set it to the poster source
if imageUrl == '':
    imageUrl = poster_src
response = requests.get(imageUrl, headers=headers)

with open(filename + '.jpg', 'wb') as f:
    f.write(response.content)

#download the video
response = requests.get(biggest_source, headers=headers)

with open(filename + '.mp4', 'wb') as f:
    f.write(response.content)

# close the driver
driver.close()

# execute a command to convert the image to square
os.system(f'convert "{filename}.jpg" \( +clone -rotate 90 +clone -mosaic +level-colors black \) +swap -gravity center -composite "output/{filename}.jpg"')

# execute a command to convert the video to mp4
os.system(f'HandbrakeCli -i "{filename}.mp4" --preset "Apple 1080p30 Surround" -o "output/{filename}.mp4"') 

# delete the original image and video
os.remove(f'{filename}.jpg')
os.remove(f'{filename}.mp4')
