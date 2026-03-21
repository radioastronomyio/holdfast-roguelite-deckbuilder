# M3a Balance Analysis Report

**Seeds:** 5000  |  **Strategies:** aggressive, defensive, balanced

## 1. Executive Summary

**Win-rate band (40.0%–70.0%):** ✅ IN BAND

- ✅ **aggressive**: 47.4% (2370/5000) | avg regions 4.35 | avg turns 77.6
- ✅ **defensive**: 41.1% (2057/5000) | avg regions 4.17 | avg turns 112.8
- ✅ **balanced**: 50.2% (2508/5000) | avg regions 4.42 | avg turns 117.4

**Win-rate spread:** 9.0%

**Convergence warning:** YES

## 2. GDD Degenerate Signal Checklist

### Signal 1: Win Rate In Range

- aggressive: 47.4% → **PASS**
- defensive: 41.1% → **PASS**
- balanced: 50.2% → **PASS**

### Signal 2: Upgrade Path Pick Rate

- No upgrade data (no upgrade trees in game data) → **N/A**

### Signal 3: World Card Skip/Accept Rate

- **PASS** — no world card >90% auto-accept or auto-skip

### Signal 4: Speed Stat Ceiling

- Entities acting >3x/cycle: 12.3% of (entity,combat) pairs → **FAIL**
- Entities acting >5x/cycle: 9.8%
- Max observed ratio: 597.00
- Flagged combats: 16213

### Signal 5: Card Combo Win Rate

- **FAIL** — high win correlation cards: deep_focus_01 (3.052), power_surge_01 (-0.053)

## 3. Strategy Differentiation

- First-region agreement across strategies: 100.0%
- Full region-order agreement: 52.6%
- Seeds where all strategies agree (win or all lose): 54.6%
- Strategy-dependent seeds: 45.4%

**Pairwise win/loss agreement rate:**

| | aggressive | defensive | balanced |
|---|---|---|---|
| **aggressive** | 100.0% | 76.2% | 64.4% |
| **defensive** | 76.2% | 100.0% | 68.6% |
| **balanced** | 64.4% | 68.6% | 100.0% |

## 4. Card Balance

**Top 10 cards by win correlation:**

| Card | Win Corr | Plays/Campaign | Avg Damage/Play |
|------|----------|----------------|-----------------|
| deep_focus_01 | 3.0519 | 12.30 | 0.0 |
| power_surge_01 | -0.0534 | 0.20 | 0.0 |
| adrenaline_01 | -0.0658 | 0.22 | 0.0 |
| immolate_01 | -0.3265 | 1.01 | 0.0 |
| sweeping_blade_01 | -0.4459 | 10.92 | 45.5 |
| acid_flask_01 | -0.5225 | 2.14 | 0.0 |
| stone_wall_01 | -0.5373 | 1.53 | 0.0 |
| phalanx_01 | -0.7201 | 1.91 | 0.0 |
| drain_life_01 | -0.8224 | 2.18 | 7.4 |
| lightning_chain_01 | -0.8456 | 2.52 | 10.1 |

**Bottom 10 cards by win correlation:**

| Card | Win Corr | Plays/Campaign | Avg Damage/Play |
|------|----------|----------------|-----------------|
| acid_flask_01 | -0.5225 | 2.14 | 0.0 |
| stone_wall_01 | -0.5373 | 1.53 | 0.0 |
| phalanx_01 | -0.7201 | 1.91 | 0.0 |
| drain_life_01 | -0.8224 | 2.18 | 7.4 |
| lightning_chain_01 | -0.8456 | 2.52 | 10.1 |
| shield_bash_01 | -0.8808 | 2.07 | 4.9 |
| arcane_strike_01 | -1.1344 | 3.36 | 7.1 |
| heal_potion_01 | -4.1520 | 8.26 | 0.0 |
| frost_bolt_01 | -12.3237 | 225.96 | 17.1 |
| cleanse_01 | -17.0882 | 29.55 | 0.2 |

**Never-played cards:** none

## 5. Region Analysis

