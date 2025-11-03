from scrapers.ncaa_hockey_scraper import data, regular_season
from elo_engine import update_elo, get_rankings, build_elo_table


build_elo_table(regular_season)