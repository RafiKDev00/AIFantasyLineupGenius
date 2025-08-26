#B''SD
import os
import time
import requests
import random
from dotenv import load_dotenv
from urllib.parse import unquote
from espn_api.football import League



TEAM_NAME = "RafiSquared" # I know i know
load_dotenv(override=True) # override so we reload the .env everytime
TEAM_ID = int(os.getenv("TEAM_ID"))
LEAGUE_ID = int(os.getenv("LEAGUE_ID"))
SWID = (os.getenv("SWID"))
YEAR = int(os.getenv("YEAR"))#
ESPN_S2 = (os.getenv("ESPN_S2"))


BASE_WRITES = "https://lm-api-writes.fantasy.espn.com"
WRITES_URL  = f"{BASE_WRITES}/apis/v3/games/ffl/seasons/{YEAR}/segments/0/leagues/{LEAGUE_ID}/transactions/"

def swapper_but_now_one_by_one(moves, week):
    if not moves:     # If no planned moves, log and exit 
        print("No moves needed.")
        return
    payload_base = { 
        "isLeagueManager": False,
        "teamId": TEAM_ID,
        "type": "ROSTER",
        "memberId": SWID,
        "scoringPeriodId": week,
        "executionType": "EXECUTE",
    }
    with requests.Session() as s:
        s.cookies.update({"SWID": SWID, "espn_s2": ESPN_S2})   # Attach auth cookies  SWID and espn_s2 authenticate you
        for it in moves: #Iterate through the ordered list of single-player moves
            payload = dict(payload_base)
            payload["items"] = [{
                "type": "LINEUP",
                "playerId": it["playerId"],
                "fromTeamId": TEAM_ID,
                "fromLineupSlotId": it["fromLineupSlotId"],
                "toTeamId": TEAM_ID,
                "toLineupSlotId": it["toLineupSlotId"],
            }]
            response = s.post(WRITES_URL, json=payload, timeout=20)  # Send the POST to ESPN's transactions endpoint
            print("move", it, "→", response.status_code)
            try:
                print(response.json())
            except Exception:
                print(response.text[:200])

