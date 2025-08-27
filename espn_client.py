# espnClient.py
import os
from dotenv import load_dotenv
from urllib.parse import unquote
from espn_api.football import League
from send_email import notify_via_email

def get_league():
    '''
    load ESPN Fantasy Football league object using credentials in .env
    stuff we combined from previous versions
    A) Unquotes `ESPN_S2` to handle URL-encoded cookie values (`%2B` -> `+`).
    B) we Raises an error if required vars are missing.
    '''

    # envs can be annoying and hold previous values, so we just override
    # load_dotenv(override=True)
    load_dotenv(override=not os.getenv("GITHUB_ACTIONS"))

    swid = os.getenv("SWID", "").strip()
    s2 =unquote(os.getenv("ESPN_S2", "").strip())  # decode - honestly this was an overkill
    league_id = os.getenv("LEAGUE_ID", "").strip()
    year = int(os.getenv("YEAR", "2025"))

    if not (swid and s2 and league_id):
        raise RuntimeError("Missing SWID / ESPN_S2 / LEAGUE_ID in .env")

    #debug so we know exactly what league/year we're hitting
    print(f"[espnClient] league_id={league_id} year={year} swid={swid} s2_len={len(s2)}")

    # print(f"Leauge Name: {league.league_id}\n")
        # for team in league.teams:
        #     print(f"Team Name {team.team_name} + Team ID: {team.team_id}")
    try:
        league = League(
            league_id=int(league_id),
            year=year,
            swid=swid,
            espn_s2=s2,
        )
        ''' 
        So I played around a lot with SWID and ESPN_S2's etc, and it seems like SWID
        aren't all that important, Like it can be incorrect and everything can still work (confirmed by ChatGpt)
        You may need this to get in if you are originally not logged in, maybe, 
        in which case I make you check anyway, it's harmless, both values are right next to each other
        on the cookies page of developer mode. But yeah ESPN_S2 autofails everything, somethign to keep in mind
        
        
        '''
        # print(f"Leauge Name: {league.league_id}\n")
        # for team in league.teams:
        #     print(f"Team Name {team.team_name} + Team ID: {team.team_id}")
        expected_league_name = os.getenv("LEAGUE_NAME")
        if expected_league_name:
            actual = (getattr(league.settings, "name", "") or "").strip()
            if actual.lower() != expected_league_name.strip().lower():
                notify_via_email(
                    "LineupGenius: league name mismatched", # I love you chatGPT print statements...never cahnge
                    f"Expected '{expected_league_name}', got '{actual}' for LEAGUE_ID {league.league_id}."
                )
                raise RuntimeError("LEAGUE_NAME mismatched...")
        expected_league_id = os.getenv("LEAGUE_ID", "").strip()
        if expected_league_id != league_id:
            raise RuntimeError("NO LEAGUE FOUND!!!!")
        
        return league
    except Exception as e:
        notify_via_email(
            "LineupGenius: ESPN login/league fetch failed - likely improper .env credentials SWID, ESPN_S2 etc.",
            f"{type(e).__name__}: {e}"
        )
    # exit with errror message - kill program - user gets an email
        exit("lOGIN FAILED CHECK .ENV CREDENTIALS")
