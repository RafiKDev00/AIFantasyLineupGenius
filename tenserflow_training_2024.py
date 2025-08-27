# baseline_2024.py
#B''SD
# Deps (install if needed):
#   pip install nfl_data_py tensorflow scikit-learn pandas numpy

import os
import math
import pandas as pd
import numpy as np

import nfl_data_py as nfl
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

SEASON = 2024
POS_KEEP = {"RB","WR","TE"}  # focus on skill positions

def implied_points(total, spread, home):
    # For home team, implied = total/2 - spread/2; for away, implied = total/2 + spread/2 (spread = home - away)
    if pd.isna(total) or pd.isna(spread): return np.nan
    return total/2 - spread/2 if home else total/2 + spread/2

def safe_div(a, b):
    return float(a) / float(b) if b and b != 0 else 0.0

print("Loading 2024 weekly player stats…")
wk = nfl.import_weekly_data([SEASON], downcast=True)

off = wk[(wk["season_type"]=="REG") & (wk["position"].isin(POS_KEEP))].copy()

# Team totals per game to compute shares
team_totals = off.groupby(["season","week","team"]).agg(
    team_targets=("targets","sum"),
    team_rush_att=("rushing_attempts","sum"),
    team_air_yards=("air_yards","sum"),
    team_redzone_tgt=("redzone_targets","sum"),
).reset_index()
off = off.merge(team_totals, on=["season","week","team"], how="left")

# Shares
off["target_share"] = off.apply(lambda r: safe_div(r.get("targets",0), r.get("team_targets",0)), axis=1)
off["carry_share"]  = off.apply(lambda r: safe_div(r.get("rushing_attempts",0), r.get("team_rush_att",0)), axis=1)
off["ay_share"]     = off.apply(lambda r: safe_div(r.get("air_yards",0), r.get("team_air_yards",0)), axis=1)
off["rz_tgt_share"] = off.apply(lambda r: safe_div(r.get("redzone_targets",0), r.get("team_redzone_tgt",0)), axis=1)

# Snap share
print("Loading snap counts…")
snaps = nfl.import_snap_counts([SEASON])
snaps = snaps[snaps["season_type"]=="REG"][["season","week","team","player_id","offense_snaps","team_offense_snaps"]].copy()
snaps["snap_share"] = snaps.apply(lambda r: safe_div(r.get("offense_snaps",0), r.get("team_offense_snaps",0)), axis=1)
off = off.merge(snaps[["season","week","team","player_id","snap_share"]], on=["season","week","team","player_id"], how="left")

# Vegas lines → implied team points
print("Loading scoring lines…")
lines = nfl.import_sc_lines([SEASON])
lines = lines[lines["season_type"]=="REG"][["season","week","team","home_away","spread_line","total_line"]].copy()
lines["is_home"] = lines["home_away"].eq("home")
lines["implied_pts"] = lines.apply(lambda r: implied_points(r["total_line"], r["spread_line"], r["is_home"]), axis=1)
off = off.merge(lines[["season","week","team","implied_pts"]], on=["season","week","team"], how="left")

