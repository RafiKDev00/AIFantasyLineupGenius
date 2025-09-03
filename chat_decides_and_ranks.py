# B''SD
# chat_decides_and_moves.py
import os, json
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

if not os.getenv("GITHUB_ACTIONS"):  # local dev only etc
    load_dotenv(override=True)

'''
Strong Prompts below Set background (roleplay with AI), tell it 
Be very specific, and line about returnign only the JSON is key...we don't want to use extra tokens
on output we aren't using! We have a few different prompts at play...by convention
System/System_Prompt is the overarching command that informs GPT who it is, and what it's broad goal is.
Schema tells us what the output should look like exactly (and yes i had
gpt make up the format of the schema cause it's a pain to do so myself ) 

'''
SYSTEM = (
  "You are a fantasy football assistant manager. "
  "Given TEAM players with positions and eligibility, output rankings (best→worst) per position. "
  "Return ONLY JSON matching the schema. No commentary." 
)

#Output schema we mUse exactly your position keys. strict: true is an OPENAI convention
# that means we must have all these properties...
SCHEMA = {
  "name": "espn_rankings",
  "schema": {
    "type": "object",
    "properties": {
      "rankings": {
        "type": "object",
        "properties": {
          "QB":  {"type":"array","items":{"type":"integer"}},
          "RB":  {"type":"array","items":{"type":"integer"}},
          "WR":  {"type":"array","items":{"type":"integer"}},
          "TE":  {"type":"array","items":{"type":"integer"}},
          "K":   {"type":"array","items":{"type":"integer"}},
          "D/ST":{"type":"array","items":{"type":"integer"}}
        },
        "required": ["QB","RB","WR","TE","K","D/ST"],
        "additionalProperties": False
      }
    },
    "required": ["rankings"],
    "additionalProperties": False
  },
  "strict": True
}

# We are further reinforcing the results and to remember wehn you select and move players
#they need to be assinged these slot values, we "call the api" somewhatr iteratively so each
#time we hit him with the Promp_TPL so nothing bizarre happens and also with the rules
#we dont' want him benching everyone again
PROMPT_TPL = """SLOT IDS: QB=0, RB=2, WR=4, TE=6, D/ST=16, K=17, BENCH=20, IR=21, FLEX=23

RULES:
- Rank players by your football judgment; projections optional.
- For each position (QB/RB/WR/TE/K/D/ST) list ALL players of that position, best→worst.
- Use playerId integers only. No commentary.

TEAM JSON:
```json
{team_json}
```
"""

#Dict[Any, Dict[str, Any]] that's the structure of player_map as a refresh...
'''
Here we go through the player map and cut it down to what we actually need...In the form of team Json.
Notice how it makes it clear what spots everythign can go into?
why not do this earlier? Because i'm still messing with this code and I don't want to lose/forget
about variables I can use for another purpose
'''
def minimum_team_json(team: Dict[Any, Dict[str, Any]]):
  slim = {}
  for p in team.values() :
    slim[str(int(p["playerId"]))] = {
    "playerId": int(p["playerId"]),
    "name": p.get("name"),
    "position": p.get("position"),
    "eligible_slots": [int(s) for s in p.get("eligible_slots", [])],
    "lineup_slot_id": int(p.get("slot_id", 20)),
    }
  return json.dumps(slim, separators=(",",":"))


"""
"team" variable is the original player map Dict[Any, Dict[str, Any]]...we are gonna call the minumizer
below... chat_ranks_players is essentially the "driver", model is the model we are using
why 4o? cause it's gonna be cheaper...maybe we'll upgrade to 5o when I'm on a more final stage
and I'm not testing this left and right...5o shoudl be more updated and anaylitical, but we'll see!

"""
def chat_ranks_players(team , model: str = "gpt-4o-mini") -> Dict[str, List[int]]:
  api_key = os.getenv("OPENAI_API_KEY") # get that OpenAPI key, we overode it so it should work from github
  if not api_key:
    raise RuntimeError("Missing OPENAI_API_KEY")
  client = OpenAI(api_key=api_key) # we are accessign the software development kit of openAi..we are in

  #OK here we get everythign togethor
  '''
  user is a variable that represents the merginig of min_team_json into a string for prompt purposes.
  We also have those extra "rules" appended to it, ya know, to keep the gpt doing what we want
  ALSO
  why are we hitting completions API as opposed to one of the other openAI api's? because older model
  was boring single prompt which didn't give us flexibility to do what chat completions does...roleplay and a message
  now we can prime GPT and then ask it to  do what we want! There's also "responses" but that's more for integrating other
  data forms and such, and was higher level then what we need.
  '''
  user = PROMPT_TPL.format(team_json=minimum_team_json(team)) 
  resp = client.chat.completions.create( #make a post to OPen Ai completions api or model type was passed in
      model=model,
      temperature=0.4, #how creative we want it to be...this we should play with more
      response_format={"type":"json_schema","json_schema":SCHEMA}, #telling it how we want our response to be
      messages=[{"role":"system","content":SYSTEM}, {"role":"user","content":user}], #messages first we give it the broad system, who it is, and then we give it it's specifc material to work with plus a reminer
  )
  #because of strict = true and some of the other formattign magic...it will try until it get's an acceptable output
  msg = resp.choices[0].message # pick first response
  data = getattr(msg, "parsed", None) or json.loads(msg.content) #put everything into python dict that's usble for us
  return  data["rankings"] # return rankings...that's all we needed after all that