# B''SD
# chat_decides.py
import os
import json
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv


if not os.getenv("GITHUB_ACTIONS"):  # local dev bla bla bla you've seen this elsewhere
    load_dotenv(override=True)

OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY"))

# IDK...easier to reinclude this
SLOT = {
    "QB": 0, "RB": 2, "WR": 4, "TE": 6, "DST": 16, "K": 17,
    "BENCH": 20, "IR": 21, "FLEX": 23
}

#  Let GPT do the JSON schema building...way easier and frnaly safer
MOVE_SCHEMA = {
    "name": "espn_lineup_moves",
    "schema": {
        "type": "object",
        "properties": {
            "moves": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "playerId": {"type": "integer"},
                        "fromLineupSlotId": {"type": "integer"},
                        "toLineupSlotId": {"type": "integer"}
                    },
                    "required": ["playerId", "fromLineupSlotId", "toLineupSlotId"]
                }
            }
        },
        "required": ["moves"],
        "additionalProperties": False
    },
    "strict": True
}

'''
I thought this prompt was very thorough and yet...he continues to bench my team 
'''
SYSTEM_PROMPT = ( 
    "You are a fantasy football lineup assistant. "
    "Given a TEAM dict of players with current slots and eligible slots, "
    "propose an ordered list of ESPN LINEUP moves to improve the starting lineup.\n"
    "- You may use your general football knowledge and judgement about players; "
    "you do NOT need to rely on projections. \n"
    "- Only make legal moves: a player's toLineupSlotId must be in their eligible_slots "
    "(BENCH=20 is always allowed). Do not exceed slot counts implicitly: if the target slot is full, "
    "first bench a current starter from that slot, then promote your choice.\n"
    "- Prefer filling empty starter slots first (if any).\n"
    "- You must fill all starter spots - you cannot leave any open"
    "- There is always one starting QB, K, D/ST, FLEX, TE and 2 RB's and 2 WR "
    "- Never bench a starter unless you ALSO promote a bench  player into that same slot in this same answer."
    "- Prefer bench→starter moves. Standalone starter→bench moves are not allowed."
    "- Output ONLY JSON that matches the provided schema: {\"moves\": [...]}. "
    "No commentary."
)
# again let GPT write up this stuff
USER_PROMPT_TEMPLATE = """WEEK: {week}

SLOT IDS (for reference):
QB=0, RB=2, WR=4, TE=6, D/ST=16, K=17, BENCH=20, IR=21, FLEX=23

TEAM JSON:
```json
{team_json}
"""

def team_to_minimum_json(team):
    '''
    we're cutting down team TEAM to field the minimum structure we need for swaps
    each field in team has a : playerId, name, position, lineup_slot_id, eligible_slots, proj (optional).
    This is a glitch in my wider code schema....I have so many extra fields that I'm passing around, but its fine for now
    It's just a remnant of a different era when I had no idea what I actually needed to make swaps
    '''
    minimal = {}
    for pid, info in team.items():
    # allow keys as int or str; normalize to str key to reduce payload size churn
        minimal[str(int(info["playerId"]))] = {
        "playerId": int(info["playerId"]),
        "name": info.get("name"),
        "position": info.get("position"),
        "lineup_slot_id": int(info.get("lineup_slot_id", SLOT["BENCH"])),
        "eligible_slots": [int(s) for s in info.get("eligible_slots", [])],
        "proj": float(info.get("proj")) if info.get("proj") is not None else None,
        }
    return json.dumps(minimal, separators=(",", ":"))

def call_chat_gpt(team_json, week, model):
    '''
    Calls OpenAI with a strict and hopefully returns a list of moves dicts:
    [{playerId, fromLineupSlotId, toLineupSlotId}, ...]
    '''
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) #give it the key
    user_msg = USER_PROMPT_TEMPLATE.format(week=week, team_json=team_json)
    resp = client.chat.completions.create(
    model=model, # rn we giving it 4.0
    temperature=0.1, #IDK...do i want this being wild...lets play witht hsi
    response_format={"type": "json_schema", "json_schema": MOVE_SCHEMA},
    messages=[
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_msg},
    ],
    )

    #newer SDKs attach parsed dict - but otherwise well go back to JSON decoding content.
    message = resp.choices[0].message
    data = getattr(message, "parsed", None)
    if data is None:
        data = json.loads(message.content)
    return data.get("moves", [])


def validate_and_fix_moves(moves, team):
    """
    Look we have to check if we're feeding/benig fed crap/hallucinations... so here we 
    A) checl player exists
    B) check fromLineupSlotId matches our current view; if not, auto-correct to TEAM value
    C) checl toLineupSlotId is legal (eligible) or bench
    Invalid moves are dropped (to prevent the swapper from bugging and gltiching out the code).
    """
    index: Dict[int, Dict[str, Any]] = {}
    for k, v in team.items():
        index[int(v["playerId"])] = v
    cleaned = []
    for m in moves:
        pid = int(m.get("playerId"))
        fr = int(m.get("fromLineupSlotId"))
        to = int(m.get("toLineupSlotId"))

        info = index.get(pid)
        if not info:
            continue

        current = int(info.get("lineup_slot_id", SLOT["BENCH"]))
        eligible = set(int(s) for s in info.get("eligible_slots", [])) | {SLOT["BENCH"]}
        #correct bad 'from' if needed
        if fr != current:
            fr = current
        # drop illegal "move to"
        if to not in eligible:
            continue

        cleaned.append({"playerId": pid, "fromLineupSlotId": fr, "toLineupSlotId": to})
    return cleaned

def chat_decides(team, week, model:str = "gpt-4o-mini" ):
    '''
    Driverish thing...noticed we hard coded in gpt-4o-mini... returns a structure can be used by swapper. Team is a Dict[any, dict[str,any]] structure
    '''
    team_json = team_to_minimum_json(team)
    raw_moves = call_chat_gpt(team_json, week, model=model)
    return validate_and_fix_moves(raw_moves, team)