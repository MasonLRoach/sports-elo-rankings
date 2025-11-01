from flask import Flask, render_template
from elo_engine import build_elo_table, get_team_schedule
from scrapers.ncaa_hockey_scraper import regular_season, all_games, d1_team_list, games_df

app = Flask(__name__)

elo_table = build_elo_table(regular_season)
team_slug_map = {row['team_slug']: row['team'] for row in elo_table}
display_name_map = {row['team_slug']: row['display_name'] for row in elo_table}

@app.route('/')
def show_rankings():
    return render_template('elo_rankings.html', elo_table=elo_table)



@app.route('/schedule/<path:team_name>')
def show_team_schedule(team_name):
    schedule = get_team_schedule(team_name, all_games.to_dict(orient='records'))
    return render_template('schedule.html', team_name=team_name, schedule=schedule)




if __name__ == '__main__':
    app.run(debug=True)