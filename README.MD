# Lineup Genius

Your friends want you in the fantasy league, but you don't know anything about football? Liable to forget to set your lineup every week? Here's your solution! An AI ESPN Fantasy Football genius that automatically finds the **optimal weekly lineup** and sets it. It's fairly involved to set this up (we're working on fixing that), so check the "***Find Your ESPN Credentials + Set Up***" section below for instructions on what you need to do. 

If you want to use the AI function from CHATGPT you'll need to purchase an API key (Hopefully we'll get a tenserflow based predictor up soon, and then you won't need to pay to add AI, but realistically I think that's dumb to try to harvest states...the hive mind of twitter which we will be tapping into, I think is a better model). Anyway if you don't want to pay for anything, use the free version that bases everything off ESPN's own projections! 

*Disclaimer* This code only works if your team has the same makeup of positions as mine - we are looking to improve that for the 2026 season. 

As of now now, this code can optimize your ESPN Fantasy Football lineup with a greedy algorithm, just like you would, or using openAI's api to make predictions, and it does all this both remotely and automamously! This has already taken me way more time then it would have to just set my lineup every week, but for you, this will be faster. As I mentioned there is what to build upon, and I'm working on it. This program will be in an even better shape for 2026 season then we were in 2025.

And How did we do in 2025? We came first in the regular season, finishing with 11 wins and 3 losses! We lost in the Semi Finals to end up taking 3rd place in the leauge. Dissapointing, but we Scored the second most points in the leauge as well 1750, with the first place (and most scoring) team scoring 1800, and the next most scoring (the fifth place team) at 1680. In the end a rash of injuries doomed the team, although the bot failed to pick up on them (as expected) and did not manage the lineup effectivcely afterward (this forced me to step in). We will need to improve the bots ability to understand injuries, which means adding a pre game time live internet search/ a twitter scrape.

I think the biggest take away is that the team ESPN projected to get the least wins, actually did the best in the regular season. We destroyed the algorithm, beating autodrafts predictions by a massive margin. In other words, we did way better then the default for an uninvolved player, hell... we almost won money.

Conclusion: It was a sucesfull trial run. Next season: live draft instead of manual querying, ~~injury detection (so it can manage bench even when there are injured players)~~ DONE, upgrade the model and model querying to track more live data ~~(maybe allow a pre game twitter scrape?)~~ DONE — see `check_injury` below. Let's see....

### What's New for 2026 !!!! 

**MCP Server** — You can now talk to the bot in plain English via Claude Desktop (or any MCP-compatible client). Ask it to check your roster, optimize your lineup, check injuries, etc. No more running scripts manually.

**Injury Detection** — The thing that killed us in 2025. `check_injury` pulls ESPN's official status AND searches Google News for what the insiders are actually saying (Schefter, Rapoport, beat writers — the real sources). it then figures out replacement moves from your bench, handles flex juggling, and caches the moves so you can apply them immediately. This was the numero uno thing we needed.

---

## Project Structure

| File / Folder         | Purpose |
|-----------------------|---------|
| `main.py`             | Entry point for running the script |
| `lineup_genius.py`    | Logic to build the best lineup based on projections |
| `espn_client.py`      | Handles fetching data from ESPN via the `espn-api` library |
| `swapper.py`          | Sends posts to ESPN endpoints, physically "does the swap" |
| `credentials.json`    | Stores `SWID`,`espn_s2`, and some leauge info cookies (ignored by Git) |
| `build_player_data_structure.py`| Returns a data structure that can be used to sort your team for swapping purposes |
| `.github/workflows/lineup.yml` | connects me to githubs server so it can run it once a day |
| `.env`                | Stores your secret tokens and league info (also ignored) |
| `requirements.txt`    | Python dependencies (so far just `espn-api`) |
| `.gitignore`          | Prevents secrets and system files from being tracked |
| `strategyForFullLineupOptimizer.txt`| A little more in depth then the readme about the codes algorithm|
| `chat_decides_and_ranks.py`| We hit the OpenAI api, and let it rank our players - i.e. who will play this Sunday|
| `chat_decides_and_moves.py`| Here we take chatGPT's ranks and use them to generate posts for the swapper to send|
| `mcp_server/`         | MCP server package — talk to the bot in plain English via Claude Desktop or any MCP client |
| `mcp_server/server.py`| FastMCP instance, shared cache, and helper functions |
| `mcp_server/tools/`   | One file per tool: `roster.py`, `optimize.py`, `ai_rank.py`, `apply_moves.py`, `check_injury.py` |
| `run_mcp.sh`          | Convenience script to launch the MCP server |
| `README.md`           | Meta. You're reading it :) |
| `Dockerfile`          | Why do I have a dockerfile, mostly to prove I can, but also could be useful for hosting on a real server (not just github) one day |

---

## How to Find Your ESPN Credentials + Set Up

1. **Login to [fantasy.espn.com](https://fantasy.espn.com)**
2. Open **DevTools → Application tab → Cookies**
3. Look for:
   - `SWID` (should look like `{A1B2C3D4-...}`)
   - `espn_s2` (long alphanumeric token)

4. Your **League ID** is in the URL when you're on your team homepage:
 - https://fantasy.espn.com/football/team?leagueId=1234567890
 - ^ the 1234567890 in this guy above

5. Go to the credentials or .env/example file and create a .env with all those fields

6. You are going to need an App Password - it's one of the .env fields - for the email notifier, so you have to your google acount, Turn on 2 Factor authentification, and make an app password titled "Mail" (no quotes), you put in in your .env with NO spaces",  I hate this for a variety of reasons, it adds a layer of weakness to your personal information and makes another annoying step
to setting this up, we will improve this. I personally created a dummy email to send this from...it's not attached to anything so if somehow someone gets into it, all they can do is use that email, and they get nothing of value about me,not even real name or birthday. We will find a better way going forward to do this.

5. Right now you need to "source venv/bin/activate" in command line to get your venv or this wont run, remember!

6. in order to run this remotely (on githubs server) you need to upload your secret variables from your personal .env (or you can run this randomly by yourself - but whats the point, that's not managing your team is it) here's what you do (for mac) - If you have any doubt how I did that, ask ChatGPT I learned from it...As for what this does, practically we set it so it'll run itself on githubs server with my personal info it'll access my personal code and use my personal hidden variables. I could otherwise run this locally, but then it isn't automated, which defeats most of the purpose.

         ```bash 
         # Follow prompts, choose your repo, give "repo" scope
         gh auth login  
         # Load your local .env into the current shell
         set -a; source .env; set +a

         # Choose exactly which keys to upload
         keys=(YEAR LEAGUE_ID TEAM_ID SWID ESPN_S2 SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASS ALERT_TO LEAGUE_NAME)

         # Create/update each secret from the env var of the same name
         for k in "${keys[@]}"; do
           v="${!k}"
           if [ -n "$v" ]; then
             echo "Setting secret $k"
             gh secret set "$k" -b"$v"
           else
             echo "Skipping $k (empty)"
           fi
         done

         # Verify
         gh secret list
    
7. docker run --rm lineup-genius:latest If choose to use Docker Image


## Still to Make
- what if your league has different positions then mine
- Notify if replaced/picking up players
- manage pick ups and drops and even trades?
- ~~Front end for easier use~~ MCP server + Claude Desktop is basically this now
- Verify you need to be logged in on a device to use this...I don't think this can break through Disneys password authentication...and maybe it shouldn't
- Live draft assistant


## Disclaimers

- Works **only** for ESPN Fantasy Football 
- Don't mess around and do things that'll make other people angry
