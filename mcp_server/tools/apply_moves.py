# B''SD
# apply_moves.py — the one that actually talks to ESPN and makes the swaps happen
# you gotta call optimize_lineup or ai_rank_lineup or check_injury first
# to generate the moves...then this guy executes them

import io
from contextlib import redirect_stdout

from swapper import swapper_but_now_one_by_one
from mcp_server.server import mcp, _cache, _get_context, _format_moves


@mcp.tool()
def apply_moves() -> str:
    """Executes the most recently proposed lineup moves on ESPN,
    runs optimize_lineup or ai_rank_lineup first to generate moves."""
    moves = _cache.get("pending_moves")
    if moves is None:
        return "No pending moves. Run `optimize_lineup` or `ai_rank_lineup` first."
    if not moves:
        return "No moves needed — lineup is already optimal."

    _, _, week = _get_context()
    player_map = _cache.get("player_map", {})

    buf = io.StringIO()
    with redirect_stdout(buf):  # swapper prints a ton of stuff
        swapper_but_now_one_by_one(moves, week)
    log = buf.getvalue()

    _cache.pop("pending_moves", None)  # clear em out so we don't accidentally re-run

    parts = [f"## Moves Applied (Week {week})\n"]
    parts.append(f"Executed **{len(moves)}** move(s) on ESPN.\n")
    parts.append(_format_moves(moves, player_map))
    parts.append(f"\n### ESPN Response Log\n```\n{log.strip()}\n```")
    return "\n".join(parts)
