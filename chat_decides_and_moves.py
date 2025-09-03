

# B''SD
# chat_decides_moves.py
from collections import defaultdict
from typing import Dict, Any, List

#We've used this before...outline very clearly what we need, where people go, etc.
SLOT_ID = {"QB":0, "RB":2, "WR":4, "TE":6, "D/ST":16, "K":17, "FLEX":23, "BE":20}
ROSTER_NEEDS = {"QB":1, "RB":2, "WR":2, "TE":1, "FLEX":1, "K":1, "D/ST":1}
FLEX_OK = {"RB","WR","TE"}
STARTER_SLOTS = [SLOT_ID["QB"], SLOT_ID["RB"], SLOT_ID["WR"], SLOT_ID["TE"], SLOT_ID["K"], SLOT_ID["D/ST"], SLOT_ID["FLEX"]]



def compute_best_lineup_from_rankings(player_map, rankings: Dict[str,  List[int]]) -> Dict[int, int]:
    """
    Use ChatGPT's per position rankings we generated in chat_decides_and_ranks, we returna. dict where the
    PID is matched where the player should go based off output...Dict[PID, SID], oh and taken is a variable to tell
    us that we've already used this player please don't do anything with him again
    """
    desired: Dict[int, int] = {}
    taken = set()

    def take_top(pos_key, need: int, slot_id: int): #pos key is like WR or TE, need is postion still ened to fill
        chosen = 0 #counting up to make sure we have the rgiht number
        for pid in rankings.get(pos_key, []):
            if pid in player_map and  player_map[pid]["position"] == pos_key and pid not in taken:
                desired[pid] = slot_id
                taken.add(pid)
                chosen += 1
                if chosen >= need:
                    break

    take_top("QB",ROSTER_NEEDS["QB"], SLOT_ID["QB"])
    take_top("TE",ROSTER_NEEDS["TE"],SLOT_ID["TE"])
    take_top("K",ROSTER_NEEDS["K"],SLOT_ID["K"])
    take_top("D/ST",ROSTER_NEEDS["D/ST"],SLOT_ID["D/ST"])
    take_top("RB",ROSTER_NEEDS["RB"],SLOT_ID["RB"])
    take_top("WR",ROSTER_NEEDS["WR"], SLOT_ID["WR"])

    #take FLEX from leftover RB,WR,TE in ranking order
    flex_pool: List[int] = []
    for pos in ("RB", "WR","TE"):
        for pid in rankings.get(pos, []):
            if pid in player_map and player_map[pid]["position"] == pos and pid not in taken:
                flex_pool.append(pid)
    for _ in range(ROSTER_NEEDS["FLEX"]): #I frickin love a good use of a wildcard, always feel like a genius, that and unpacking tuples returned from a method...gets me going
        if flex_pool:
            pid = flex_pool.pop(0)
            desired[pid] = SLOT_ID["FLEX"]
            taken.add(pid)

    #everyone else goes to the benchbench
    for pid in  player_map:
        if pid not in desired:
            desired[pid] = SLOT_ID["BE"]

    return desired

def plan_moves_sequential(player_map, desired) -> List[dict]:
    """
    the evolved form of our old lineup_genius. Takes Playermap and the desired dict generated above
    Makes us a list of commands (structured as dicts) which we can send to the swapper.
    TBH chat did most of the writing here. I gave it what I wanted it to do. It liked the idea
    of using sets because the math is faster and I defered. Basically I said switch around the players using the info we 
    already have to assure we are in the form needed to for swapper just like the old lineupgenius did,
    The conversation knew the code so well...and it returned exactly what I needed (I bet I could make it more efficient
    but I want to move on to adding tenserflow...I'm satisfied with the outputs and since it's not hitting the API
    it's not costing me...my purpose here was to A) get somethign that manages my fantasy team B) proves I know
    how to use the openAI api...I've done those 2 things. Adjusting what comes below is a fun side project...but 
    doing it now gets in the way of other goals. That's my guilty conffession. Toodles)
    """
    cur_by_slot = defaultdict(set)  # slot_id to set(pid)
    cur_slot_of: Dict[int, int] = {}
    for pid, info in player_map.items():
        s = int(info["slot_id"])
        cur_by_slot[s].add(pid)
        cur_slot_of[pid] = s

    want_by_slot = defaultdict(set)  # slot_id -> set(pid)
    for pid, want in desired.items():
        want_by_slot[int(want)].add(pid)

    moves: List[dict] = []

    # Step 1: vacate starters who shouldn't be there
    for slot in STARTER_SLOTS:
        for pid in list(cur_by_slot[slot] - want_by_slot[slot]):
            moves.append({
                "playerId": pid,
                "fromLineupSlotId": cur_slot_of[pid],
                "toLineupSlotId": SLOT_ID["BE"],
            })
            cur_by_slot[cur_slot_of[pid]].remove(pid)
            cur_by_slot[SLOT_ID["BE"]].add(pid)
            cur_slot_of[pid] = SLOT_ID["BE"]

    # Step 2: promote missing starters into their slots
    for slot in STARTER_SLOTS:
        for pid in list(want_by_slot[slot] - cur_by_slot[slot]):
            moves.append({
                "playerId": pid,
                "fromLineupSlotId": cur_slot_of[pid],  # could be 20/23/etc.
                "toLineupSlotId": slot,
            })
            cur_by_slot[cur_slot_of[pid]].discard(pid)
            cur_by_slot[slot].add(pid)
            cur_slot_of[pid] = slot

    # Final cleanup: no self-moves
    moves = [m for m in moves if m["fromLineupSlotId"] != m["toLineupSlotId"]]
    return moves




