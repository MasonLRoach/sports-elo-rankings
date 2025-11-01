import pandas as pd
from scrapers.ncaa_hockey_scraper import games_df, all_games, played_games, regular_season, d1_team_list
default_elo = 1000
k_factor = 24
HOME_ADVANTAGE = 12  # Elo points added to home team for expected win calculation



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


def clean_team_name(name):
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

def build_elo_table(games_df):
    elo_ratings = {}
    team_stats = {}  # track W/L

    for _, row in games_df.iterrows():
        if not row['Home Score'] or not row['Away Score']:
            continue

        home_raw = row['Home Team']
        away_raw = row['Away Team']
        home_score = int(row['Home Score'])
        away_score = int(row['Away Score'])

        home = clean_team_name(home_raw)
        away = clean_team_name(away_raw)

        for team in [home, away]:
            if team not in elo_ratings:
                elo_ratings[team] = default_elo
            if team not in team_stats:
                team_stats[team] = {'W': 0, 'L': 0}

        home_elo = elo_ratings[home]
        away_elo = elo_ratings[away]
        home_won = home_score > away_score

        new_home_elo, new_away_elo = update_elo(home_elo, away_elo, home_won)
        elo_ratings[home] = new_home_elo
        elo_ratings[away] = new_away_elo

        if home_won:
            team_stats[home]['W'] += 1
            team_stats[away]['L'] += 1
        else:
            team_stats[home]['L'] += 1
            team_stats[away]['W'] += 1

    # Build ratings DataFrame
    original_names = {}
    for _, row in games_df.iterrows():
        for t in ['Home Team', 'Away Team']:
            raw_name = row[t]
            norm_name = clean_team_name(raw_name)
            if norm_name not in original_names or len(raw_name) > len(original_names[norm_name]):
                original_names[norm_name] = raw_name.strip()

    # Step 2: build ratings_df with display name
    ratings_df = pd.DataFrame([
        {
            'team': team,
            'display_name': original_names.get(team, team.title()),  # fallback to title case
            'rating': round(rating),
            'W': team_stats.get(team, {}).get('W', 0),
            'L': team_stats.get(team, {}).get('L', 0)
        }
        for team, rating in elo_ratings.items()
    ])

    # Clean D1 team list
    d1_df = pd.DataFrame({'team': d1_team_list})
    d1_df['team'] = d1_df['team'].apply(clean_team_name)

    # merge
    full_df = d1_df.merge(ratings_df, on='team', how='left')
    full_df = full_df.drop_duplicates(subset='team', keep='first')
    full_df['display_name'] = full_df['display_name'].fillna(full_df['team'].str.title())


    # Fill missing teams with defaults
    full_df['rating'] = full_df['rating'].fillna(default_elo).astype(int)
    full_df['W'] = full_df['W'].fillna(0).astype(int)
    full_df['L'] = full_df['L'].fillna(0).astype(int)

    # Add slug + rank
    full_df = full_df.sort_values(by='rating', ascending=False).reset_index(drop=True)
    full_df['rank'] = full_df.index + 1
    full_df['team_slug'] = full_df['team'].str.replace(' ', '-')

# Final output
    return full_df.to_dict(orient='records')

    return full_elo_df.to_dict(orient='records')

def get_rankings(rankings_df):
    rankings_df = rankings_df.sort_values(by='rating', ascending=False).reset_index(drop=True)
    rankings_df['rank'] = rankings_df.index + 1
    rankings_df['team_slug'] = rankings_df['team'].str.lower().str.replace(' ', '-', regex=False)
    return rankings_df.to_dict(orient='records')


def get_team_schedule(team_name, games):
    team_name_normalized = team_name.lower().replace('.', '').replace("'", '').strip()

    schedule = []

    for game in games:
        home_raw = game['Home Team']
        away_raw = game['Away Team']

        home = home_raw.lower().replace('.', '').replace("'", '').strip()
        away = away_raw.lower().replace('.', '').replace("'", '').strip()

        is_home = home == team_name_normalized
        is_away = away == team_name_normalized

        if is_home or is_away:
            opponent = away_raw if is_home else home_raw
            team_score = game['Home Score'] if is_home else game['Away Score']
            opp_score = game['Away Score'] if is_home else game['Home Score']
            date = game['Date']

            if not team_score or not opp_score:
                result_str = 'TBD'
            else:
                team_score = int(team_score)
                opp_score = int(opp_score)
                result = 'W' if team_score > opp_score else 'L'
                result_str = f"{team_score}-{opp_score} ({result})"

            # create a safe link for the opponent
            opponent_slug = opponent

            schedule.append({
                'date': date,
                'opponent': opponent,
                'opponent_slug': opponent_slug,
                'result': result_str,
                'is_d1': opponent in d1_team_list,
            })

    return schedule
