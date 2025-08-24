

# B''SD
# main.py
import os
from dotenv import load_dotenv
from lineup_genius import lineup_optimizer
from espn_client import get_league

#configuration stuff
TEAM_ID = 1  # this will change when we've drafted and can use regualr team name
WEEK = 1   # We will have a server that'll track the week "automatically", but for now hardcoded

load_dotenv(override=True) # override so we reload the .env everytime


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

def build_projections_week_map(league, team, week: int):
    """
    Returns:
      {
        playerId: {
          "playerId": int,
          "name": str,
          "position": str,
          "slot": str,       # current lineup slot label (e.g., 'WR', 'BE', 'FLEX')
          "slot_id": int,    # current lineup slot id (fallback to 20 = bench)
          "proj": float      # weekly projection (0.0 if not available)
        }, ...
      }
    """
    data = {}

    # 1) start from your team roster so everyone is present
    for p in getattr(team, "roster", []):
        pid = int(p.playerId)
        sid, sname = slot_info(p)  # your helper
        data[pid] = {
            "playerId": pid,
            "name": getattr(p, "name", "Unknown"),
            "position": getattr(p, "position", "UNK"),
            "slot": (sname or "BE"),
            "slot_id": int(sid) if sid is not None else 20,
            "proj": 0.0,
        }

    #2)add projections (and optionally fresher slot info) from box scores
    def overlay(lineup):
        for slot in (lineup or []):
            try:
                pid = int(getattr(slot, "playerId", -1))
            except Exception:
                continue
            if pid not in data:
                continue

            #projection
            proj = getattr(slot, "projected_points", None)
            if proj is not None:
                data[pid]["proj"] = float(proj)

            # slot/slot_id - if present in box score, refresh)  
            sid = getattr(slot, "lineupSlotId", None)
            sname = (getattr(slot, "lineupSlot", "") or "").upper()
            if sname:
                data[pid]["slot"] = sname
            if sid is not None:
                data[pid]["slot_id"] = int(sid)

            #def overkill pretttyyyy sure, I think what i thought needed backfilling was a bug on my end (emoji needed here)
            if data[pid]["name"] == "Unknown":
                data[pid]["name"] = getattr(slot, "name", data[pid]["name"])
            if data[pid]["position"] == "UNK":
                data[pid]["position"] = getattr(slot, "position", data[pid]["position"])

    for bs in league.box_scores(week):
        overlay(bs.home_lineup)
        overlay(bs.away_lineup)

    return data

def main():
    swid = os.getenv("SWID", "").strip()  # member ID (with braces!)
    league = get_league()

    team = next((t for t in league.teams if t.team_id == TEAM_ID), None)
    if not team:
        raise RuntimeError(f"TEAM_ID {TEAM_ID} not found in this league.")

    # Build a {playerId: projected_points} map for the week
    # proj_map = build_week_proj_map(league, WEEK)

    player_map = build_projections_week_map(league, team, WEEK)
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






