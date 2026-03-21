# M3a Balance Analysis Report

**Seeds:** 5000  |  **Strategies:** aggressive, defensive, balanced

## 1. Executive Summary

**Win-rate band (40.0%–70.0%):** ✅ IN BAND

- ✅ **aggressive**: 49.9% (2495/5000) | avg regions 4.29 | avg turns 66.6
- ✅ **defensive**: 42.2% (2111/5000) | avg regions 4.17 | avg turns 52.2
- ✅ **balanced**: 51.3% (2563/5000) | avg regions 4.40 | avg turns 60.9

**Win-rate spread:** 9.0%

**Convergence warning:** YES

## 2. GDD Degenerate Signal Checklist

### Signal 1: Win Rate In Range

- aggressive: 49.9% → **PASS**
- defensive: 42.2% → **PASS**
- balanced: 51.3% → **PASS**

### Signal 2: Upgrade Path Pick Rate

- **FAIL** — dominant branches detected:
  - adrenaline_01: Branch B 100.0% in winning runs
  - phalanx_01: Branch A 97.2% in winning runs
  - stone_wall_01: Branch A 96.7% in winning runs
  - cleanse_01: Branch A 96.6% in winning runs
  - acid_flask_01: Branch A 97.1% in winning runs

### Signal 3: World Card Skip/Accept Rate

- **FAIL** — auto-accept/skip cards:
  - barricaded: accept 100.0%
  - martyrdom: accept 100.0%
  - vampiric_contract: accept 100.0%
  - heavy_armor: accept 100.0%
  - hyper_metabolism: accept 100.0%

### Signal 4: Speed Stat Ceiling

- Entities acting >3x/cycle: 7.4% of (entity,combat) pairs → **FAIL**
- Entities acting >5x/cycle: 5.0%
- Max observed ratio: 33.00
- Flagged combats: 11432

### Signal 5: Card Combo Win Rate

- **FAIL** — high win correlation cards: arcane_strike_01 (7.063), cleanse_01 (4.378)

## 3. Strategy Differentiation

- First-region agreement across strategies: 100.0%
- Full region-order agreement: 43.4%
- Seeds where all strategies agree (win or all lose): 46.3%
- Strategy-dependent seeds: 53.7%

**Pairwise win/loss agreement rate:**

| | aggressive | defensive | balanced |
|---|---|---|---|
| **aggressive** | 100.0% | 61.4% | 66.5% |
| **defensive** | 61.4% | 100.0% | 64.8% |
| **balanced** | 66.5% | 64.8% | 100.0% |

## 4. Card Balance

**Top 10 cards by win correlation:**

| Card | Win Corr | Plays/Campaign | Avg Damage/Play |
|------|----------|----------------|-----------------|
| arcane_strike_01 | 7.0632 | 60.50 | 27.3 |
| cleanse_01 | 4.3783 | 54.82 | 0.1 |
| frost_bolt_01 | 4.2077 | 42.49 | 24.9 |
| heal_potion_01 | 4.1859 | 55.13 | 0.1 |
| sweeping_blade_01 | 3.9373 | 38.85 | 31.4 |
| acid_flask_01 | 3.9030 | 40.66 | 0.1 |
| drain_life_01 | 3.6061 | 38.45 | 15.6 |
| shield_bash_01 | 3.5479 | 37.56 | 15.2 |
| phalanx_01 | 3.0694 | 36.03 | 0.1 |
| immolate_01 | 2.9081 | 36.98 | 0.1 |

**Bottom 10 cards by win correlation:**

| Card | Win Corr | Plays/Campaign | Avg Damage/Play |
|------|----------|----------------|-----------------|
| acid_flask_01 | 3.9030 | 40.66 | 0.1 |
| drain_life_01 | 3.6061 | 38.45 | 15.6 |
| shield_bash_01 | 3.5479 | 37.56 | 15.2 |
| phalanx_01 | 3.0694 | 36.03 | 0.1 |
| immolate_01 | 2.9081 | 36.98 | 0.1 |
| lightning_chain_01 | 1.5441 | 18.83 | 24.2 |
| deep_focus_01 | 1.3369 | 18.51 | 0.1 |
| power_surge_01 | 1.2929 | 18.56 | 0.1 |
| stone_wall_01 | 1.1490 | 18.49 | 0.1 |
| adrenaline_01 | 1.1049 | 18.79 | 0.1 |

**Never-played cards:** none

**Upgrade branch dominance:**

| Card | Branch A rate | Branch B rate | A win rate | B win rate |
|------|---------------|---------------|------------|------------|
| adrenaline_01 | 0.0% | 100.0% ⚠️ | 0.0% | 59.9% |
| power_surge_01 | 50.5% | 49.5% | 57.5% | 60.6% |
| deep_focus_01 | 46.4% | 53.6% | 53.5% | 59.8% |
| arcane_strike_01 | 47.8% | 52.2% | 54.0% | 58.1% |
| phalanx_01 | 97.2% ⚠️ | 2.8% | 58.6% | 91.9% |
| stone_wall_01 | 96.7% ⚠️ | 3.3% | 59.9% | 90.3% |
| cleanse_01 | 96.6% ⚠️ | 3.4% | 59.7% | 91.5% |
| acid_flask_01 | 97.1% ⚠️ | 2.9% | 58.6% | 89.7% |
| sweeping_blade_01 | 52.7% | 47.3% | 96.5% | 93.9% |
| immolate_01 | 52.2% | 47.8% | 96.7% | 88.2% |
| shield_bash_01 | 47.4% | 52.6% | 95.5% | 94.7% |
| lightning_chain_01 | 49.2% | 50.8% | 94.6% | 93.6% |
| drain_life_01 | 48.4% | 51.6% | 94.8% | 92.5% |
| frost_bolt_01 | 48.4% | 51.6% | 92.4% | 95.2% |
| heal_potion_01 | 48.4% | 51.6% | 89.9% | 91.7% |