# Opponent aFPA vs position (rolling prev-3 weeks, no leakage)
print("Building opponent aFPA (rolling)…")
def build_afpa(df):
    by_pos = df.groupby(["season","week","opponent_team","position"]).agg(
        fpa=("fantasy_points_ppr","sum")
    ).reset_index().rename(columns={"opponent_team":"def_team"})
    by_pos = by_pos.sort_values(["def_team","position","week"])
    by_pos["fpa_prev3"] = by_pos.groupby(["def_team","position"])["fpa"].apply(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    return by_pos

afpa = build_afpa(off)
off = off.merge(
    afpa[["season","week","def_team","position","fpa_prev3"]],
    left_on=["season","week","opponent_team","position"],
    right_on=["season","week","def_team","position"],
    how="left"
).drop(columns=["def_team"])

# Team intent: PROE from PBP
print("Computing team PROE… (this can take a minute)")
pbp = nfl.import_pbp_data([SEASON], downcast=True, cache=True)
pbp_neutral = pbp[(pbp["season_type"]=="REG") &
                  (pbp["qtr"]<=4) &
                  (pbp["wp"].between(0.2,0.8)) &
                  (~pbp["no_play"])]

proe = pbp_neutral.groupby(["season","week","posteam"]).agg(
    pass_rate=("pass","mean"),
    xpass_rate=("xpass","mean")
).reset_index().rename(columns={"posteam":"team"})
proe["proe"] = proe["pass_rate"] - proe["xpass_rate"]
off = off.merge(proe[["season","week","team","proe"]], on=["season","week","team"], how="left")

# Injuries → simple flag
print("Loading injuries…")
inj = nfl.import_injuries([SEASON])[["season","week","team","gsis_id","report_status"]].copy()
ids_map = nfl.import_ids(ids=["gsis_id","nflverse_id"])
inj = inj.merge(ids_map[["gsis_id","nflverse_id"]], on="gsis_id", how="left")
inj["injury_flag"] = inj["report_status"].isin(["Questionable","Doubtful","Out"]).astype(int)
inj = inj.rename(columns={"nflverse_id":"player_id"})
off = off.merge(inj[["season","week","team","player_id","injury_flag"]], on=["season","week","team","player_id"], how="left")
off["injury_flag"] = off["injury_flag"].fillna(0)

# Pace proxy: simple team plays per game (coarse)
plays_pg = off.groupby(["season","week","team"]).agg(team_plays=("fantasy_points_ppr","count")).reset_index()
off = off.merge(plays_pg, on=["season","week","team"], how="left")

# Final feature frame
FEATURES = [
    "implied_pts",
    "target_share",
    "carry_share",
    "ay_share",
    "rz_tgt_share",
    "snap_share",
    "fpa_prev3",
    "proe",
    "team_plays",
]
LABEL = "fantasy_points_ppr"

df = off[["season","week","team","player_id","player_name","position","opponent_team", LABEL] + FEATURES].copy()
df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)

# Holdout split within 2024: train <=14, test >=15
train = df[df["week"] <= 14]
test  = df[df["week"] >= 15]

X_train = train[FEATURES].to_numpy(dtype=np.float32)
y_train = train[LABEL].to_numpy(dtype=np.float32)
X_test  = test[FEATURES].to_numpy(dtype=np.float32)
y_test  = test[LABEL].to_numpy(dtype=np.float32)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test  = scaler.transform(X_test)

# TensorFlow model
tf.random.set_seed(42)
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(len(FEATURES),)),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(1)
])
model.compile(optimizer="adam", loss="mae")
model.fit(X_train, y_train, validation_split=0.15, epochs=12, batch_size=256, verbose=0)

# Evaluate
pred = model.predict(X_test, verbose=0).reshape(-1)
mae = np.mean(np.abs(pred - y_test))

print("\n=== 2024 HOLDOUT (Weeks 15-18) ===")
print(f"Features used: {FEATURES}")
print(f"MAE (PPR points): {mae:.2f}")

# Attach predictions to rows and show biggest misses
out = test[["season","week","team","opponent_team","player_id","player_name","position", LABEL]].copy()
out["pred"] = pred
out["abs_err"] = (out["pred"] - out[LABEL]).abs()

print("\nTop 15 biggest misses:")
print(out.sort_values("abs_err", ascending=False).head(15)[
    ["week","player_name","team","position","fantasy_points_ppr","pred","abs_err"]
].to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

# Optional: compare to your current projections (CSV with: season,week,player_id,baseline_proj)
BASELINE_CSV = os.environ.get("BASELINE_PROJ_CSV","")
if BASELINE_CSV and os.path.exists(BASELINE_CSV):
    base = pd.read_csv(BASELINE_CSV)
    merged = out.merge(base, on=["season","week","player_id"], how="inner")
    m_mae = np.mean(np.abs(merged["pred"] - merged[LABEL]))
    b_mae = np.mean(np.abs(merged["baseline_proj"] - merged[LABEL]))
    print(f"\nBaseline file: {BASELINE_CSV}")
    print(f"MAE – Our TF model: {m_mae:.2f} | Your baseline: {b_mae:.2f} | Δ: {b_mae - m_mae:+.2f}")
    print("\nSample compare (10 rows):")
    print(merged.sample(min(10, len(merged)))[
        ["week","player_name","position", "fantasy_points_ppr","baseline_proj","pred"]
    ].to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
else:
    print("\nSet BASELINE_PROJ_CSV=/path/to/your.csv to print a direct comparison vs your current projections.")
