# B''SD
# check_injury.py — the injury checker tool
#
# the idea: you hear on twitter your RB got hurt. you say "check injury PersonsName"
# and the proejct:
# 1) grabs ESPN's official injury status (which is laggy)
# 2) hits Google News RSS to find what Schefter, Rapoport, beat writers etc are
#    actually saying, giving us real intel 
# 3) figures out replacement moves from your bench (appropriate flex juggling and all that if we need it)
# 4) caches the moves so you can say "apply moves" and ... boom ... done
#
# Google News RSS tho? is server-rendered XML, with no API key, no auth, etc. , and it aggregates from all the
# sources we actually care about. tried other avenues not as good

import io
import re
from contextlib import redirect_stdout
from urllib.parse import quote_plus

from lineup_genius import compute_best_lineup
from chat_decides_and_moves import plan_moves_sequential
from mcp_server.server import mcp, _cache, _build_player_map, _get_context, _format_moves


def _search_injury_news(player_name):
    """search google news RSS for recent injury intel on a player.
    aggregates from ESPN, NFL.com, and articles that cite twitter insiders
    (Schefter, Rapoport, FantasyPros, Underdog, beat writers, etc.)
    returns up to 5 latest headlines+snippets. if it fails we just move on."""
    import requests

    query = quote_plus(f'"{player_name}" injury NFL')
    url = (
        f"https://news.google.com/rss/search?q={query}"
        f"&hl=en-US&gl=US&ceid=US:en"
    )
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        resp.raise_for_status()
    except Exception:
        return []

    xml = resp.text

    # parse the RSS items — each <item> has title, pubDate, source, description
    titles = re.findall(r"<title>(.*?)</title>", xml, re.DOTALL)
    pub_dates = re.findall(r"<pubDate>(.*?)</pubDate>", xml, re.DOTALL)
    sources = re.findall(r'<source[^>]*>(.*?)</source>', xml, re.DOTALL)
    descriptions = re.findall(r"<description>(.*?)</description>", xml, re.DOTALL)

    titles = titles[1:]  # first title is the feed title itself, skip it

    snippets = []
    for i, title in enumerate(titles[:5]):
        title_clean = re.sub(r"<[^>]+>", "", title).strip()
        source = sources[i].strip() if i < len(sources) else "Unknown"
        date = pub_dates[i].strip() if i < len(pub_dates) else ""
        date_short = date[:22] if date else ""  # trim to just day + time

        desc = ""
        if i < len(descriptions):
            desc = re.sub(r"<[^>]+>", " ", descriptions[i]).strip()
            desc = re.sub(r"\s+", " ", desc)
            if len(desc) > 200:  # don't need a novel
                desc = desc[:200] + "..."

        line = f"**{title_clean}** — _{source}, {date_short}_"
        if desc:
            line += f"\n   {desc}"
        snippets.append(line)

    return snippets


@mcp.tool()
def check_injury(player_name: str) -> str:
    """Check a player's injury status — pulls ESPN designation + latest news
    from Google News (Schefter, Rapoport, beat writers, etc).
    Suggests replacement moves if they're hurt. Say 'apply moves' to execute."""
    player_map, week = _build_player_map()
    _, team, _ = _get_context()

    # find the player by name — case insensitive partial match so you can
    # just type "mccaffrey" and it'll figure it out
    name_lower = player_name.lower()
    found_pid = None
    for pid, info in player_map.items():
        if name_lower in info["name"].lower():
            found_pid = pid
            break

    if found_pid is None:
        return f"Could not find **{player_name}** on your roster."

    info = player_map[found_pid]

    # grab ESPN injury data from the actual roster Player object
    # injuryStatus is like "QUESTIONABLE"/"OUT"/"DOUBTFUL", injured is a bool
    roster_player = None
    for p in team.roster:
        if int(p.playerId) == found_pid:
            roster_player = p
            break

    injury_status = getattr(roster_player, "injuryStatus", "ACTIVE") or "ACTIVE"
    injured = getattr(roster_player, "injured", False)
    pro_team = getattr(roster_player, "proTeam", "???")

    # search google news for the real scoop — ESPN status always lags behind
    news_snippets = _search_injury_news(info["name"])

    # the trick: copy the player map, zero out the injured guy's projection,
    # and re-run the greedy optimizer. it naturally benches them, shuffles
    # flex if needed, and promotes the best bench player. no custom logic needed
    sim_map = {pid: dict(pinfo) for pid, pinfo in player_map.items()}
    sim_map[found_pid]["proj"] = 0.0

    buf = io.StringIO()
    with redirect_stdout(buf):
        desired = compute_best_lineup(sim_map)
        moves = plan_moves_sequential(sim_map, desired)

    # cache moves so apply_moves works right away
    _cache["pending_moves"] = moves
    _cache["player_map"] = player_map

    # format it all up nice
    parts = [f"## Injury Check: {info['name']}\n"]
    parts.append(f"| Field | Value |")
    parts.append(f"|-------|-------|")
    parts.append(f"| Position | {info['position']} |")
    parts.append(f"| NFL Team | {pro_team} |")
    parts.append(f"| Current Slot | {info['slot']} |")
    parts.append(f"| ESPN Status | **{injury_status}** |")
    parts.append(f"| Injured Flag | {'Yes' if injured else 'No'} |")
    parts.append(f"| Projection | {info['proj']:.2f} |")

    parts.append(f"\n### Latest Injury News (via Google News)\n")
    parts.append("_Sourced from: Schefter, Rapoport, FantasyPros, beat writers, etc._\n")
    if news_snippets:
        for i, snippet in enumerate(news_snippets, 1):
            parts.append(f"{i}. {snippet}\n")
    else:
        parts.append("_No recent injury news found for this player._\n")

    parts.append(f"\n### Suggested Replacement Moves\n")
    parts.append(_format_moves(moves, player_map))

    if moves:
        parts.append('\n*Say "apply moves" to execute these on ESPN.*')

    return "\n".join(parts)
