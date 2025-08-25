# espnClient.py
import os
from dotenv import load_dotenv
from urllib.parse import unquote
from espn_api.football import League

def get_league():
    '''
    load ESPN Fantasy Football league object using credentials in .env
    stuff we combined from previous versions
    A) Unquotes `ESPN_S2` to handle URL-encoded cookie values (`%2B` -> `+`).
    B) we Raises an error if required vars are missing.
    '''

    # envs can be annoying and hold previous values, so we just override
    load_dotenv(override=True)

    swid = os.getenv("SWID", "").strip()
    s2 =unquote(os.getenv("ESPN_S2", "").strip())  # decode - honestly this was an overkill
    league_id = os.getenv("LEAGUE_ID", "").strip()
    year = int(os.getenv("YEAR", "2025"))

    if not (swid and s2 and league_id):
        raise RuntimeError("Missing SWID / ESPN_S2 / LEAGUE_ID in .env")

    #debug so we know exactly what league/year we're hitting
    print(f"[espnClient] league_id={league_id} year={year} swid={swid} s2_len={len(s2)}")

    league = League(
        league_id=int(league_id),
        year=year,
        swid=swid,
        espn_s2=s2
    )
    # print(f"Leauge Name: {league.league_id}\n")
    # for team in league.teams:
    #     print(f"Team Name {team.team_name} + Team ID: {team.team_id}")
    
    return league
