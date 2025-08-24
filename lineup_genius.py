#B''SD
#lineupOptimizer.py

import os
from dotenv import load_dotenv
from urllib.parse import unquote
from espn_api.football import League
from swapper import swapper

def is_bench_slot( slot_label: str) -> bool:
    return slot_label in ("BE", "BN", "BENCH")

def is_WR_slot(slot_label: str, slot_id: int) -> bool:
    return slot_label == "WR" or slot_id == 4

def is_flex_slot(slot_label, slot_id) -> bool:
    return slot_label in ("W/R/T", "FLEX", "RB/WR/TE") or slot_id == 23

def optimize_qb_swaps(slot_label:str, slot_id: int)-> bool:
    return slot_label in ("QB") or slot_id == 0


def optimize_wr_swaps(player_map):
    """
    Replace starting WRs with higher-projected bench WRs (up to 2),
    calling `swapper` once per winning upgrade.
    Expects `is_bench_slot` and `is_WR_slot` to be defined.
    """
    starters = []  # [(pid, proj, slot_id, info)]
    bench = []     # [(pid, proj, slot_id, info)]

    for pid, info in player_map.items():
        slot_label = info["slot"]
        slot_id = info["slot_id"]
        proj = info["proj"]
        pos = info["position"]

        if is_WR_slot(slot_label, slot_id):
            starters.append((pid, proj, slot_id, info))
        elif is_bench_slot(slot_label) and pos == "WR":
            bench.append((pid, proj, slot_id, info))

    if not starters or not bench:
        return player_map

    # We want to replace the weakest starters with the strongest bench WRs
    starters.sort(key=lambda t: t[1])              # ascending by proj (weakest first)
    bench.sort(key=lambda t: t[1], reverse=True)   # descending by proj (strongest first)

    # Try up to two upgrades (zip handles fewer/more safely)
    for (s_pid, s_proj, s_slot_id, s_info), (b_pid, b_proj, b_slot_id, b_info) in zip(starters, bench):
        if b_proj > s_proj:
            # Keep your tuple shape: (pid, proj, slot_id, proj, info)
            to_bench  = (s_pid, s_proj, 4, s_proj, s_info)  # starter → to bench
            to_lineup = (b_pid, b_proj, 20, b_proj, b_info)  # bench → to lineup
            swapper(to_bench, to_lineup)
        else:
            # Best remaining bench WR can't beat this (or any stronger) starter
            break


def lineup_optimizer(player_map):

  """ 
  Ok basic strategy here, we have a dict of dicts, first level is 
  Key (player ID): a dict of player Values (player info), inside that dict 
  we have the position value. I would like to do this in O(n), and the good news
  is that the logic is simple. Basic greedy algorithm as we outlined in the 
  strategy file. We should need to do as many iterations through the lineup
  as there are positions (QB, TE, WR, RB, D/ST, K, + for flex). 
  We will then need to iterate through the sublists to find the best possible swaps,
  that kinda list and then iterating over smaller sublists could make this look like
  O(nlogn), but functionally these sublists are tiny, and anyway, I'm not unhappy with 
  an O(nlogn) complexity. 

  First step iterate and collect every player by position and then sort into sepperate dicts.
  I wanta  dict of all WR's to start. let's just do that as a test case, 

  then we'll take the best ones and only the essential details and send to be processed

  """


  #i'm just trying to swap the Flex with highest value person on the bench
  #start at none and sort through logic wille xist for both
 
  #testing because we had issues with the flex


  #DO the WR's first

# one at  a time brother
#   optimize_qb_swaps(player_map)

#   optimize_rb_swaps(player_map)

  optimize_wr_swaps(player_map)


 
  to_bench = None
  to_lineup = None
  for pid, info in player_map.items():
      if is_flex_slot(info["slot"], info["slot_id"]) or info["slot_id"] == 23:# "ok consistent error of not being able to access the flex, it seems we don't know how to properly naem it"
          to_bench = (pid, info["proj"], 23, info['proj'], info)
          break  #In my leauge at least there's only one flex, should put this in notes in my readme

  # here we ID all bench players save the guy that's both either a WR RB OR TE and has highest value'
  for pid, info in player_map.items():
      if is_bench_slot(info["slot"]) and info["position"] in {"RB", "WR", "TE"}:
          if to_lineup is None or info["proj"] > to_lineup[1]: # floating point comparison?
              to_lineup = (pid, info["proj"], 20, info['proj'], info)


  if to_bench[1] <= to_lineup[1]: #only send to the swapper if it's worth it!
      swapper(to_bench, to_lineup)

  return player_map

    

#  data[pid] = {
#             "playerId": pid,
#             "name": getattr(p, "name", "Unknown"),
#             "position": getattr(p, "position", "UNK"),
#             "slot": (sname or "BE"),
#             "slot_id": int(sid) if sid is not None else 20,
#             "proj": 0.0,
#         }

#this is what info has ^^
