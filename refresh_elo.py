from scrapers.ncaa_hockey_scraper import run_scraper
from elo.elo_builder import build_elo_table
import datetime, os

def daily_refresh():
    all_games, regular_season, games_df = run_scraper()
    elo_table = build_elo_table(regular_season)

    last_updated = datetime.datetime.now().strftime("%I:%M %p on %A, %B %d, %Y")

    os.makedirs("data", exist_ok=True)
    with open("data/last_updated.txt", "w") as f:
        f.write(last_updated)

    print(f"Elo rankings refreshed successfully at {last_updated}")

if __name__ == "__main__":
    daily_refresh()