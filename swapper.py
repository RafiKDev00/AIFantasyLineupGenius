#B''SD
import os
import time
import requests
import random
from dotenv import load_dotenv
from urllib.parse import unquote
from espn_api.football import League



WEEK = 1
TEAM_ID = 1 # I know i know
load_dotenv(override=True) # override so we reload the .env everytime

def swapper(to_bench, to_lineup):  


    '''
    This is the swapping logic, we are just flipping the lineup positions attached to each player
    so when we post them, we are good to go. 
    '''

    swid_raw = os.getenv("SWID").strip()
    member_id = swid_raw  # includes braces {..}
    league_id = int(os.getenv("LEAGUE_ID"))

    starter_pid, _, starter_slot_id, _, _ = to_bench     # current WR starter you’re benching
    bench_pid,   _, bench_slot_id,   _, _ = to_lineup    # bench WR you’re promoting

    BENCH = 20
    NEW_STARTER_SLOT = starter_slot_id  # fill the vacated WR slot (or whatever the starter’s slot was)

    print(f"bench_pid {bench_pid}, bench_slot_id {bench_slot_id}\n")
    print(f"starter_pid {starter_pid}, starter_slot_id {starter_slot_id}\n")


    payload = {
    "isLeagueManager": False,
    "teamId": TEAM_ID,
    "type": "ROSTER",
    "memberId": member_id,                 # ← use your env SWID (with braces) that you already parsed
    "scoringPeriodId": WEEK,
    "executionType": "EXECUTE",
    "items": [
        {   # move current starter to the bench
            "playerId": starter_pid,
            "type": "LINEUP",
            "fromTeamId": 1,
            "fromLineupSlotId": starter_slot_id,     # e.g., 4 for WR
            "toLineupSlotId": 20                  # 20
        },
        {   # move bench player into the vacated starter slot
            "playerId": bench_pid,
            "type": "LINEUP",
            "fromTeamId": 1,
            "fromLineupSlotId": 20,       # usually 20 if truly on bench
            "toLineupSlotId": starter_slot_id       # e.g., 4 (WR) or whatever was vacated
        }
    ]
}

    #send via writes cluster with browserish headers
    base_writes = "https://lm-api-writes.fantasy.espn.com"
    url = f"{base_writes}/apis/v3/games/ffl/seasons/{2025}/segments/0/leagues/{2056100353}/transactions/"

    s2 = unquote(os.getenv("ESPN_S2").strip())
    cookies = {
        "SWID": swid_raw,
        "espn_s2": s2
    }

    headers = { #so this may not work on google chrome...something to check
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.5 Safari/605.1.15"
        ),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://fantasy.espn.com",
        "Referer": "https://fantasy.espn.com/",
        "X-Fantasy-Platform": "kona-PROD",
        "X-Fantasy-Source": "kona",
    }

    with requests.Session() as sess:
        sess.headers.update(headers)
        sess.cookies.update(cookies)

        # warm-up GET (optional): hit the roster view like a browser
        roster_url = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{2024}/segments/0/leagues/{2056100353}"
        g = sess.get(roster_url, params={"view": "mRoster"}, timeout=15)
        print(f"Warm-up GET: {g.status_code}")

        time.sleep(0.4 + random.random() * 0.6)

        r = sess.post(url, json=payload, timeout=20)
        print(f"POST /transactions/ status: {r.status_code}")
        # ESPN often returns a small JSON or empty body; print for sanity
        try:
            print("Response JSON:", r.json())
        except Exception:
            print("Response text:", r.text[:400])

    print("\nIf that returned 200 and no error message, refresh your lineup page.") #Good stuff to print
    print("If nothing moved, drag/drop once in the browser again and confirm the same slot ids (WR=4, BENCH=20 or FLEX=23).")

   

# {
#     "bidAmount": 0,
#     "executionType": "EXECUTE",
#     "id": "14683b10-2b01-4230-bf87-6ada75d4755b",
#     "isActingAsTeamOwner": false,
#     "isLeagueManager": false,
#     "isPending": false,
#     "items": [
#         {
#             "fromLineupSlotId": 23,
#             "fromTeamId": 0,
#             "isKeeper": false,
#             "overallPickNumber": 0,
#             "playerId": 3116385,
#             "toLineupSlotId": 20,
#             "toTeamId": 0,
#             "type": "LINEUP"
#         },
#         {
#             "fromLineupSlotId": 20,
#             "fromTeamId": 0,
#             "isKeeper": false,
#             "overallPickNumber": 0,
#             "playerId": 3121422,
#             "toLineupSlotId": 23,
#             "toTeamId": 0,
#             "type": "LINEUP"
#         }
#     ],
#     "memberId": "{1DA3F1F0-15C5-4C21-A966-05712BAB7D34}",
#     "proposedDate": 1755504503268,
#     "rating": 0,
#     "scoringPeriodId": 1,
#     "skipTransactionCounters": false,
#     "status": "EXECUTED",
#     "subOrder": 0,
#     "teamId": 1,
#     "type": "ROSTER"
# }




# this worked to swtich briant homas jr and mlaurie!

# {   # move current starter to bench
#                 "playerId": 4432773,
#                 "type": "LINEUP",
#                 "fromTeamId": 1,
#                 "fromLineupSlotId": 4,
#                 "toLineupSlotId": 23
#             },
#             {   # move chosen bench to starter slot at end of this switch BT JR is flex and T MX is a WR
#                 "playerId": 3121422,
#                 "type": "LINEUP",
#                 "fromTeamId": 1,
#                 "fromLineupSlotId": 23,
#                 "toLineupSlotId": 4
#             }
