from scrapers.ncaa_hockey_scraper import data
from elo_engine import run_elo, get_rankings, get_team_schedule


rankings_df, history_df = run_elo()

rankings = get_rankings(rankings_df)


if __name__ == "__main__":
    rankings_df, history_df = run_elo()
    rankings = get_rankings(rankings_df)