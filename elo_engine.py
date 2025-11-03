import pandas as pd
from scrapers.ncaa_hockey_scraper import games_df, all_games, played_games, regular_season, d1_team_list, standardized_team_name
default_elo = 1000
k_factor = 24
home_advantage = 2  # Elo points added to home team for expected win calculation



# ---- Elo Update Function ----
def update_elo(home_elo, away_elo, result, k=k_factor, home_advantage=home_advantage):
    # 538-style expected win probability
    adj_home_elo = home_elo + home_advantage
    expected_home_win = 1 / (1 + 10 ** ((away_elo - adj_home_elo) / 400))

    # Actual delta based on fractional result
    delta = k * (result - expected_home_win)

    new_home_elo = home_elo + delta
    new_away_elo = away_elo - delta

    return new_home_elo, new_away_elo





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

        # --- Determine result as 538-style fraction
        if home_score == away_score:
            result = 0.5  # tie
        elif abs(home_score - away_score) == 1:
            result = 0.75 if home_score > away_score else 0.25  # OT win/loss
        else:
            result = 1.0 if home_score > away_score else 0.0  # regulation

        # --- Update Elo using new 538 function
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

    # --- Ensure all D1 teams are present
    d1_df = pd.DataFrame({'team': d1_team_list})
    d1_df['team'] = d1_df['team'].apply(standardized_team_name)
    full_df = d1_df.merge(ratings_df, on='team', how='left')
    full_df['display_name'] = full_df['display_name'].fillna(full_df['team'].str.title())
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
                result_str = 'TBD' # Maybe get the time of the game?
            else:
                team_score = int(team_score)
                opp_score = int(opp_score)
                """Get the result of the game"""
                if team_score > opp_score:
                    result = 'W'
                elif team_score < opp_score:
                    result = 'L'
                else:
                    result = 'T'

                result_str = f"{team_score}-{opp_score} ({result})"

            # create a safe link for the opponent
            opponent_slug = opponent

            schedule.append({
                'date': date,
                'opponent': opponent,
                'opponent_slug': opponent_slug,
                'result': result_str,
                'is_d1': opponent.lower().replace('.', '').replace('-', ' ').replace("'", '').strip() in [
                    t.lower().replace('.', '').replace('-', ' ').replace("'", '').strip() for t in d1_team_list
                ],
            })

    return schedule