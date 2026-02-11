import pandas as pd
from .elo_math import update_elo, default_elo
import sys
import os
# Add parent directory to path so we can import from scrapers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.ncaa_hockey_scraper import d1_team_list, standardized_team_name


def build_elo_table(games_df):
    elo_ratings = {}
    team_stats = {}

    for _, row in games_df.iterrows():
        if not row['Home Score'] or not row['Away Score']:
            continue

        home_raw = row['Home Team']
        away_raw = row['Away Team']
        home_score = int(row['Home Score'])
        away_score = int(row['Away Score'])

        home = standardized_team_name(home_raw)
        away = standardized_team_name(away_raw)

        for team in [home, away]:
            if team not in elo_ratings:
                elo_ratings[team] = default_elo
            if team not in team_stats:
                team_stats[team] = {'W': 0, 'L': 0, 'T': 0}

        home_elo = elo_ratings[home]
        away_elo = elo_ratings[away]

        # --- Determine result
        if home_score == away_score:
            result = 0.5  # tie
        elif abs(home_score - away_score) == 1:
            result = 0.75 if home_score > away_score else 0.25  # OT win/loss
        else:
            result = 1.0 if home_score > away_score else 0.0  # regulation

        # --- Update Elo
        new_home_elo, new_away_elo = update_elo(home_elo, away_elo, result)
        elo_ratings[home] = new_home_elo
        elo_ratings[away] = new_away_elo

        # --- Update W/L stats
        if result > 0.5:
            team_stats[home]['W'] += 1
            team_stats[away]['L'] += 1
        elif result < 0.5:
            team_stats[home]['L'] += 1
            team_stats[away]['W'] += 1
        else:
            team_stats[home]['T'] += 1
            team_stats[away]['T'] += 1

    # --- Map cleaned name -> display name
    original_names = {}
    for _, row in games_df.iterrows():
        for col in ['Home Team', 'Away Team']:
            raw = row[col]
            norm = standardized_team_name(raw)
            if norm not in original_names or len(raw) > len(original_names[norm]):
                original_names[norm] = raw.strip()

    # --- Build final rating table
    ratings_df = pd.DataFrame([
        {
            'team': team,
            'display_name': original_names.get(team, team.title()),
            'rating': round(rating),
            'W': team_stats.get(team, {}).get('W', 0),
            'L': team_stats.get(team, {}).get('L', 0),
            'T': team_stats.get(team, {}).get('T', 0)
        }
        for team, rating in elo_ratings.items()
    ])
    school_df = pd.read_csv("data/school_info.csv")
    school_df["team"] = school_df["Team"].apply(standardized_team_name)

    ratings_df = ratings_df.merge(
        school_df[["team", "Conference"]],
        on="team",
        how="left"
    )



    # --- Ensure all D1 teams are present
    d1_df = pd.DataFrame({'team': d1_team_list})
    d1_df['team'] = d1_df['team'].apply(standardized_team_name)
    full_df = d1_df.merge(ratings_df, on='team', how='left')
    full_df['display_name'] = full_df['display_name'].fillna(full_df['team'].str.title())
    full_df['Conference'] = full_df['Conference'].fillna("")
    full_df['rating'] = full_df['rating'].fillna(default_elo).astype(int)
    full_df['W'] = full_df['W'].fillna(0).astype(int)
    full_df['L'] = full_df['L'].fillna(0).astype(int)
    full_df['T'] = full_df['T'].fillna(0).astype(int)

    full_df = full_df.drop_duplicates(subset='team', keep='first')
    full_df = full_df.sort_values(by='rating', ascending=False).reset_index(drop=True)
    full_df['rank'] = full_df.index + 1
    full_df['team_slug'] = full_df['team'].str.replace(' ', '-')

    return full_df.to_dict(orient='records')


def get_rankings(rankings_df):
    rankings_df = rankings_df.sort_values(by='rating', ascending=False).reset_index(drop=True)
    rankings_df['rank'] = rankings_df.index + 1
    rankings_df['team_slug'] = rankings_df['team'].str.lower().str.replace(' ', '-', regex=False)
    return rankings_df.to_dict(orient='records')
