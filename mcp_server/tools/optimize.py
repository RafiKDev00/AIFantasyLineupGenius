# B''SD
# optimize.py — greedy lineup optimizer, uses projected points
# same compute_best_lineup we've been using since day 1

from lineup_genius import compute_best_lineup
from chat_decides_and_moves import plan_moves_sequential
from mcp_server.server import mcp, _cache, _build_player_map, _format_moves


@mcp.tool()
def optimize_lineup() -> str:
    """computes the best lineup using projected points via standard greedy algorithm).
    Shows proposed moves but does NOT apply them (cause we got the ai now). Call apply_moves to execute."""
    player_map, week = _build_player_map()

    desired = compute_best_lineup(player_map)
    moves = plan_moves_sequential(player_map, desired)

    _cache["pending_moves"] = moves  # stash for apply_moves
    _cache["player_map"] = player_map

    cur_total = sum(
        info["proj"] for info in player_map.values() if info["slot_id"] != 20
    )
    new_total = sum(
        player_map[pid]["proj"] for pid, slot in desired.items() if slot != 20
    )

    parts = [f"## Greedy Lineup Optimization (Week {week})\n"]
    parts.append(f"Current projected total: **{cur_total:.2f}**")
    parts.append(
        f"Optimized projected total: **{new_total:.2f}** ({new_total - cur_total:+.2f})\n"
    )
    parts.append(_format_moves(moves, player_map))
    parts.append('\n*Say "apply moves" to execute these on ESPN.*')
    return "\n".join(parts)
