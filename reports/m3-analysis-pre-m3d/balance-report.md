# M3a Balance Analysis Report

**Seeds:** 5000  |  **Strategies:** aggressive, defensive, balanced

## 1. Executive Summary

**Win-rate band (40.0%–70.0%):** ❌ OUT OF BAND

- ❌ **aggressive**: 31.4% (1572/5000) | avg regions 3.74 | avg turns 61.2
- ✅ **defensive**: 42.7% (2136/5000) | avg regions 4.18 | avg turns 49.9
- ✅ **balanced**: 57.2% (2862/5000) | avg regions 4.58 | avg turns 54.4

**Win-rate spread:** 25.8%

**Convergence warning:** YES

## 2. GDD Degenerate Signal Checklist

### Signal 1: Win Rate In Range

- aggressive: 31.4% → **FAIL**
- defensive: 42.7% → **PASS**
- balanced: 57.2% → **PASS**

### Signal 2: Upgrade Path Pick Rate

- **FAIL** — dominant branches detected:
  - adrenaline_01: Branch B 100.0% in winning runs
  - power_surge_01: Branch A 100.0% in winning runs
  - immolate_01: Branch A 100.0% in winning runs
  - shield_bash_01: Branch A 100.0% in winning runs
  - phalanx_01: Branch A 100.0% in winning runs
  - cleanse_01: Branch A 100.0% in winning runs
  - acid_flask_01: Branch A 100.0% in winning runs
  - stone_wall_01: Branch A 100.0% in winning runs

### Signal 3: World Card Skip/Accept Rate

- **PASS** — no world card >90% auto-accept or auto-skip

### Signal 4: Speed Stat Ceiling

- Entities acting >3x/cycle: 5.1% of (entity,combat) pairs → **FAIL**
- Entities acting >5x/cycle: 3.5%
- Max observed ratio: 109.00
- Flagged combats: 7759

### Signal 5: Card Combo Win Rate

- **FAIL** — high win correlation cards: arcane_strike_01 (7.879), cleanse_01 (4.671)

## 3. Strategy Differentiation

- First-region agreement across strategies: 100.0%
- Full region-order agreement: 44.9%
- Seeds where all strategies agree (win or all lose): 48.7%
- Strategy-dependent seeds: 51.3%

**Pairwise win/loss agreement rate:**

| | aggressive | defensive | balanced |
|---|---|---|---|
| **aggressive** | 100.0% | 65.3% | 62.1% |
| **defensive** | 65.3% | 100.0% | 70.0% |
| **balanced** | 62.1% | 70.0% | 100.0% |

## 4. Card Balance

**Top 10 cards by win correlation:**

| Card | Win Corr | Plays/Campaign | Avg Damage/Play |
|------|----------|----------------|-----------------|
| arcane_strike_01 | 7.8787 | 53.72 | 32.2 |
| cleanse_01 | 4.6713 | 48.73 | 0.0 |
| frost_bolt_01 | 4.4378 | 38.02 | 24.8 |
| heal_potion_01 | 3.9570 | 49.68 | 0.0 |
| drain_life_01 | 3.9215 | 34.30 | 14.9 |
| sweeping_blade_01 | 3.6480 | 34.85 | 30.9 |
| acid_flask_01 | 3.5303 | 33.25 | 0.1 |
| shield_bash_01 | 3.1367 | 34.40 | 14.9 |
| immolate_01 | 2.9702 | 32.62 | 0.0 |
| phalanx_01 | 2.9449 | 32.12 | 0.0 |

**Bottom 10 cards by win correlation:**

| Card | Win Corr | Plays/Campaign | Avg Damage/Play |
|------|----------|----------------|-----------------|
| sweeping_blade_01 | 3.6480 | 34.85 | 30.9 |
| acid_flask_01 | 3.5303 | 33.25 | 0.1 |
| shield_bash_01 | 3.1367 | 34.40 | 14.9 |
| immolate_01 | 2.9702 | 32.62 | 0.0 |
| phalanx_01 | 2.9449 | 32.12 | 0.0 |
| lightning_chain_01 | 1.7832 | 16.46 | 24.3 |
| adrenaline_01 | 1.4471 | 16.41 | 0.1 |
| power_surge_01 | 1.3252 | 16.60 | 0.0 |
| stone_wall_01 | 1.3085 | 16.42 | 0.0 |
| deep_focus_01 | 1.2695 | 16.48 | 0.0 |

**Never-played cards:** none

**Upgrade branch dominance:**

| Card | Branch A rate | Branch B rate | A win rate | B win rate |
|------|---------------|---------------|------------|------------|
| arcane_strike_01 | 67.3% | 32.7% | 51.7% | 33.4% |
| adrenaline_01 | 0.0% | 100.0% ⚠️ | 0.0% | 48.6% |
| deep_focus_01 | 30.7% | 69.3% | 56.7% | 52.1% |
| power_surge_01 | 100.0% ⚠️ | 0.0% | 57.7% | 0.0% |
| immolate_01 | 100.0% ⚠️ | 0.0% | 75.4% | 0.0% |
| shield_bash_01 | 100.0% ⚠️ | 0.0% | 100.0% | 0.0% |
| phalanx_01 | 100.0% ⚠️ | 0.0% | 60.0% | 0.0% |
| cleanse_01 | 100.0% ⚠️ | 0.0% | 60.0% | 0.0% |
| acid_flask_01 | 100.0% ⚠️ | 0.0% | 71.7% | 0.0% |
| stone_wall_01 | 100.0% ⚠️ | 0.0% | 66.5% | 0.0% |

