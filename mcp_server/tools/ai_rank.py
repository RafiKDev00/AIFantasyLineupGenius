# B''SD
# ai_rank.py — the OpenAI powered version of lineup optimization
# instead of just using ESPN projections, we ask GPT to rank the players
# and then use those rankings to build the lineup...pretty cool honestly

from chat_decides_and_moves import (
    compute_best_lineup_from_rankings,
    plan_moves_sequential,
)
from mcp_server.server import mcp, _cache, _build_player_map, _format_moves


@mcp.tool()
def ai_rank_lineup(model: str = "gpt-4o-mini") -> str:
    """Uses OpenAI API to rank players and propose lineup moves.
    Requires OPENAI_API_KEY in .env. Shows proposed moves but doesn't apply.
    Call apply_moves to execute."""
    # deferred import so the server starts even without an OpenAI key
    from chat_decides_and_ranks import chat_ranks_players

    player_map, week = _build_player_map()

    rankings = chat_ranks_players(player_map, model=model)
    desired = compute_best_lineup_from_rankings(player_map, rankings)
    moves = plan_moves_sequential(player_map, desired)

    _cache["pending_moves"] = moves
    _cache["player_map"] = player_map

    cur_total = sum(
        info["proj"] for info in player_map.values() if info["slot_id"] != 20
    )
    new_total = sum(
        player_map[pid]["proj"] for pid, slot in desired.items() if slot != 20
    )

    parts = [f"## AI Lineup Optimization (Week {week}, model: {model})\n"]
    parts.append(f"Current projected total: **{cur_total:.2f}**")
    parts.append(
        f"AI-optimized projected total: **{new_total:.2f}** ({new_total - cur_total:+.2f})\n"
    )
    parts.append(_format_moves(moves, player_map))
    parts.append('\n*Say "apply moves" to execute these on ESPN.*')
    return "\n".join(parts)
