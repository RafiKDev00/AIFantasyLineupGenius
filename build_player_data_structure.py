
# B''SD
# build_player_data_structure.py
import os
from dotenv import load_dotenv

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