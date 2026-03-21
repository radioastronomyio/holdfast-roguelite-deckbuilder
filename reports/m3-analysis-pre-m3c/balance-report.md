# M3a Balance Analysis Report

**Seeds:** 5000  |  **Strategies:** aggressive, defensive, balanced

## 1. Executive Summary

**Win-rate band (40.0%–70.0%):** ❌ OUT OF BAND

- ❌ **aggressive**: 34.0% (1699/5000) | avg regions 3.84 | avg turns 58.8
- ✅ **defensive**: 43.6% (2178/5000) | avg regions 4.20 | avg turns 46.6
- ✅ **balanced**: 60.7% (3034/5000) | avg regions 4.68 | avg turns 51.9

**Win-rate spread:** 26.7%

**Convergence warning:** YES

## 2. GDD Degenerate Signal Checklist

### Signal 1: Win Rate In Range

- aggressive: 34.0% → **FAIL**
- defensive: 43.6% → **PASS**
- balanced: 60.7% → **PASS**

### Signal 2: Upgrade Path Pick Rate

- **PASS** — no branch >70% dominance in winning runs

### Signal 3: World Card Skip/Accept Rate

- **PASS** — no world card >90% auto-accept or auto-skip

### Signal 4: Speed Stat Ceiling

- Entities acting >3x/cycle: 3.8% of (entity,combat) pairs → **FAIL**
- Entities acting >5x/cycle: 2.6%
- Max observed ratio: 77.00
- Flagged combats: 5965

### Signal 5: Card Combo Win Rate

- **FAIL** — high win correlation cards: arcane_strike_01 (6.557), frost_bolt_01 (3.485)

## 3. Strategy Differentiation

- First-region agreement across strategies: 100.0%
- Full region-order agreement: 51.3%
- Seeds where all strategies agree (win or all lose): 51.5%
- Strategy-dependent seeds: 48.5%

**Pairwise win/loss agreement rate:**

| | aggressive | defensive | balanced |
|---|---|---|---|
| **aggressive** | 100.0% | 69.5% | 62.1% |
| **defensive** | 69.5% | 100.0% | 71.4% |
| **balanced** | 62.1% | 71.4% | 100.0% |

## 4. Card Balance

**Top 10 cards by win correlation:**

| Card | Win Corr | Plays/Campaign | Avg Damage/Play |
|------|----------|----------------|-----------------|
| arcane_strike_01 | 6.5570 | 49.21 | 35.3 |
| frost_bolt_01 | 3.4854 | 35.33 | 26.2 |
| cleanse_01 | 3.4486 | 43.59 | 0.0 |
| drain_life_01 | 2.9976 | 31.36 | 15.7 |
| sweeping_blade_01 | 2.9654 | 31.65 | 32.5 |
| acid_flask_01 | 2.6716 | 29.73 | 0.0 |
| heal_potion_01 | 2.5949 | 45.24 | 0.0 |
| shield_bash_01 | 2.2417 | 31.46 | 16.5 |
| immolate_01 | 1.8902 | 30.17 | 0.0 |
| phalanx_01 | 1.7395 | 29.78 | 0.0 |

**Bottom 10 cards by win correlation:**

| Card | Win Corr | Plays/Campaign | Avg Damage/Play |
|------|----------|----------------|-----------------|
| acid_flask_01 | 2.6716 | 29.73 | 0.0 |
| heal_potion_01 | 2.5949 | 45.24 | 0.0 |
| shield_bash_01 | 2.2417 | 31.46 | 16.5 |
| immolate_01 | 1.8902 | 30.17 | 0.0 |
| phalanx_01 | 1.7395 | 29.78 | 0.0 |
| lightning_chain_01 | 1.4039 | 14.89 | 26.2 |
| adrenaline_01 | 1.1262 | 14.57 | 0.0 |
| power_surge_01 | 1.0044 | 14.82 | 0.0 |
| deep_focus_01 | 0.9888 | 14.77 | 0.0 |
| stone_wall_01 | 0.8831 | 14.70 | 0.0 |

**Never-played cards:** none

**Upgrade branch dominance:**

| Card | Branch A rate | Branch B rate | A win rate | B win rate |
|------|---------------|---------------|------------|------------|
| arcane_strike_01 | 0.0% | 0.0% | 0.0% | 0.0% |
| adrenaline_01 | 0.0% | 0.0% | 0.0% | 0.0% |
| deep_focus_01 | 0.0% | 0.0% | 0.0% | 0.0% |
| power_surge_01 | 0.0% | 0.0% | 0.0% | 0.0% |
| immolate_01 | 0.0% | 0.0% | 0.0% | 0.0% |
| shield_bash_01 | 0.0% | 0.0% | 0.0% | 0.0% |
| phalanx_01 | 0.0% | 0.0% | 0.0% | 0.0% |
| cleanse_01 | 0.0% | 0.0% | 0.0% | 0.0% |
| acid_flask_01 | 0.0% | 0.0% | 0.0% | 0.0% |
| stone_wall_01 | 0.0% | 0.0% | 0.0% | 0.0% |

