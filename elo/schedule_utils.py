from scrapers.ncaa_hockey_scraper import d1_team_list

def get_team_schedule(team_name, games):
    team_name_normalized = team_name.lower().replace('.', '').replace("'", '').strip()
    schedule = []

    for game in games:
        home_raw, away_raw = game['Home Team'], game['Away Team']
        home = home_raw.lower().replace('.', '').replace("'", '').strip()
        away = away_raw.lower().replace('.', '').replace("'", '').strip()

        is_home = home == team_name_normalized
        is_away = away == team_name_normalized
        if not (is_home or is_away):
            continue

        opponent = away_raw if is_home else home_raw
        team_score = game['Home Score'] if is_home else game['Away Score']
        opp_score = game['Away Score'] if is_home else game['Home Score']
        date = game['Date']

        if not team_score or not opp_score:
            result_str = 'TBD'
        else:
            team_score, opp_score = int(team_score), int(opp_score)
            result = 'W' if team_score > opp_score else 'L' if team_score < opp_score else 'T'
            result_str = f"{team_score}-{opp_score} ({result})"

        schedule.append({
            'date': date,
            'opponent': opponent,
            'result': result_str,
            'is_d1': opponent.lower().replace('.', '').replace('-', ' ').replace("'", '').strip() in [
                t.lower().replace('.', '').replace('-', ' ').replace("'", '').strip() for t in d1_team_list
            ],
        })

    return schedule