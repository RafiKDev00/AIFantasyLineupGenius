# B''SD
# server.py .... the heart of the MCP server, FastMCP instance lives here
# every tool file imports from this to get mcp, the cache, helpers, etc.

import os
import io
from contextlib import redirect_stdout

from dotenv import load_dotenv
load_dotenv(override=True)

from mcp.server.fastmcp import FastMCP
from espn_client import get_league
from build_player_data_structure import build_player_map_with_projections

mcp = FastMCP("AIFantasyLineupGenius")

# slot id -> readable name...we've seen this map before across the codebase
SLOT_NAMES = {
    0: "QB", 2: "RB", 4: "WR", 6: "TE",
    16: "D/ST", 17: "K", 23: "FLEX", 20: "Bench", 21: "IR",
}

# shared state between tool calls — pending moves, player map, league context
# this is how we pass stuff between tools without re-fetching everything
_cache = {}


# helpers

def _get_context():
    """return (league, team, week) cached after first call...
    avoids hammering ESPN's API every single tool invocation"""
    if "league" not in _cache:
        buf = io.StringIO()
        with redirect_stdout(buf):  # suppress the print noise from espn_client
            league = get_league()
            league.refresh()
        team_id = int(os.getenv("TEAM_ID"))
        team = next((t for t in league.teams if t.team_id == team_id), None)
        if not team:
            raise RuntimeError(f"TEAM_ID {team_id} not found in league")
        _cache.update(league=league, team=team, week=league.current_week)
    return _cache["league"], _cache["team"], _cache["week"]


def _build_player_map():
    """builds the player map — same old build_player_map_with_projections
    but we capture stdout cause that code prints a bunch of stuff"""
    league, team, week = _get_context()
    buf = io.StringIO()
    with redirect_stdout(buf):
        player_map = build_player_map_with_projections(league, team, week)
    return player_map, week


def _format_moves(moves, player_map):
    """format moves as a readable list for the AI to show the user"""
    if not moves:
        return "No moves needed — your lineup is already optimal!"
    lines = [f"**{len(moves)} proposed move(s):**\n"]
    for m in moves:
        name = player_map[m["playerId"]]["name"]
        frm = SLOT_NAMES.get(m["fromLineupSlotId"], str(m["fromLineupSlotId"]))
        to = SLOT_NAMES.get(m["toLineupSlotId"], str(m["toLineupSlotId"]))
        lines.append(f"- **{name}**: {frm} → {to}")
    return "\n".join(lines)
