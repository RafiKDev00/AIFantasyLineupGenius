

# B''SD
# main.py
import os
from dotenv import load_dotenv
from lineup_genius import lineup_optimizer
from espn_client import get_league
from build_player_data_structure import build_player_map_with_projections
from swapper import swapper_but_now_one_by_one


#configuration stuff


load_dotenv(override=True) # override so we reload the .env everytime
TEAM_NAME = os.getenv("TEAM_NAME")  #I'm not really using this value - but I would like to replace team ID with it, more user friendly
TEAM_ID = int(os.getenv("TEAM_ID"))

league = get_league() #get the league from espn client  - this used to be a variabel local inside the main method - but I pulled it out for clarity purposes
league.refresh() #refresh was recomended by to make sure we're up to date - I think overkill, but it's one line and better to be safe then sorrt
WEEK = league.current_week # Before we were hardcoding/baking the Week variable into our env, now it should live update everytime we get the code!
print(f"did we really get the correct {WEEK}")

def main():
    '''
    1) get all players on out team by looping throuhg league teams
        build_player_map_with_projections -> data struct with playres + projections
    2) create a data structure of commands from lineup_optimizer 
        (basically create the optimized lineup we want and the commands to send to swapper) 
    3) Swapper is be all end all - actually sends the Post to ESPN endpoints: it's output
        is a message (error or success) and a perfectly arragned lineup
    
    '''

    swid = os.getenv("SWID", "").strip()  # member ID (with braces!)

    team = next((t for t in league.teams if t.team_id == TEAM_ID), None) # find my team in the leauge based of team_ID could also do this with Team Name which may be easier for most people
    if not team:
        raise RuntimeError(f"TEAM_ID {TEAM_ID} not found in this league.") #thank you GPT for ideas for writing my error messages - no team no prob, fail fast & fail safe

    # Build a {playerId: projected_points} map for the week
    # proj_map = build_week_proj_map(league, WEEK)

    player_map =  build_player_map_with_projections(league, team, WEEK) #now we send to a different file, he'll take care of the rest
    
    print("\n--- Full Roster (player_map) ---") #this'll print out the team as is...more of a glorified check
    print(f"{'Name':<25} {'Pos':<4} {'PlayerID':<8} {'SlotID':<6} {'Slot':<8} {'Proj(Wk)':>10}")
    for pid, info in sorted(player_map.items(), key=lambda kv: (-kv[1]["proj"], kv[1]["name"])):
        print(f"{info['name']:<25} {info['position']:<4} {info['playerId']:<8} {info['slot_id']:<6} {info['slot']:<8} {info['proj']:>10.2f}")

    desired_moves = lineup_optimizer(player_map, WEEK)  # takes the players and projectionsgets the list of commands to send to swapper
    swapper_but_now_one_by_one(desired_moves, WEEK) #apply moves...which means send to the swapper, NOW found in main keeping in case it breaks


if __name__ == "__main__":
    main()

