import pandas as pd
import json
import os
from datetime import datetime
from elo.elo_builder import build_elo_table

# Load the games data
games_df = pd.read_csv("data/games.csv")

# Build ELO rankings using existing system
rankings_list = build_elo_table(games_df)

# Convert to the format the website expects
rankings_for_web = []
for item in rankings_list:
    rankings_for_web.append({
        'rank': item['rank'],
        'team': item['display_name'],
        'rating': item['rating']
    })

# Create the JSON output
output = {
    'last_updated': datetime.now().isoformat(),
    'rankings': rankings_for_web
}

# Save to data/rankings.json
os.makedirs("data", exist_ok=True)
with open("data/rankings.json", 'w') as f:
    json.dump(output, f, indent=2)

print(f"✅ Saved {len(rankings_for_web)} team rankings to data/rankings.json")
print(f"Top 5 teams:")
for i, team in enumerate(rankings_for_web[:5], 1):
    print(f"  {i}. {team['team']} - {team['rating']}")
