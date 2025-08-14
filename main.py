
# B''SD
import os, json, time, random, requests
from urllib.parse import unquote
from dotenv import load_dotenv
from espnClient import get_league


''' 
these variables are for early stage use only
Team_ID is hardcoding information for test team in the leauge
easier to do when you don't have multiple teams in the leauge - then you
can just search by team name
As for the week number - well we'll have to get a server going to take care of
time related issues, and we just aren't there yet

'''
TEAM_ID = 1
WEEK = 1 


'''
GPT came in the clutch
easy way of mapping players to their positions/slots in the lineup, because sometimes
espn gives you a string ID, and sometimes a numerical one.
it's super cool, and you can find this by either checking out the espn api
or reverse engineering it by looking at the developer tools and seeing what 
it outputs when you swap players around
'''
SLOT_NAME_TO_ID = {
    "WR": 4,
    "W/R/T": 23, "FLEX": 23,   #Not sure flex or bench is written
    "D/ST": 16,
    "K": 17,
    "QB": 0,
    "RB": 2,
    "IR":21,
    "BE": 20, "BN": 20, "BENCH": 20
}

'''
get all the values from .env, ESPN_S2, leauge ID, and SID and ya override here too...we don't wanan reset the enviroment everytime
'''
load_dotenv(override=True)

def slot_info(p):
    ''' 
    Here we return (lineupSlotId or 'None', slot_name_upper) from a Player we get from the espn_api
    '''
    sid = getattr(p, "lineupSlotId", None) #this may be poorly named cause there is another sid, but sid = slot id
    if sid is None:
        sid =getattr(p, "slotPositionId", None) #if no slot id, then try to get the string, we need one or the other
    sname = (getattr(p, "lineupSlot", "") or "").upper() #standardizing the string value for the player because espn is a mess!
    return sid, sname

def slot_id_from_name(name_upper: str) -> int:
    '''
    we try to only use numbers, the so called slot ID's so if we got a string we consult our map that
    GPT found, and convert the string values to nums before preceeding. If we don't know the value we default
    to bench value: 20. I have every position in my personal leauge mapped out, I know there are others, so a point 
    should be made in a future more broadly functional update to find and input the rest of the values.
    If I don't get to it...you future user, have been made aware.
    '''
    for key, val in SLOT_NAME_TO_ID.items():
        if key in name_upper:
            return val
    return 20 #bench value


def is_bench(p):
    ''' 
    method used to check if someone is on the bench, it's one thing to know if someone IS 
    a widereceiver, but we are also concerned as to where they reside.
    '''
    _,name = slot_info(p)
    return name in ("BE", "BN", "BENCH")

def is_wr_starter(p): #this is straight boolean 
    '''
    This is the oppisite of the earlier check. We've estebalished the player has wide reciver number - but is
    he playing in a wide reciever spot, (we are checking if he's either conventional WR or playing flex, no matter
    how it is illlustrated)
    '''
    if p.position != "WR":
        return False
    _, name = slot_info(p)
    return (("WR" in name) and (name not in ("BE", "BN", "BENCH"))) or ("FLEX" in name) or ("W/R/T" in name)

def proj_week(p, week):
    '''
    Gets the players projected value for the week, otherwise returns zero or an exception with 0, 
    I am curious what happens if, say, all the WR's are injured
    '''
    try:
        v = p.projected_points(week)
        return 0.0 if v is None else float(v)
    except Exception:
        return 0.0

