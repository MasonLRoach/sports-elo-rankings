import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys
import json

# Configure
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR

# Load URL
current_year_url = "https://www.collegehockeynews.com/schedules/?season=20252026"
base_url = "https://www.collegehockeynews.com"

# Load School Info
csv_path = os.path.join(DATA_DIR, "school_info.csv")
school_info_df = pd.read_csv(csv_path)

# Clean school list only once
school_info_df = (
    school_info_df.drop_duplicates(subset=["School"], keep="first")
    .assign(School=lambda df: df["School"]
            .str.strip()
            .str.replace("-", " ", regex=False)
            .str.replace(".", "", regex=False)
            .str.lower())
)

d1_team_list = school_info_df["School"].str.title().tolist() # Creates list of d1 teams
abbreviation_to_fullname = school_info_df.set_index("abv")["School"].to_dict()
print(d1_team_list)


# --- Scraper core ---
def get_current_season(url):
    """Scrape College Hockey Scores"""
    current_date = None
    current_conference = None
    data = []

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("tr")

    for row in rows:
        if row.get("class") == ["stats-section"]:
            current_date = row.find("td").text.strip()
        elif row.get("class") == ["sked-header"]:
            current_conference = row.find("td").text.strip()
        elif row.get("valign") == "top":
            cells = row.find_all("td")
            if len(cells) >= 9:
                away_team = cells[0].text.strip().replace("-", " ")
                away_score = cells[1].text.strip()
                home_team = cells[3].text.strip().replace("-", " ")
                home_score = cells[4].text.strip()
                ot = cells[5].text.strip()

                data.append([
                    current_date, current_conference,
                    away_team, away_score,
                    home_team, home_score, ot
                ])
    return data


def standardized_team_name(name: str) -> str:
    """Normalize team names to avoid duplicates."""
    return (
        name.strip()
        .lower()
        .replace(".", "")
        .replace("’", "")
        .replace("'", "")
        .replace("int'l", "intl")
        .replace("  ", " ")
    )


# --- Daily wrapper for scheduler ---
def run_scraper():
    """Re-scrape schedule and write CSV of current games."""
    data = get_current_season(current_year_url)

    columns = ["Date", "Conference", "Away Team", "Away Score",
               "Home Team", "Home Score", "OT"]
    df = pd.DataFrame(data, columns=columns)

    # Filter regular season, remove unplayed games
    regular_season = df[df["Conference"] != "Exhibition"]
    games_df = regular_season[regular_season["Home Score"] != ""]
    all_games = df

    output_path = os.path.join(DATA_DIR, "games.csv")
    games_df.to_csv(output_path, index=False)
    
    # ADD THIS - Save as JSON too
    json_output_path = os.path.join(DATA_DIR, "games.json")
    games_json = games_df.to_dict(orient='records')
    with open(json_output_path, 'w') as f:
        json.dump(games_json, f, indent=2)
    
    print(f"Saved {len(games_df)} games to CSV and JSON")

    return games_df, regular_season, all_games

# Run File
if __name__ == "__main__":
    run_scraper()
