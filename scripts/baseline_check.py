"""Post-fix Monte Carlo baseline check."""
import sys
sys.path.insert(0, "simulation")
from campaign.loader import load_game_data
from agents.monte_carlo import run_monte_carlo, monte_carlo_to_json, MonteCarloConfig
from pathlib import Path
import time

data_path = Path("data")
mods_path = Path("mods/default/flavor")
gd = load_game_data(data_path, mods_path)

# Quick check
print("=== 100 SEED BASELINE ===")
config = MonteCarloConfig(seed_start=1, seed_count=100, strategies=["aggressive", "defensive", "balanced"])
t0 = time.time()
result = run_monte_carlo(config, gd, data_path, mods_path)
elapsed = time.time() - t0

for m in result.strategy_results:
    status = "OK" if 0.40 <= m.win_rate <= 0.70 else "OUT OF RANGE"
    print(f"  {m.strategy_name:12s} | win_rate={m.win_rate:.0%} [{status}] | regions={m.avg_regions_cleared:.1f} | turns={m.avg_total_turns:.0f}")
print(f"  Spread: {result.win_rate_spread:.2f} (healthy: < 0.30)")
print(f"  Convergence: {result.convergence_warning}")
print(f"  Time: {elapsed:.1f}s")

all_ok = all(0.40 <= m.win_rate <= 0.70 for m in result.strategy_results)
print(f"\n{'PASS' if all_ok else 'NEEDS TUNING'}: {'All strategies in range' if all_ok else 'Some strategies out of range'}")
