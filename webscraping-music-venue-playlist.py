import os
import spotipy
import pprint
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import datetime

# **************
# SCRAPE WEBSITE
# **************

# Store today's date

today = datetime.date.today()

def getEventPage(url):
    """Call and store events page into a Beautiful Soup object"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

# Scrape events page
url = "https://www.blackcatdc.com/schedule.html"
soup = getEventPage(url)
print('Events page scraped.')

# Get all h1 and h2 tags
h_tags = list(soup.find_all(["h1", "h2"]))

# Extract h2 tags with show dates
dates = list(soup.find_all('h2', {'class' : 'date'}))

def getDates(show_dates):
    """Extract and clean dates from h2 tags"""
    date_str = str(show_dates)
    # Find date and subset h2 tag
    st = date_str.find(">")+1
    ed = date_str.find("</")
    date_substr = date_str[st:ed]
    # Split date string
    date_split = date_substr.split(" ")
    # Format in MDYYY for easier conversion, use the same year as today
    date_formatted = f'{date_split[1]} {date_split[2]}, {today.year}'
    return date_formatted

# Initialize empty list for clean dates
dates_clean = []

# Get clean dates
for i in dates:
    new_date = getDates(i)
    dates_clean.append(new_date)
print('Event dates extracted.')

# Extract h1 tags with headliners
headliner = list(soup.find_all('h1', {'class' : 'headline'}))

# Strip headliners from h tags
def getHeadliners(show_headliners):
    """Extract and clean headliners from h1 tags"""
    headliner_str = str(show_headliners)
    # Remove h tag
    st = headliner_str.find(">")+1
    ed = headliner_str.find("</")
    headliner_str = headliner_str[st:ed]
    # Remove a tag
    st = headliner_str.find(">")+1
    headliner_str = headliner_str[st:]
    return headliner_str

# Initialize empty list for clean headliners
headliners_clean = []

# Get clean headliners
for i in headliner:
    new_headliner = getHeadliners(i)
    headliners_clean.append(new_headliner)
print('Event headliners extracted.')

# Zip top 20 dates and headliners into a shows DataFrame
shows = pd.DataFrame(list(zip(dates_clean[0:21], headliners_clean[0:21])), columns =['dates', 'headliners']) 

# Convert dates in df to date objects
shows["dates"] = pd.to_datetime(shows["dates"], format='%B %d, %Y')

# Store date that is three weeks from today
three_weeks = today + datetime.timedelta(days=21)

# Convert three weeks date to a pandas datetime obj
three_weeks_obj = pd.to_datetime(three_weeks)

# Subset shows dataframe to only rows within three weeks from today
shows_three_weeks = shows.loc[shows["dates"] <= three_weeks_obj]


# ***************
# UPDATE PLAYLIST
# ***************


#  Set Spotipy environment variables
os.environ['SPOTIPY_CLIENT_ID'] = 'INSERT HERE'
os.environ['SPOTIPY_CLIENT_SECRET'] = 'INSERT HERE'
os.environ['SPOTIPY_REDIRECT_URI'] = 'INSERT HERE'

# Connect app to Spotify

from spotipy.oauth2 import SpotifyOAuth
scope = 'playlist-modify-private playlist-modify-public'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

def getTopTen(artist):
    """Search Spotify for artist and their top ten songs"""
    # search for artist 
    results = sp.search(q='artist:' + artist, type='artist')
    # if found, get artist id of first artist listed
    if len(results['artists']['items']) != 0:
        artist_id = results['artists']['items'][0]['id']
        # get top 10 tracks
        top_ten_tracks = sp.artist_top_tracks(artist_id,country='US')
        top_ten_tracks_ids = []
        i = 0
        while i < len(top_ten_tracks['tracks']):
            top_ten_tracks_ids.append(top_ten_tracks['tracks'][i]['id'])
            i += 1
        return top_ten_tracks_ids

# Loop through shows dataframe and get track ids for each artists's top ten songs
master_track_id_list = [] # empty list

for index, row in shows_three_weeks.iterrows():
    artist = row['headliners']
    top_ten_songs = getTopTen(artist)
    if top_ten_songs != None:
        for i in top_ten_songs:
            master_track_id_list.append(i)
print('Top ten songs for headliners acquired.')

# Update Spotify playlist
playlist_id = 'INSERT HERE'
sp.playlist_replace_items(playlist_id, master_track_id_list)
print('Playlist updated.')
