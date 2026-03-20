"""M3a Analysis Runner — runs full Monte Carlo simulation and generates all analysis outputs.

Run from repo root:
    python scripts/run_m3_analysis.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Add simulation/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "simulation"))

from campaign.loader import load_game_data
from agents.monte_carlo import MonteCarloConfig, run_monte_carlo
from analysis.reports import generate_balance_report
from analysis.plots import generate_all_plots
from analysis.data_export import export_analysis_data

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED_START = 1
SEED_COUNT = 5000
STRATEGIES = ["aggressive", "defensive", "balanced"]
OUTPUT_DIR = Path("reports/m3-analysis")
DATA_PATH = Path("data")
MODS_PATH = Path("mods/default/flavor")

# Use multiprocessing for the large run (4 workers)
WORKERS = 4


def main():
    total_start = time.time()
    print(f"[M3a] Running Monte Carlo: {SEED_COUNT} seeds x {len(STRATEGIES)} strategies")
    print(f"      Workers: {WORKERS}  |  Output: {OUTPUT_DIR}")
    print()

    # Load game data
    t0 = time.time()
    game_data = load_game_data(DATA_PATH, MODS_PATH)
    print(f"[M3a] Game data loaded in {time.time() - t0:.1f}s")

    # Run simulation
    config = MonteCarloConfig(
        seed_start=SEED_START,
        seed_count=SEED_COUNT,
        strategies=STRATEGIES,
        workers=WORKERS,
    )
    t0 = time.time()
    mc_result = run_monte_carlo(config, game_data, DATA_PATH, MODS_PATH)
    elapsed = time.time() - t0
    print(f"[M3a] Monte Carlo complete in {elapsed:.1f}s "
          f"({SEED_COUNT * len(STRATEGIES)} total runs, "
          f"{elapsed / (SEED_COUNT * len(STRATEGIES)) * 1000:.0f}ms/run avg)")
    print()

    # Print quick summary
    for m in mc_result.strategy_results:
        print(f"  {m.strategy_name:12s}: {m.win_rate:.1%} win rate "
              f"({m.wins}/{m.total_runs}), avg {m.avg_regions_cleared:.2f} regions, "
              f"avg {m.avg_total_turns:.0f} turns")
    print(f"  win-rate spread: {mc_result.win_rate_spread:.3f}")
    if mc_result.convergence_warning:
        print("  WARNING: Convergence warning: strategies converge on same first region >80% of the time")
    print()

    # Generate markdown report
    t0 = time.time()
    report_path = generate_balance_report(mc_result, OUTPUT_DIR)
    print(f"[M3a] Balance report generated: {report_path} ({time.time() - t0:.1f}s)")

    # Generate plots
    t0 = time.time()
    plots = generate_all_plots(mc_result, OUTPUT_DIR)
    print(f"[M3a] {len(plots)} plots generated in {time.time() - t0:.1f}s -> {OUTPUT_DIR / 'plots'}/")

    # Export JSON data
    t0 = time.time()
    export_analysis_data(mc_result, OUTPUT_DIR)
    print(f"[M3a] JSON data exported in {time.time() - t0:.1f}s -> {OUTPUT_DIR / 'data'}/")

    total_elapsed = time.time() - total_start
    print()
    print(f"[M3a] Done in {total_elapsed:.1f}s total.")
    print(f"      Report: {report_path}")
    print(f"      Plots:  {OUTPUT_DIR / 'plots'}")
    print(f"      Data:   {OUTPUT_DIR / 'data'}")


if __name__ == "__main__":
    main()
