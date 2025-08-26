# Lineup Genius

Your friends want you in the fantasy league, but you don't know anything about football? Liable to forget to set your lineup every week? Here's your solution! An ESPN Fantasy Football genius that automatically finds the **optimal weekly lineup** and sets it. It's fairly involved to set this up (we're working on it), so check the ***Find Your ESPN Credentials + Set Up*** section below for instructions on what you need to do. *Disclaimer* This code only works if your team has the same makeup of positions as mine - but looking to fix that. *Coming soon* We're working on functionality for it to add/drop players, and maybe also link it up with ChatGPT's API so it AI can manage your lineup, and  maybe even make trades. Nonetheless, as of now now, this code can optimize your ESPN Fantasy Football lineup with a greedy algorithm, just like you would, but remotely and automamously! This has already taken me way more time then it would have to just set my lineup every week, but for you, this will be faster. As I mentioned there is what to build upon, and I'm working on it, the 2025 season has yet to begin...

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
| `.env`                | Stores your secret tokens and league info (also ignored) |
| `requirements.txt`    | Python dependencies (so far just `espn-api`) |
| `.gitignore`          | Prevents secrets and system files from being tracked |
| `strategyForFullLineupOptimizer.txt`| A little more in depth then the readme about the codes algorithm
| `README.md`           | Meta. You're reading it :) |

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

   #follow prompts, choose your repo, give "repo" scope
   gh auth login

   #Load your local .env into the current shell
   set -a; source .env; set +a

   #Choose exactly which keys to upload
   keys=(YEAR LEAGUE_ID TEAM_ID SWID ESPN_S2 SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASS ALERT_TO LEAGUE_NAME)

   #Create/update each secret from the env var of the same name
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

    


## Still to Make
- automatic lineup setting (using server)
- what if your league has different positions then mine
- Notify if replaced/picking up players
- Connect with ChatGPT
- manage pick ups and drops and even trades?
- Front end for easier use
- Verify you need to be logged in on a device to use this...I don't think this can break through Disneys password authentication...and maybe it shouldn't
- NOTE TO SELF: make sure week is correct when week 2 happens...

## Disclaimers

- Works **only** for ESPN Fantasy Football 
- Don't mess around and do things that'll make other people angry
