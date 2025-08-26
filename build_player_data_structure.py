
# B''SD
# build_player_data_structure.py
import os
from dotenv import load_dotenv

#configuration stuff
TEAM_NAME = "RafiSquared"  # this will change when we've drafted and can use regualr team name


load_dotenv(override=True) # override so we reload the .env everytime
TEAM_ID = int(os.getenv("TEAM_ID"))

SLOT_NAME_TO_ID = { #backup slot id's
    "QB": 0, "RB": 2, "WR": 4, "TE": 6, "D/ST": 16, "K": 17,
    "W/R/T": 23, "FLEX": 23, "RB/WR/TE": 23, "BE": 20, "BN": 20, "BENCH": 20, "IR": 21
}


def slot_info(p):
    """
    Return (slot_id (int), slot_label (UPPER)) for a roster player,
   tries to read lineupSlotId / slotPositionId and lineupSlot safely.
    """
    sid = getattr(p,  "lineupSlotId", None)
    sname = (getattr(p, "lineupSlot", "") or "").upper()
    if sid is None:
        #best effort mapping from the name if id missing
        for k, v in SLOT_NAME_TO_ID.items():
            if k in sname:
                sid = v
                break
    return int(sid) if sid is not None else 20, sname or "BE"


def get_my_boxscore(league, team_id: int, week: int): #

    for bs in league.box_scores(week):
        if bs.home_team.team_id == team_id:
            return bs,"home"
        if bs.away_team.team_id == team_id:
            return bs, "away"
    raise RuntimeError(f"Team {team_id} not found in box scores for week {week}")




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

def build_player_map_with_projections(league, team, week: int):
    # get my personal box score - before hand we were literally looping through every player in the leauges pid it was a messs
    box_score = next(
        (matchup for matchup in league.box_scores(week)
         if matchup.home_team.team_id ==  team.team_id or matchup.away_team.team_id == team.team_id),
        None
    )
    if box_score is None:
        raise RuntimeError(f"my team {team.team_id} wasn't in the {week}'s boxscore!?!")

    my_lineup = (box_score.home_lineup if box_score.home_team.team_id == team.team_id else box_score.away_lineup) or [] #ok here we go, get my specific lineup out of the boxscore

    # build indices from the box score - gets us bothn the projections and slots 
    proj_by_pid = {}
    slot_by_pid = {}
    for slot in my_lineup:
        pid = getattr(slot, "playerId", None) #get player id from slot
        if pid is None: 
            continue
        pid = int(pid) #make pid into an int
        if getattr(slot, "projected_points", None) is not None:   
            proj_by_pid[pid] = float(slot.projected_points)   #get projected points and assign to player
        sid = getattr(slot, "lineupSlotId", None)  #lineupslot id so for QB that's 0 and WR i believe is 4
        sname = (getattr(slot, "lineupSlot", "") or "").upper()  #position name so this is like QB or WR...
        slot_by_pid[pid] = (sid if sid is not None else None, sname or None)  # organize all the slots with pids of those players

    data, missing = {}, []
    for p in team.roster:
        pid = int(p.playerId)

        # Prefer box-score slot, fall back with roster, finally map label ---> id tbh could be an overkill maybe we can just start with mapping
        sid_box, sname_box = slot_by_pid.get(pid, (None, None))  # From box score index get player's (slot_id, slot_name); default to None
        sid_roster = getattr(p, "lineupSlotId", None) # try to get numeric slot slot from roster if couldn't get from boscore
        sname_roster= (getattr(p, "lineupSlot", "") or "").upper() #try to read label from roster if couldn't get from boxscore

        sname = (sname_box or sname_roster or "BE") #Yay we have a result
        if sid_box is not None:
            sid = int(sid_box) #set based off boxscore (our prefernce)
        elif sid_roster is not None:
            sid = int(sid_roster) #set based off roster our back up
        else:
            sid = SLOT_NAME_TO_ID.get(sname, 20)  #Map this bad boy based off the label we got from the roster...but if there isn't even one, we gotta default to 20 - which is bench

        proj = proj_by_pid.get(pid) #self explanatory use pid as a key to get the projection for that player (via id of course)
        if proj is None: #we'll try to get this from roster
            missing.append(getattr(p, "name", f"pid={pid}"))

        data[pid] = { #put it all togethor
            "playerId": pid,
            "name": getattr(p, "name", "Unknown"),
            "position": getattr(p, "position", "UNK"),
            "slot": sname,
            "slot_id": sid,
            "proj": proj,
        }

    if missing:
        raise RuntimeError("No projection in this week's box score for: " + ", ".join(missing))
    return data
