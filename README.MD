# Lineup Genius

Your friends want you in the fantasy league, but you don't know anything about football? Liable to forget to set your lineup every week? Here's your solution! An ESPN Fantasy Football genius that automatically finds the **optimal weekly lineup** and sets it. Right now this is a cool proof of concept project, but it won't solve your issues. It won't add players if you're missing positions in a bye week, if you leave a lineup slot empty - it won't do anything about it (it only switches players, this will be the next update), and the code isn't connected to a server, it needs to be physcially run. It also only works if your team has the same makeup of positions as mine. So overall it's limited. However, what it does accomplish, is optimize your ESPN Fantasy Football lineup with a greedy algorithm just like you would, but remotely! This has already taken me way more time then it would have to just set my lineup every week, but for you, this will be faster. As I mentioned there is what to build upon, and I'm working on it, the 2025 season has yet to begin...

---

## Project Structure

| File / Folder         | Purpose |
|-----------------------|---------|
| `main.py`             | Entry point for running the script |
| `lineup_genius.py`    | Logic to build the best lineup based on projections |
| `espn_client.py`      | Handles fetching data from ESPN via the `espn-api` library |
| `credentials.json`    | Stores `SWID` and `espn_s2` cookies (ignored by Git) |
| `.env`                | Stores your secret tokens and league info (also ignored) |
| `requirements.txt`    | Python dependencies (so far just `espn-api`) |
| `.gitignore`          | Prevents secrets and system files from being tracked |
| `README.md`           | Meta. You're reading it :) |

---

## How to Find Your ESPN Credentials

1. **Login to [fantasy.espn.com](https://fantasy.espn.com)**
2. Open **DevTools → Application tab → Cookies**
3. Look for:
   - `SWID` (should look like `{A1B2C3D4-...}`)
   - `espn_s2` (long alphanumeric token)

4. Your **League ID** is in the URL when you're on your team homepage:
 - https://fantasy.espn.com/football/team?leagueId=1234567890
 - ^ the 1234567890 in this guy above


## Still to Update
- automatic lineup setting
- what if your league has different positions then mine
- Blank spots in lineup?
- Notifying if bye weeks/SID needs to be replaced/picking up players

## Disclaimers

- Works **only** for ESPN Fantasy Football 
- Don't mess around and do things that'll make other people angry