## 5. Region Analysis

| Region Idx | Win Rate (given reached) | Death Rate | Ordering Freq |
|------------|--------------------------|------------|---------------|
| 0 | 47.8% | 4.9% | 100.0% |
| 1 | 50.2% | 9.6% | 95.1% |
| 2 | 55.9% | 9.0% | 85.5% |
| 3 | 62.4% | 9.8% | 76.5% |
| 4 | 71.6% | 9.8% | 66.8% |
| 5 | 83.9% | 9.2% | 57.0% |

**Difficulty curve (conditional win prob by region):**

| Region Idx | aggressive | defensive | balanced | Attrition |
|---|---|---|---|---|
| 0 | 49.9% | 42.2% | 51.3% | 4.9% |
| 1 | 53.9% | 43.4% | 53.6% | 9.6% |
| 2 | 59.2% | 49.2% | 59.2% | 9.0% |
| 3 | 65.4% | 56.2% | 65.5% | 9.8% |
| 4 | 73.8% | 65.9% | 74.7% | 9.8% |
| 5 | 86.2% | 79.8% | 85.3% | 9.2% |

## 6. World Card Economics

| Card | Accept Rate | Skip Rate | Accept (wins) | Accept (losses) |
|------|-------------|-----------|---------------|-----------------|
| barricaded | 100.0% ⚠️ | 0.0% | 100.0% | 100.0% |
| martyrdom | 100.0% ⚠️ | 0.0% | 100.0% | 100.0% |
| vampiric_contract | 100.0% ⚠️ | 0.0% | 100.0% | 100.0% |
| heavy_armor | 100.0% ⚠️ | 0.0% | 100.0% | 100.0% |
| hyper_metabolism | 100.0% ⚠️ | 0.0% | 100.0% | 100.0% |
| rations_cut | 85.2% | 14.8% | 86.7% | 82.1% |
| leyline_tap | 84.9% | 15.1% | 87.0% | 80.2% |
| forced_march | 84.8% | 15.2% | 87.4% | 79.0% |
| cursed_relic | 84.7% | 15.3% | 87.0% | 79.9% |
| temporal_shift | 84.5% | 15.5% | 86.0% | 81.8% |
| scavengers_greed | 84.3% | 15.7% | 87.0% | 77.9% |
| echo_chamber | 84.2% | 15.8% | 86.7% | 79.0% |
| unstable_mutagen | 73.7% | 26.3% | 73.2% | 74.8% |
| tunnel_vision | 58.0% | 42.0% | 58.6% | 57.0% |
| reckless_assault | 58.0% | 42.0% | 59.7% | 54.4% |
| glass_cannon | 28.4% | 71.6% | 6.4% | 58.8% |
| overclocked | 28.0% | 72.0% | 26.7% | 30.7% |
| blood_magic | 27.9% | 72.1% | 26.6% | 30.4% |
| fog_of_war | 27.8% | 72.2% | 25.0% | 33.1% |
| pacifism_protocol | 27.3% | 72.7% | 27.0% | 27.9% |

## 7. Speed System Health

- Mean action ratio: 0.673
- Max observed ratio: 33.000
- % entity-combats >3x: 7.4%
- % entity-combats >5x: 5.0%
- Flagged combats (any entity >3x): 11432

## 8. Seed Characterization

- Total seeds: 5000
- All-win seeds: 994 (19.9%)
- All-loss seeds: 1323 (26.5%)
- Strategy-dependent seeds: 2683 (53.7%)
- Sample all-loss seeds: [1, 5, 6, 8, 14]
- Sample all-win seeds: [3, 9, 20, 29, 41]

## 9. Combat Health

- Mean combat duration: 7.5 turns
- Median combat duration: 4.0 turns
- P95 combat duration: 14.0 turns
- Turn-cap hit rate: 1.2%

**Turn-cap rate by region index:**

| Region Idx | Cap Rate |
|------------|----------|
| 0 | 1.0% |
| 1 | 0.6% |
| 2 | 1.5% |
| 3 | 0.9% |
| 4 | 1.5% |
| 5 | 1.2% |
| 6 | 1.4% |
| 7 | 1.2% |
| 8 | 1.5% |
| 9 | 0.9% |
| 10 | 1.2% |
| 11 | 1.1% |

- Aggregate damage dealt (all plays, display scale): 27866207
- Aggregate healing done (all plays, display scale): 7858150

## 10. Flagged Issues

1. [Signal 2] adrenaline_01 Branch B dominance 100.0%
2. [Signal 2] phalanx_01 Branch A dominance 97.2%
3. [Signal 2] stone_wall_01 Branch A dominance 96.7%
4. [Signal 2] cleanse_01 Branch A dominance 96.6%
5. [Signal 2] acid_flask_01 Branch A dominance 97.1%
6. [Signal 3] barricaded auto-accept rate 100.0%
7. [Signal 3] martyrdom auto-accept rate 100.0%
8. [Signal 3] vampiric_contract auto-accept rate 100.0%
9. [Signal 3] heavy_armor auto-accept rate 100.0%
10. [Signal 3] hyper_metabolism auto-accept rate 100.0%
11. [Signal 4] Speed dominance: 7.4% of entity-combats >3x
12. [Signal 5] Card win correlation: arcane_strike_01 (7.063)
