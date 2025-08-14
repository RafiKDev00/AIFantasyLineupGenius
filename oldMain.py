#B''SD

from espnClient import get_league

def main():
    league = get_league()
    my_team = next((team for team in league.teams if "testTeam" in team.team_name), None)
    if not my_team:
        raise ValueError("testTeam doesn't exit...go to main.py and change the team name to actually be your team name instead of mine")

    print(f"Team Name: {my_team.team_name}")
    print("Current Roster:")
    for player in my_team.roster:
        print(f"{player.name} ({player.position}) - Projected: {player.projected_avg_points}")

if __name__ == "__main__":
    main()