def main():
    '''
      Basic Gist
      A Fetch league and selects the team by TEAM_ID
      B We partition the roster into WR starters vs bench WRs
      C Find the lowest projected starter and highest projected bench - by the week
      D Build the exact TRANSACTIONS payload the ESPN web client uses
      E POST it to the writes cluster with "browser-like headers" & your cookies
      F Print the results
    '''
    league = get_league() # comes from the espnClient.py file
    team = next((t for t in league.teams  if getattr(t, "team_id", None) == TEAM_ID), None) # looking for our team based off teamID  given in env - Will probably switch to name when back in my leauge
    if not team:
        raise RuntimeError(
            "Couldn't find TEAM_ID. Available:\n" +
            "\n".join([f"  team_id={getattr(t,'team_id','?')} | {t.team_name}" for t in league.teams])
        )
    print(f"Team: {team.team_name} (team_id={TEAM_ID}) | Week={WEEK}") # 

    '''
    making two lists, one of WR's on the bench, and one of WR's in the starting lineup.
    These methods could TOTALLY be made more efficient, but it's not worth the time. Our goal
    isn't to swap Wide recivers. So we will have to plan this out. But anyway, 
    the built on logic will be moved to the lineUp Genius in the next iteration. 
    What happens in this line, will likely only be preserved as calls to files,
    which if they are even done as calls to files, will likely not be seen in this file
    '''
    wr_starters = [p for p in team.roster if is_wr_starter(p)]
    wr_bench = [p for p in team.roster if p.position == "WR" and is_bench(p)]


    '''
    GPT does write great print statements. Very clear, We loop thrugh the roster
    if we Find a wide reciver we print his slot ID, his name, wether he is a bench player
    and his projection for the week
    '''
    print("\nWR snapshot:")
    for p in team.roster:
        if p.position != "WR": continue
        sid, sname = slot_info(p)
        print(f"  {p.name:<24} slot_id={sid!s:<4} slot_name='{sname}' "
              f"bench={'YES' if is_bench(p) else 'NO'} proj[{WEEK}]={proj_week(p,WEEK):.2f}")


    '''
    I am not even sure ESPN will let this happen (maybe if everyone is on the IR...but not sure
    my leauge even let's that happen). But hypothetically, if no available players, we get an error.
    It's just good practice.
    '''
    if not wr_starters or not wr_bench:
        raise RuntimeError("We need at least 1 starter WR and 1 bench WR to swap...")

    #find the best and worst of our list of wide recivers
    low_wr= min(wr_starters, key=lambda x: proj_week(x,  WEEK))
    high_wr = max(wr_bench,key=lambda x: proj_week(x, WEEK))

    '''
    This is the swapping logic, we are just flipping the lineup positions attached to each player
    so when we post them, we are good to go. 
    '''
    starter_slot_id, starter_slot_name = slot_info(low_wr)
    if starter_slot_id is None:
        starter_slot_id = slot_id_from_name(starter_slot_name or "WR")  # default to a WR
    bench_slot_id, bench_slot_name = slot_info(high_wr)
    if bench_slot_id is None:
        bench_slot_id = slot_id_from_name(bench_slot_name or "BE") # default to BENCH( slot 20)

    '''
    some gorgeous GPT print outs
    '''
    print(f"\nPlanned swap (Week {WEEK}):")
    print(f"  OUT (starter) : {low_wr.name:<24}  [{starter_slot_id} -> {bench_slot_id}]")
    print(f"  IN  (bench)   : {high_wr.name:<24}  [{bench_slot_id} -> {starter_slot_id}]")

    '''
      will include more instructions on how I got this, but basically
      I took the information from the developer tool and filterd for the 
      posts after swapping a player. Based on that, we moved! I had GPT do the formatting
      just way easier.
    
    '''
    swid_raw = os.getenv("SWID").strip()
    member_id = swid_raw  # includes braces {..}
    league_id = int(os.getenv("LEAGUE_ID"))

    payload = {
        "isLeagueManager": False,
        "teamId": TEAM_ID,
        "type": "ROSTER",
        "memberId": member_id,
        "scoringPeriodId": WEEK,
        "executionType": "EXECUTE",
        "items": [
            {   # move current starter to bench
                "playerId": int(low_wr.playerId),
                "type": "LINEUP",
                "fromLineupSlotId": int(starter_slot_id),
                "toLineupSlotId": int(bench_slot_id)
            },
            {   # move chosen bench to starter slot
                "playerId": int(high_wr.playerId),
                "type": "LINEUP",
                "fromLineupSlotId": int(bench_slot_id),
                "toLineupSlotId": int(starter_slot_id)
            }
        ]
    }

    #send via writes cluster with browserish headers
    base_writes = "https://lm-api-writes.fantasy.espn.com"
    url = f"{base_writes}/apis/v3/games/ffl/seasons/{league.year}/segments/0/leagues/{league_id}/transactions/"

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
        roster_url = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{league.year}/segments/0/leagues/{league_id}"
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

if __name__ == "__main__":
    main()
