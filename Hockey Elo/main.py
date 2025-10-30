import requests
from bs4 import BeautifulSoup
import pandas as pd
import math
import os

current_year_url = 'https://www.collegehockeynews.com/schedules/?season=20252026'
base_url = 'https://www.collegehockeynews.com'

script_dir = os.path.dirname(__file__)
csv_path = os.path.join(script_dir, 'arena_school_info.csv')

school_info_df = pd.read_csv(csv_path)
abbreviation_to_fullname = school_info_df.set_index('abv')['School'].to_dict()

def get_current_season(url):
    current_date = None
    current_conference = None

    data = []

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')

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

                data.append([current_date, current_conference , away_team, away_score, home_team, home_score])
    
    return data

data = get_current_season(current_year_url)

columns = ['Date','Conference', 'Away Team', 'Away Score' ,'Home Team', 'Home Score']
df = pd.DataFrame(data, columns=columns)


# Filter games that have not been played
df = df[df['Home Score'] != '']

# Print length of dataframe before and after filtering for exhibition games
print(f'Length of dataframe before filtering for exhibition games: {len(df)}')

# Filter out exhibition games - Conference = Exhibition
df = df[df['Conference'] != 'Exhibition']

print(f'Length of dataframe after filtering for exhibition games: {len(df)}')


games_df = df.copy()



# ---- Elo Parameters ----
default_elo = 1500
k_factor = 24
HOME_ADVANTAGE = 35  # Elo points added to home team for expected win calculation

# ---- Initialize Elo Ratings and History ----
elo_ratings = {}
elo_history = []

# ---- Elo Update Function ----
def update_elo(home_elo, away_elo, home_won, k=k_factor, home_advantage=HOME_ADVANTAGE):
    # Apply home ice advantage for win probability only
    adj_home_elo = home_elo + home_advantage
    expected_home_win = 1 / (1 + 10 ** ((away_elo - adj_home_elo) / 400))

    if home_won:
        new_home_elo = home_elo + k * (1 - expected_home_win)
        new_away_elo = away_elo + k * (0 - (1 - expected_home_win))
    else:
        new_home_elo = home_elo + k * (0 - expected_home_win)
        new_away_elo = away_elo + k * (1 - (1 - expected_home_win))

    return new_home_elo, new_away_elo

# ---- Elo Processing Loop ----
for _, row in games_df.iterrows():
    home = row['Home Team']
    away = row['Away Team']
    home_score = int(row['Home Score'])
    away_score = int(row['Away Score'])

    # Initialize teams if not already present
    for team in [home, away]:
        if team not in elo_ratings:
            elo_ratings[team] = default_elo

    home_elo = elo_ratings[home]
    away_elo = elo_ratings[away]
    home_won = home_score > away_score

    # Update ratings
    new_home_elo, new_away_elo = update_elo(home_elo, away_elo, home_won)

    elo_ratings[home] = new_home_elo
    elo_ratings[away] = new_away_elo

    # Optional: track Elo history for analysis or plotting
    elo_history.append({
        'Date': row['Date'],
        'Home Team': home,
        'Away Team': away,
        'Home Score': home_score,
        'Away Score': away_score,
        'Home Elo (pre)': home_elo,
        'Away Elo (pre)': away_elo,
        'Home Elo (post)': new_home_elo,
        'Away Elo (post)': new_away_elo
    })

# ---- Optional: Create DataFrame of Elo history ----
final_elo_df = pd.DataFrame([
    {'Team': team, 'Elo Rating': int(rating)}
    for team, rating in elo_ratings.items()
])

final_elo_df = final_elo_df.sort_values(by='Elo Rating', ascending=False).reset_index(drop=True)
final_elo_df.to_csv('elo_rankings_2025_2026.csv', index=False)

print(final_elo_df)


import pandas as pd

df = pd.read_csv('elo_rankings_2025_2026.csv')

# Convert to HTML
html_table = df.to_html(index=False, classes='elo-table', border=0)

# Wrap in basic HTML
html_page = f"""
<!DOCTYPE html>
<html>
<head>
    <title>College Hockey Elo Rankings</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 2em; }}
        h1 {{ text-align: center; }}
        .elo-table {{
            width: 60%;
            margin: auto;
            border-collapse: collapse;
        }}
        .elo-table th, .elo-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }}
        .elo-table th {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    <h1>College Hockey Elo Rankings</h1>
    {html_table}
</body>
</html>
"""

# Save to file
with open('elo_rankings.html', 'w') as f:
    f.write(html_page)