## 5. Region Analysis

| Region Idx | Win Rate (given reached) | Death Rate | Ordering Freq |
|------------|--------------------------|------------|---------------|
| 0 | 43.8% | 4.1% | 100.0% |
| 1 | 45.7% | 10.4% | 95.9% |
| 2 | 51.2% | 10.6% | 85.5% |
| 3 | 58.5% | 11.2% | 74.9% |
| 4 | 68.7% | 10.9% | 63.7% |
| 5 | 82.9% | 9.0% | 52.8% |

**Difficulty curve (conditional win prob by region):**

| Region Idx | aggressive | defensive | balanced | Attrition |
|---|---|---|---|---|
| 0 | 31.4% | 42.7% | 57.2% | 4.1% |
| 1 | 33.4% | 43.9% | 59.5% | 10.4% |
| 2 | 38.3% | 49.6% | 65.0% | 10.6% |
| 3 | 45.8% | 56.7% | 71.1% | 11.2% |
| 4 | 56.6% | 66.5% | 80.1% | 10.9% |
| 5 | 75.4% | 81.1% | 89.3% | 9.0% |

## 6. World Card Economics

| Card | Accept Rate | Skip Rate | Accept (wins) | Accept (losses) |
|------|-------------|-----------|---------------|-----------------|
| martyrdom | 86.9% | 13.1% | 90.2% | 80.8% |
| vampiric_contract | 86.8% | 13.2% | 90.1% | 81.2% |
| barricaded | 86.7% | 13.3% | 89.9% | 81.1% |
| hyper_metabolism | 86.5% | 13.5% | 89.9% | 80.3% |
| heavy_armor | 86.5% | 13.5% | 89.5% | 81.4% |
| echo_chamber | 84.7% | 15.3% | 86.2% | 81.8% |
| temporal_shift | 84.4% | 15.6% | 84.6% | 84.1% |
| forced_march | 84.0% | 16.0% | 85.9% | 80.5% |
| rations_cut | 71.5% | 28.5% | 75.9% | 63.6% |
| scavengers_greed | 71.5% | 28.5% | 76.9% | 61.5% |
| cursed_relic | 71.4% | 28.6% | 76.1% | 63.2% |
| leyline_tap | 71.1% | 28.9% | 76.0% | 62.6% |
| unstable_mutagen | 58.9% | 41.1% | 56.7% | 62.6% |
| reckless_assault | 55.8% | 44.2% | 52.6% | 61.3% |
| tunnel_vision | 55.7% | 44.3% | 52.5% | 61.2% |
| pacifism_protocol | 43.3% | 56.7% | 43.6% | 42.9% |
| glass_cannon | 42.5% | 57.5% | 11.1% | 75.8% |
| blood_magic | 42.3% | 57.7% | 41.2% | 44.3% |
| overclocked | 42.0% | 58.0% | 39.7% | 46.1% |
| fog_of_war | 41.9% | 58.1% | 38.8% | 47.0% |

## 7. Speed System Health

- Mean action ratio: 0.486
- Max observed ratio: 109.000
- % entity-combats >3x: 5.1%
- % entity-combats >5x: 3.5%
- Flagged combats (any entity >3x): 7759

## 8. Seed Characterization

- Total seeds: 5000
- All-win seeds: 887 (17.7%)
- All-loss seeds: 1550 (31.0%)
- Strategy-dependent seeds: 2563 (51.3%)
- Sample all-loss seeds: [2, 5, 6, 8, 9]
- Sample all-win seeds: [3, 7, 13, 14, 16]

## 9. Combat Health

- Mean combat duration: 7.1 turns
- Median combat duration: 4.0 turns
- P95 combat duration: 13.0 turns
- Turn-cap hit rate: 1.0%

**Turn-cap rate by region index:**

| Region Idx | Cap Rate |
|------------|----------|
| 0 | 1.0% |
| 1 | 0.5% |
| 2 | 1.3% |
| 3 | 1.0% |
| 4 | 1.2% |
| 5 | 1.1% |
| 6 | 1.2% |
| 7 | 0.9% |
| 8 | 1.3% |
| 9 | 0.8% |
| 10 | 1.0% |
| 11 | 0.5% |

- Aggregate damage dealt (all plays, display scale): 25907071
- Aggregate healing done (all plays, display scale): 7142598

## 10. Flagged Issues

1. [Signal 1] aggressive win rate 31.4% outside 40.0%–70.0%
2. [Signal 2] adrenaline_01 Branch B dominance 100.0%
3. [Signal 2] power_surge_01 Branch A dominance 100.0%
4. [Signal 2] immolate_01 Branch A dominance 100.0%
5. [Signal 2] shield_bash_01 Branch A dominance 100.0%
6. [Signal 2] phalanx_01 Branch A dominance 100.0%
7. [Signal 2] cleanse_01 Branch A dominance 100.0%
8. [Signal 2] acid_flask_01 Branch A dominance 100.0%
9. [Signal 2] stone_wall_01 Branch A dominance 100.0%
10. [Signal 4] Speed dominance: 5.1% of entity-combats >3x
11. [Signal 5] Card win correlation: arcane_strike_01 (7.879)
