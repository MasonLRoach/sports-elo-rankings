from flask import Flask, render_template
from scrapers.ncaa_hockey_scraper import run_scraper
from elo.elo_builder import build_elo_table, get_rankings
from elo.schedule_utils import get_team_schedule
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime
import os


app = Flask(__name__)

last_updated = "Unkown"

all_games, regular_season, games_df = run_scraper()
def daily_refresh():
    
    global all_games, regular_season, elo_table, games_df, last_updated

    # 1. Re-scrape data
    all_games, regular_season, games_df = run_scraper()

    # 2. Recalculate Elo rankings
    elo_table = build_elo_table(regular_season)

    last_updated = datetime.datetime.now().strftime("%I:%M %p on %A, %B %d, %Y")
    timestamp_path = os.path.join("data", "last_updated.txt")
    with open(timestamp_path, "w") as f:
        f.write(last_updated)


    


timestamp_path = os.path.join("data", "last_updated.txt")
if os.path.exists(timestamp_path):
    with open(timestamp_path, "r") as f:
        last_updated = f.read().strip()
else:
    last_updated = "Unknown"

elo_table = build_elo_table(regular_season)
team_slug_map = {row['team_slug']: row['team'] for row in elo_table}
display_name_map = {row['team_slug']: row['display_name'] for row in elo_table}

@app.route('/')
def show_rankings():
    return render_template('elo_rankings.html', elo_table=elo_table, last_updated=last_updated)



@app.route('/schedule/<path:team_name>')
def show_team_schedule(team_name):
    schedule = get_team_schedule(team_name, games_df.to_dict(orient='records'))
    return render_template('schedule.html', team_name=team_name, schedule=schedule)




if __name__ == '__main__':
    eastern = pytz.timezone('US/Eastern')  # or 'US/Central' if you prefer
    scheduler = BackgroundScheduler(timezone=eastern)
    scheduler.add_job(daily_refresh, 'cron', hour=6, minute=0)
    scheduler.start()
    app.run(debug=True)