# B''SD
# lineup_genius.py
from collections import defaultdict
from swapper import swapper_but_now_one_by_one
import os
from dotenv import load_dotenv

'''
This method was born out of a realization that trying to optimize by finding the best
and swapping got some nasty edge cases, easier to find the optimal switches before messing
with espn, otherwise too easy to get collisions and such. ALSO, this formats it PERFECTLY
for setting it up to have GPT set the lineup. Just saying.

'''
# We will have a server that'll track the week "automatically", but for now hardcoded

WEEK = int(os.getenv("WEEK"))# We will have a server that'll track the week "automatically", but for now hardcoded

SLOT_ID = {"QB":0, "RB":2, "WR":4, "TE":6, "D/ST":16, "K":17, "FLEX":23, "BE":20} #we've seen this list before
ROSTER_NEEDS = {"QB":1, "RB":2, "WR":2, "TE":1, "FLEX":1, "K":1, "D/ST":1} # how many positions there are to fill
FLEX_OK = {"RB","WR","TE"} #who can be in flex
STARTER_SLOTS = [SLOT_ID["QB"], SLOT_ID["RB"], SLOT_ID["WR"], SLOT_ID["TE"],
                 SLOT_ID["K"], SLOT_ID["D/ST"], SLOT_ID["FLEX"]]
# ya starter slot ID's
#there's a LOT of mapping going on here

def compute_best_lineup(player_map):
    '''Use a greedy algorithm to create the optimal roster/fill slots, the best remaining rb/wr/ ===> FLEX'''
    by_pos = {} #list of PIDS and proj's by position...thanks GPT for a smart way to organize this btw
    for pid, info in player_map.items():
        by_pos.setdefault(info["position"], []).append((pid, info["proj"])) 
    for lst in by_pos.values():
        lst.sort(key=lambda x: x[1], reverse=True)

    desired = {}
    def take_top(pos, n, slot_id):     #here we go...we harvest the top postion for each slot and put itas desired for position
        for pid, _ in by_pos.get(pos, [])[:n]:
            desired[pid] = slot_id

    take_top("QB",   ROSTER_NEEDS["QB"],   SLOT_ID["QB"])   #call this repititvelt
    take_top("TE",   ROSTER_NEEDS["TE"],   SLOT_ID["TE"])
    take_top("K",    ROSTER_NEEDS["K"],    SLOT_ID["K"])
    take_top("D/ST", ROSTER_NEEDS["D/ST"], SLOT_ID["D/ST"])
    take_top("RB",   ROSTER_NEEDS["RB"],   SLOT_ID["RB"])
    take_top("WR",   ROSTER_NEEDS["WR"],   SLOT_ID["WR"])

    flex_pool = [] #like deadpool but nothing like deadpool...remaining players in desired are elligible for flex and now we will proceed to put them ehre and find the best
    for pos in FLEX_OK:      #the flex is the reaming highest player...so we sort through who's left that's not in desired AND we check they're eligible to flex ofc
        for pid, proj in by_pos.get(pos, []):
            if pid not in desired:
                flex_pool.append((pid, proj))
    flex_pool.sort(key=lambda x: x[1], reverse=True)
    for i in range(ROSTER_NEEDS["FLEX"]):
        if i <len(flex_pool):
            desired[flex_pool[i][0]] = SLOT_ID["FLEX"]

    for pid in player_map:    #everyone else...takes a seat on the bench
        if pid not in desired:
            desired[pid] = SLOT_ID["BE"]
    return desired

def plan_moves_sequential(player_map, desired):
    ''' 
    Build single player LINEUP moves in a lineup like order
    Step one -> vacate the starters who shouldn't be there to the bench
    and the Two --> raise desired players into target slots
    '''

    cur_by_slot = defaultdict(set) #yeahhhhh  slot_id -> set(pid) currently there
    cur_slot_of = {}   # pid => current slot_id
    for pid, info in player_map.items():
        s = int(info["slot_id"]) #s is a holder value a.k.a the slot though
        cur_by_slot[s].add(pid)
        cur_slot_of[pid] = s

    want_by_slot = defaultdict(set)     #slot_id ==> set(pid) that should be there
    for pid, want in desired.items():
        want_by_slot[int(want)].add(pid)

    moves = []     #this is an ordered list of moves to execute ... no more collisions at the end points
    # vacate!
    for slot in STARTER_SLOTS: #strep up iteratet through...also it's nice what we're doing is essentially building the POST commanf
        #you'll see these same fields being used in the swapper down the road
        for pid in list(cur_by_slot[slot] - want_by_slot[slot]):
            moves.append({
                "playerId": pid,
                "fromLineupSlotId": cur_slot_of[pid],
                "toLineupSlotId": SLOT_ID["BE"],
            })
            cur_by_slot[cur_slot_of[pid]].remove(pid)
            cur_by_slot[SLOT_ID["BE"]].add(pid)
            cur_slot_of[pid] = SLOT_ID["BE"]
    # move to lineup! Same exact idea as above...just going the other way
    for slot in STARTER_SLOTS:
        for pid in list(want_by_slot[slot] - cur_by_slot[slot]):
            moves.append({
                "playerId": pid,
                "fromLineupSlotId": cur_slot_of[pid],  # could be 20 or 23, etc.
                "toLineupSlotId": slot,
            })
            cur_by_slot[cur_slot_of[pid]].discard(pid)
            cur_by_slot[slot].add(pid)
            cur_slot_of[pid] = slot

    moves = [m for m in moves if m["fromLineupSlotId"] != m["toLineupSlotId"]] # A last check to make sure no collisons...probably redundant but better safe then sorry
    return moves

def lineup_optimizer(player_map, WEEK ):
    desired = compute_best_lineup(player_map) #this calls the above...
    cur_total = sum(info["proj"] for info in player_map.values() if info["slot_id"] != SLOT_ID["BE"]) # calculates what our lineup currently would be from the old "player map"
    new_total = sum(player_map[pid]["proj"] for pid, slot in desired.items() if slot != SLOT_ID["BE"]) #
    print(f"Projected starters total: current={cur_total:.2f} -> desired={new_total:.2f}") # How much better can we do? thank you GPT again for fantastic print statemetns

    moves = plan_moves_sequential(player_map, desired) #ok great now make it better
    print(f"Planned moves: {len(moves)}")
    swapper_but_now_one_by_one(moves, WEEK) #apply moves...which means send to the swapper
    return desired
