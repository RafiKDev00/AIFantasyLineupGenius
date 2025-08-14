# from espn_api.football import League
# import json
# import os
# from dotenv import load_dotenv

# load_dotenv()  # loads .env if it exists


# def load_credentials():
#   ''' if we are in testing mode we may use the credential file but dangerous on
#       github...so we also have the .env for the boys who should know
#   '''
#   swid = os.getenv("SWID")
#   s2 = os.getenv("ESPN_S2")
#   league_id = os.getenv("LEAGUE_ID")

#   if swid and s2 and league_id:
#       return swid, s2, league_id

#   #if no env...i.e we are in some kind of testing mode, use credentials DELETE THIS LATER
#   # with open("credentials.json", encoding="utf-8") as fp:
#   #   creds = json.load(fp)
#   #   return creds["SWID"], creds["espn_s2"], league_id

# def get_league():
#   swid, s2, league_id = load_credentials()
#   year = 2025 # add a check to change the year when it's not this year etc

#   league = League(
#     year=year,
#     swid=swid,
#     espn_s2=s2,
#     league_id=int(league_id),
#   )
#   return league

# espnClient.py
import os
from dotenv import load_dotenv
from urllib.parse import unquote
from espn_api.football import League

def get_league():
    # env's can being annoying and can hold previous values so we'd have to deactivate and reactive everytime...nah just override
    load_dotenv(override=True)

    swid = os.getenv("SWID", "").strip()
    s2 = unquote(os.getenv("ESPN_S2", "").strip())  # decode %2B -> + etc.
    league_id = os.getenv("LEAGUE_ID", "").strip()
    year = int(os.getenv("YEAR", "2025"))

    if not (swid and s2 and league_id):
        raise RuntimeError("Missing SWID / ESPN_S2 / LEAGUE_ID in .env")

    # debug so we know exactly what league/year we’re hitting
    print(f"[espnClient] league_id={league_id} year={year} swid={swid} s2_len={len(s2)}")

    league = League(
        league_id=int(league_id),
        year=year,
        swid=swid,
        espn_s2=s2
    )
    return league
