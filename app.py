from flask import Flask, render_template
from scrapers.ncaa_hockey_scraper import run_scraper
from elo.elo_builder import build_elo_table, get_rankings
from elo.schedule_utils import get_team_schedule
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

app = Flask(__name__)

eastern = pytz.timezone('US/Eastern')  # or 'US/Central' if you prefer
scheduler = BackgroundScheduler(timezone=eastern)
scheduler.add_job(run_scraper, 'cron', hour=6, minute=0)
scheduler.start()

all_games, regular_season = run_scraper()



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