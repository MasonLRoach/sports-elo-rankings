default_elo = 1000
k_factor = 24
home_advantage = 2  # Elo points added to home team for expected win calculation


def update_elo(home_elo, away_elo, result, k=k_factor, home_advantage=home_advantage):
    # 538-style expected win probability
    adj_home_elo = home_elo + home_advantage
    expected_home_win = 1 / (1 + 10 ** ((away_elo - adj_home_elo) / 400))

    # Actual delta based on fractional result
    delta = k * (result - expected_home_win)

    new_home_elo = home_elo + delta
    new_away_elo = away_elo - delta

    return new_home_elo, new_away_elo
