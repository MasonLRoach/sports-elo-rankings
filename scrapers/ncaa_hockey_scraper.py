import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR

csv_path = os.path.join(DATA_DIR, 'arena_school_info.csv')
school_info_df = pd.read_csv(csv_path)
d1_team_list = school_info_df['Team'].str.strip().tolist()

current_year_url = 'https://www.collegehockeynews.com/schedules/?season=20252026'
base_url = 'https://www.collegehockeynews.com'

abbreviation_to_fullname = school_info_df.set_index('abv')['School'].to_dict()

def get_current_season(url):
    current_date = None
    current_conference = None

    data = []

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    rows = soup.find_all('tr')

    for row in rows:
        if row.get('class') == ['stats-section']:
            current_date = row.find('td').text.strip()
        # Check for conference row
        elif row.get('class') == ['sked-header']:
            current_conference = row.find('td').text.strip()
        elif row.get('valign') == 'top':
            cells = row.find_all('td')
            if len(cells) >= 9:
                away_team = (cells[0].text.strip()).replace('-',' ')
                away_score = cells[1].text.strip()
                home_team = (cells[3].text.strip()).replace('-',' ')
                home_score = cells[4].text.strip()
                ot = cells[5].text.strip()

                data.append([current_date, current_conference , away_team, away_score, home_team, home_score, ot])
    
    return data

data = get_current_season(current_year_url)


columns = ['Date','Conference', 'Away Team', 'Away Score' ,'Home Team', 'Home Score', 'OT']
df = pd.DataFrame(data, columns=columns)


all_games = df
regular_season = df[df['Conference'] != 'Exhibition']


games_df = regular_season[regular_season['Home Score'] != '']

# 🔧 Remove duplicates (case-insensitive)
school_info_df = school_info_df.drop_duplicates(subset=['School'], keep='first')

# 🔧 Normalize capitalization and spacing
school_info_df['School'] = school_info_df['School'].str.strip().str.lower()

# 🔧 Remove accidental non-D1 entries
school_info_df = school_info_df[~school_info_df['School'].str.contains('american international', case=False)]

# ✅ Build final team list
d1_team_list = school_info_df['School'].str.title().tolist()

school_info_df['School'] = (
    school_info_df['School']
    .str.strip()
    .str.replace('-', ' ', regex=False)
    .str.replace('.', '', regex=False)
    .str.lower()
)

d1_team_list = school_info_df['School'].str.title().tolist()

def standardized_team_name(name):
    """Standardize team names to avoid duplicates."""
    return (
        name.strip()
        .lower()
        .replace('.', '')
        .replace("’", "")
        .replace("'", "")
        .replace("state", "state")
        .replace("int'l", "intl")
        .replace('  ', ' ')
    )