

# B''SD
# main.py
import os
from dotenv import load_dotenv
from lineup_genius import lineup_optimizer
from espn_client import get_league


#configuration stuff
TEAM_NAME = "RafiSquared"  # this will change when we've drafted and can use regualr team name
WEEK = 1   # We will have a server that'll track the week "automatically", but for now hardcoded

load_dotenv(override=True) # override so we reload the .env everytime
TEAM_ID = int(os.getenv("TEAM_ID"))


SLOT_NAME_TO_ID = { #backup slot id's
    "QB": 0, "RB": 2, "WR": 4, "TE": 6, "D/ST": 16, "K": 17,
    "W/R/T": 23, "FLEX": 23, "RB/WR/TE": 23, "BE": 20, "BN": 20, "BENCH": 20, "IR": 21
}

def slot_info(p):
    """
    Return (slot_id (int), slot_label (UPPER)) for a roster player.
    Tries to read lineupSlotId / slotPositionId and lineupSlot safely.
    """
    sid = getattr(p, "lineupSlotId", None)
    sname = (getattr(p, "lineupSlot", "") or "").upper()
    if sid is None:
        # best-effort mapping from the name if id missing
        for k, v in SLOT_NAME_TO_ID.items():
            if k in sname:
                sid = v
                break
    return int(sid) if sid is not None else 20, sname or "BE"


def get_my_boxscore(league, team_id: int, week: int):
    for bs in league.box_scores(week):
        if bs.home_team.team_id == team_id:
            return bs, "home"
        if bs.away_team.team_id == team_id:
            return bs, "away"
    raise RuntimeError(f"Team {team_id} not found in box scores for week {week}")



def build_projections_week_map(league, team, week: int):

    '''
    We have to get the player values from boxscore (that's where the week by week
    projected values are held - kinda a pain not directly assigned to players,
    but I didn't make the API...), so we loop thorugh the mathcups, it's a total pain,
    get our boscore in get_my_boscore and then down we go. 
    We create a data structure that has allt the basic components we need to post
    to ESPN later on, but also, gives us what we need to make swaps, I.E...projections
    it's a little unweildy, but we will take get the projection by pid from the map of pid
    to projections form the boxcore...and we will then place that in the players data{} block in the data strucutre
    it's a hassle
    
    '''

    bs, side = get_my_boxscore(league, team.team_id, week)
    my_lineup = bs.home_lineup if side == "home" else bs.away_lineup

    #pid => projected points (from your lineup only)
    proj_by_pid = {
        int(s.playerId): float(s.projected_points)
        for s in (my_lineup or [])
        if getattr(s, "projected_points", None) is not None
    }

    data = {}
    for p in team.roster:
        pid   = int(p.playerId)
        sid   = getattr(p, "lineupSlotId", None)
        sname = (getattr(p, "lineupSlot", "") or "").upper()

        #we are gonna raise an error if this is missing via key error, otherwise we'd have huge issues
        proj = proj_by_pid[pid]  

        data[pid] = {
            "playerId": pid,
            "name": getattr(p, "name", "Unknown"),
            "position": getattr(p, "position", "UNK"),
            "slot": sname or "BE",
            "slot_id": int(sid) if sid is not None else 20,
            "proj": proj,
        }
    return data



def main():
    swid = os.getenv("SWID", "").strip()  # member ID (with braces!)
    league = get_league()
    # print(league)

    # for team in league.teams:
    #     print(f"Team Name {team.team_name} + Team ID: {team.team_id}")



    team = next((t for t in league.teams if t.team_id == TEAM_ID), None)
    if not team:
        raise RuntimeError(f"TEAM_ID {TEAM_ID} not found in this league.")

    # Build a {playerId: projected_points} map for the week
    # proj_map = build_week_proj_map(league, WEEK)

    player_map = build_projections_week_map(league, team, WEEK)
    print("\n--- Full Roster (player_map) ---")
    print(f"{'Name':<25} {'Pos':<4} {'PlayerID':<8} {'SlotID':<6} {'Slot':<8} {'Proj(Wk)':>10}")
    for pid, info in sorted(player_map.items(), key=lambda kv: (-kv[1]["proj"], kv[1]["name"])):
        print(f"{info['name']:<25} {info['position']:<4} {info['playerId']:<8} {info['slot_id']:<6} {info['slot']:<8} {info['proj']:>10.2f}")

       # ok this is fantastic take this info and let's see if we can take a simple script that forces the transfer

    player_map = lineup_optimizer(player_map)  

    #one of those fantastic chatgpt generated print statements
    # print("\n--- Full Roster (player_map) ---")
    # print(f"{'Name':<25} {'Pos':<4} {'PlayerID':<8} {'SlotID':<6} {'Slot':<8} {'Proj(Wk)':>10}")
    # for pid, info in sorted(player_map.items(), key=lambda kv: (-kv[1]["proj"], kv[1]["name"])):
    #     print(f"{info['name']:<25} {info['position']:<4} {info['playerId']:<8} {info['slot_id']:<6} {info['slot']:<8} {info['proj']:>10.2f}")

        #ok this is fantastic take this info and let's see if we can take a simple script that forces the transfer


if __name__ == "__main__":
    main()



# CAN PROB JUST DO THIS FOR OVERLAY
# def build_player_week_map(league, team, week: int):
#     data = {}
#     # Baseline from roster
#     for p in getattr(team, "roster", []):
#         pid = int(p.playerId)
#         sid, sname = slot_info(p)
#         data[pid] = {
#             "playerId": pid,
#             "name": getattr(p, "name", "Unknown"),
#             "position": getattr(p, "position", "UNK"),
#             "slot": (sname or "BE"),
#             "slot_id": int(sid) if sid is not None else 20,
#             "proj": 0.0,
#         }

#     # Only overlay projections
#     def overlay_proj(lineup):
#         for slot in (lineup or []):
#             pid = int(getattr(slot, "playerId", -1))
#             if pid in data:
#                 proj = getattr(slot, "projected_points", None)
#                 if proj is not None:
#                     data[pid]["proj"] = float(proj)

#     for bs in league.box_scores(week):
#         overlay_proj(bs.home_lineup)
#         overlay_proj(bs.away_lineup)

#     return data






