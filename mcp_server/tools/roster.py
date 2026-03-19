# B''SD
# roster.py — shows your full ESPN roster with projections
# pretty straightforward, just builds the player map and formats it nice

from mcp_server.server import mcp, _build_player_map


@mcp.tool()
def get_roster() -> str:
    """shows full ESPN fantasy football roster with projections for curr week."""
    player_map, week = _build_player_map()

    starters = []
    bench = []
    for pid, info in sorted(
        player_map.items(), key=lambda kv: (-kv[1]["proj"], kv[1]["name"])
    ):
        row = f"| {info['name']} | {info['position']} | {info['slot']} | {info['proj']:.2f} |"
        if info["slot_id"] == 20:  # 20 is bench
            bench.append(row)
        else:
            starters.append(row)

    header = "| Name | Pos | Slot | Projected |\n|------|-----|------|-----------|"
    parts = [f"## Week {week} Roster\n"]
    parts.append(f"### Starters\n{header}\n" + "\n".join(starters))
    parts.append(f"\n### Bench\n{header}\n" + "\n".join(bench))

    starter_total = sum(
        info["proj"] for info in player_map.values() if info["slot_id"] != 20
    )
    parts.append(f"\n**Projected starter total: {starter_total:.2f}**")
    return "\n".join(parts)