| Region Idx | Win Rate (given reached) | Death Rate | Ordering Freq |
|------------|--------------------------|------------|---------------|
| 0 | 46.2% | 1.4% | 100.0% |
| 1 | 46.9% | 10.4% | 98.6% |
| 2 | 52.4% | 10.8% | 88.2% |
| 3 | 59.7% | 11.9% | 77.4% |
| 4 | 70.5% | 10.3% | 65.6% |
| 5 | 83.6% | 9.1% | 55.3% |

**Difficulty curve (conditional win prob by region):**

| Region Idx | aggressive | defensive | balanced | Attrition |
|---|---|---|---|---|
| 0 | 47.4% | 41.1% | 50.2% | 1.4% |
| 1 | 48.2% | 41.7% | 50.8% | 10.4% |
| 2 | 54.0% | 47.0% | 56.2% | 10.8% |
| 3 | 61.0% | 54.3% | 63.8% | 11.9% |
| 4 | 71.3% | 65.5% | 74.4% | 10.3% |
| 5 | 83.5% | 80.4% | 86.6% | 9.1% |

## 6. World Card Economics

| Card | Accept Rate | Skip Rate | Accept (wins) | Accept (losses) |
|------|-------------|-----------|---------------|-----------------|
| martyrdom | 86.0% | 14.0% | 85.8% | 86.4% |
| vampiric_contract | 85.6% | 14.4% | 85.7% | 85.5% |
| barricaded | 85.3% | 14.7% | 85.7% | 84.3% |
| echo_chamber | 85.2% | 14.8% | 87.4% | 80.6% |
| heavy_armor | 85.0% | 15.0% | 85.1% | 84.9% |
| temporal_shift | 84.9% | 15.1% | 86.6% | 81.6% |
| forced_march | 84.8% | 15.2% | 86.4% | 81.7% |
| hyper_metabolism | 84.1% | 15.9% | 85.5% | 81.1% |
| scavengers_greed | 70.1% | 29.9% | 74.6% | 60.6% |
| rations_cut | 70.0% | 30.0% | 72.3% | 65.9% |
| leyline_tap | 70.0% | 30.0% | 72.2% | 66.1% |
| cursed_relic | 69.5% | 30.5% | 72.0% | 64.7% |
| unstable_mutagen | 58.7% | 41.3% | 57.9% | 60.1% |
| reckless_assault | 57.7% | 42.3% | 60.1% | 53.0% |
| tunnel_vision | 57.4% | 42.6% | 58.4% | 55.6% |
| pacifism_protocol | 44.4% | 55.6% | 45.8% | 41.9% |
| glass_cannon | 44.3% | 55.7% | 12.4% | 77.8% |
| overclocked | 44.3% | 55.7% | 45.7% | 41.7% |
| fog_of_war | 43.8% | 56.2% | 40.5% | 49.2% |
| blood_magic | 43.3% | 56.7% | 42.7% | 44.2% |

## 7. Speed System Health

- Mean action ratio: 2.302
- Max observed ratio: 597.000
- % entity-combats >3x: 12.3%
- % entity-combats >5x: 9.8%
- Flagged combats (any entity >3x): 16213

## 8. Seed Characterization

- Total seeds: 5000
- All-win seeds: 1228 (24.6%)
- All-loss seeds: 1502 (30.0%)
- Strategy-dependent seeds: 2270 (45.4%)
- Sample all-loss seeds: [5, 8, 11, 15, 17]
- Sample all-win seeds: [1, 4, 7, 9, 12]

## 9. Combat Health

- Mean combat duration: 12.9 turns
- Median combat duration: 6.0 turns
- P95 combat duration: 30.0 turns
- Turn-cap hit rate: 2.6%

**Turn-cap rate by region index:**

| Region Idx | Cap Rate |
|------------|----------|
| 0 | 0.4% |
| 1 | 1.0% |
| 2 | 1.6% |
| 3 | 2.5% |
| 4 | 3.0% |
| 5 | 3.6% |
| 6 | 3.7% |
| 7 | 4.3% |
| 8 | 4.2% |
| 9 | 3.9% |
| 10 | 3.5% |
| 11 | 4.5% |

- Aggregate damage dealt (all plays, display scale): 22175933
- Aggregate healing done (all plays, display scale): 2187385

## 10. Flagged Issues

1. [Signal 4] Speed dominance: 12.3% of entity-combats >3x
2. [Signal 5] Card win correlation: deep_focus_01 (3.052)
