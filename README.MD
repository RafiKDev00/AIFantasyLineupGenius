# Lineup Genius

An ESPN Fantasy Football bot that automatically finds the **optimal weekly lineup** for your team based on projected points.

---

## Project Structure

| File / Folder         | Purpose |
|-----------------------|---------|
| `main.py`             | Entry point for running the script |
| `lineup_genius.py`    | Logic to build the best lineup based on projections |
| `espn_client.py`      | Handles fetching data from ESPN via the `espn-api` library |
| `credentials.json`    | Stores `SWID` and `espn_s2` cookies (⚠️ ignored by Git) |
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

## Disclaimers

- Works **only** for ESPN Fantasy Football 
- Don't mess around and do things that'll make other people angry