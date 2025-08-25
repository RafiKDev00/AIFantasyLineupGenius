

# B''SD
# main.py
import os
from dotenv import load_dotenv
from lineup_genius import lineup_optimizer
from espn_client import get_league
from build_player_data_structure import build_projections_week_map


#configuration stuff
TEAM_NAME = "RafiSquared"  # this will change when we've drafted and can use regualr team name
WEEK = 1   # We will have a server that'll track the week "automatically", but for now hardcoded

load_dotenv(override=True) # override so we reload the .env everytime
TEAM_ID = int(os.getenv("TEAM_ID"))


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