## 5. Region Analysis

| Region Idx | Win Rate (given reached) | Death Rate | Ordering Freq |
|------------|--------------------------|------------|---------------|
| 0 | 46.1% | 3.5% | 100.0% |
| 1 | 47.7% | 10.5% | 96.5% |
| 2 | 53.6% | 10.3% | 86.0% |
| 3 | 60.9% | 10.8% | 75.7% |
| 4 | 71.0% | 10.1% | 64.9% |
| 5 | 84.1% | 8.7% | 54.8% |

**Difficulty curve (conditional win prob by region):**

| Region Idx | aggressive | defensive | balanced | Attrition |
|---|---|---|---|---|
| 0 | 34.0% | 43.6% | 60.7% | 3.5% |
| 1 | 35.7% | 44.8% | 62.6% | 10.5% |
| 2 | 41.1% | 50.5% | 68.3% | 10.3% |
| 3 | 48.5% | 57.7% | 74.4% | 10.8% |
| 4 | 59.1% | 68.2% | 82.9% | 10.1% |
| 5 | 76.9% | 81.2% | 91.3% | 8.7% |

## 6. World Card Economics

| Card | Accept Rate | Skip Rate | Accept (wins) | Accept (losses) |
|------|-------------|-----------|---------------|-----------------|
| heavy_armor | 86.8% | 13.2% | 89.0% | 82.7% |
| vampiric_contract | 86.8% | 13.2% | 89.5% | 81.6% |
| hyper_metabolism | 86.7% | 13.3% | 90.0% | 80.3% |
| martyrdom | 86.6% | 13.4% | 90.1% | 79.7% |
| barricaded | 86.3% | 13.7% | 89.5% | 79.9% |
| temporal_shift | 84.4% | 15.6% | 85.6% | 82.0% |
| forced_march | 84.2% | 15.8% | 85.9% | 80.7% |
| echo_chamber | 84.0% | 16.0% | 86.0% | 79.8% |
| scavengers_greed | 71.9% | 28.1% | 77.8% | 59.8% |
| rations_cut | 71.0% | 29.0% | 74.8% | 63.3% |
| leyline_tap | 70.6% | 29.4% | 76.1% | 59.8% |
| cursed_relic | 70.5% | 29.5% | 75.0% | 61.7% |
| unstable_mutagen | 58.7% | 41.3% | 56.4% | 63.0% |
| tunnel_vision | 56.4% | 43.6% | 52.3% | 64.1% |
| reckless_assault | 55.6% | 44.4% | 52.0% | 62.5% |
| fog_of_war | 43.3% | 56.7% | 40.2% | 48.7% |
| pacifism_protocol | 43.0% | 57.0% | 42.8% | 43.3% |
| blood_magic | 43.0% | 57.0% | 41.7% | 45.4% |
| glass_cannon | 43.0% | 57.0% | 10.8% | 78.6% |
| overclocked | 41.7% | 58.3% | 41.0% | 43.2% |

## 7. Speed System Health

- Mean action ratio: 0.360
- Max observed ratio: 77.000
- % entity-combats >3x: 3.8%
- % entity-combats >5x: 2.6%
- Flagged combats (any entity >3x): 5965

## 8. Seed Characterization

- Total seeds: 5000
- All-win seeds: 1074 (21.5%)
- All-loss seeds: 1500 (30.0%)
- Strategy-dependent seeds: 2426 (48.5%)
- Sample all-loss seeds: [2, 6, 8, 9, 10]
- Sample all-win seeds: [1, 4, 5, 12, 13]

## 9. Combat Health

- Mean combat duration: 6.7 turns
- Median combat duration: 3.0 turns
- P95 combat duration: 12.0 turns
- Turn-cap hit rate: 1.0%

**Turn-cap rate by region index:**

| Region Idx | Cap Rate |
|------------|----------|
| 0 | 1.1% |
| 1 | 0.4% |
| 2 | 1.6% |
| 3 | 0.8% |
| 4 | 1.0% |
| 5 | 0.9% |
| 6 | 1.6% |
| 7 | 1.2% |
| 8 | 1.2% |
| 9 | 0.7% |
| 10 | 1.0% |
| 11 | 0.2% |

- Aggregate damage dealt (all plays, display scale): 25506566
- Aggregate healing done (all plays, display scale): 6457992

## 10. Flagged Issues

1. [Signal 1] aggressive win rate 34.0% outside 40.0%–70.0%
2. [Signal 4] Speed dominance: 3.8% of entity-combats >3x
3. [Signal 5] Card win correlation: arcane_strike_01 (6.557)
