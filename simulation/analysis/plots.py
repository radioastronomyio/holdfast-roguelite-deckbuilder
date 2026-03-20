"""Generates all required plots from MonteCarloResult telemetry."""
from __future__ import annotations

import math
from pathlib import Path

from agents.monte_carlo import MonteCarloResult
from engine.encounters import CombatResult
from analysis.collectors import (
    collect_card_stats,
    collect_upgrade_stats,
    collect_region_stats,
    collect_world_card_stats,
    collect_speed_stats,
    collect_difficulty_curve,
    collect_seed_classification,
    collect_combat_duration,
    collect_convergence_deep,
)

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _setup_style():
    if HAS_SEABORN:
        sns.set_theme(style="whitegrid", palette="colorblind")
    else:
        plt.rcParams.update({
            "axes.facecolor": "white",
            "axes.grid": True,
            "grid.color": "#dddddd",
        })
    plt.rcParams["figure.dpi"] = 100


def _save(fig, path: Path, name: str) -> Path:
    p = path / name
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def generate_all_plots(result: MonteCarloResult, output_dir: Path) -> list[Path]:
    """Generate all 15 required plots. Returns list of saved paths."""
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _setup_style()

    saved: list[Path] = []
    saved.append(_plot_win_rate_by_strategy(result, plots_dir))
    saved.append(_plot_win_rate_by_region_reached(result, plots_dir))
    saved.append(_plot_death_distribution(result, plots_dir))
    saved.append(_plot_card_usage_heatmap(result, plots_dir))
    saved.append(_plot_card_win_correlation(result, plots_dir))
    saved.append(_plot_upgrade_branch_rates(result, plots_dir))
    saved.append(_plot_world_card_accept_rates(result, plots_dir))
    saved.append(_plot_speed_ratio_distribution(result, plots_dir))
    saved.append(_plot_combat_duration_by_region(result, plots_dir))
    saved.append(_plot_turn_cap_rate_by_region(result, plots_dir))
    saved.append(_plot_seed_tier_distribution(result, plots_dir))
    saved.append(_plot_strategy_agreement_matrix(result, plots_dir))
    saved.append(_plot_difficulty_curve(result, plots_dir))
    saved.append(_plot_damage_per_energy(result, plots_dir))
    saved.append(_plot_convergence_region_order(result, plots_dir))
    return saved


# ---------------------------------------------------------------------------
# Individual plots
# ---------------------------------------------------------------------------

def _plot_win_rate_by_strategy(result: MonteCarloResult, plots_dir: Path) -> Path:
    strategies = [m.strategy_name for m in result.strategy_results]
    win_rates = [m.win_rate for m in result.strategy_results]
    n = [m.total_runs for m in result.strategy_results]
    # 95% CI using Wilson interval approximation
    cis = []
    for wr, ni in zip(win_rates, n):
        if ni > 0:
            z = 1.96
            ci = z * math.sqrt(wr * (1 - wr) / ni)
        else:
            ci = 0.0
        cis.append(ci)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = plt.cm.tab10.colors[:len(strategies)]
    bars = ax.bar(strategies, win_rates, yerr=cis, capsize=6, color=colors, alpha=0.85)
    ax.axhline(0.40, color="red", linestyle="--", linewidth=1, label="40% lower bound")
    ax.axhline(0.70, color="green", linestyle="--", linewidth=1, label="70% upper bound")
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Win Rate")
    ax.set_title("Win Rate by Strategy (95% CI)")
    ax.legend()
    for bar, wr in zip(bars, win_rates):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{wr:.1%}", ha="center", va="bottom", fontsize=9)
    return _save(fig, plots_dir, "win_rate_by_strategy.png")


def _plot_win_rate_by_region_reached(result: MonteCarloResult, plots_dir: Path) -> Path:
    curve = collect_difficulty_curve(result)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = plt.cm.tab10.colors
    for i, (strategy, probs) in enumerate(curve.conditional_win_prob.items()):
        ax.plot(curve.region_indices, probs, marker="o", label=strategy, color=colors[i])
    ax.set_xlabel("Region Index (assault order)")
    ax.set_ylabel("Conditional Win Probability")
    ax.set_title("Win Rate Given Reaching Region N")
    ax.set_ylim(0, 1.0)
    ax.legend()
    return _save(fig, plots_dir, "win_rate_by_region_reached.png")


def _plot_death_distribution(result: MonteCarloResult, plots_dir: Path) -> Path:
    strategies = result.config.strategies
    # deaths_at[strategy][region_idx]
    max_regions = 0
    deaths: dict[str, dict[int, int]] = {s: {} for s in strategies}
    total: dict[str, int] = {s: 0 for s in strategies}

    for seed, strats in result.per_seed_results.items():
        for sname, cr in strats.items():
            total[sname] += 1
            if not cr.victory and cr.region_order:
                idx = len(cr.region_order) - 1
                deaths[sname][idx] = deaths[sname].get(idx, 0) + 1
                max_regions = max(max_regions, idx + 1)

    if max_regions == 0:
        max_regions = 6

    region_indices = list(range(max_regions))
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = plt.cm.tab10.colors
    bottoms = np.zeros(max_regions)
    for i, sname in enumerate(strategies):
        counts = np.array([deaths[sname].get(idx, 0) / max(total[sname], 1) for idx in region_indices])
        ax.bar(region_indices, counts, bottom=bottoms, label=sname, color=colors[i], alpha=0.8)
        bottoms += counts

    ax.set_xlabel("Region Index (where campaign ended)")
    ax.set_ylabel("Fraction of Campaigns")
    ax.set_title("Death Distribution by Region (per strategy, stacked)")
    ax.legend()
    return _save(fig, plots_dir, "death_distribution.png")


def _plot_card_usage_heatmap(result: MonteCarloResult, plots_dir: Path) -> Path:
    strategies = result.config.strategies
    # card × strategy usage (plays per campaign)
    plays: dict[str, dict[str, int]] = {s: {} for s in strategies}
    campaign_count: dict[str, int] = {s: 0 for s in strategies}

    for seed, strats in result.per_seed_results.items():
        for sname, cr in strats.items():
            campaign_count[sname] += 1
            for enc in cr.encounter_results:
                if isinstance(enc, CombatResult):
                    for cp in enc.card_plays:
                        plays[sname][cp.card_id] = plays[sname].get(cp.card_id, 0) + 1

    all_cards = sorted(set(
        cid for s in strategies for cid in plays[s]
    ))
    if not all_cards:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.text(0.5, 0.5, "No card play data", ha="center")
        return _save(fig, plots_dir, "card_usage_heatmap.png")

    data = np.zeros((len(all_cards), len(strategies)))
    for j, sname in enumerate(strategies):
        nc = max(campaign_count[sname], 1)
        for i, cid in enumerate(all_cards):
            data[i, j] = plays[sname].get(cid, 0) / nc

    fig, ax = plt.subplots(figsize=(max(6, len(strategies) * 2), max(6, len(all_cards) * 0.4)))
    if HAS_SEABORN:
        import seaborn as sns
        sns.heatmap(data, xticklabels=strategies, yticklabels=all_cards,
                    ax=ax, cmap="YlOrRd", linewidths=0.3)
    else:
        im = ax.imshow(data, aspect="auto", cmap="YlOrRd")
        ax.set_xticks(range(len(strategies)))
        ax.set_xticklabels(strategies)
        ax.set_yticks(range(len(all_cards)))
        ax.set_yticklabels(all_cards, fontsize=7)
        plt.colorbar(im, ax=ax)
    ax.set_title("Card × Strategy Usage Frequency (plays/campaign)")
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Card")
    return _save(fig, plots_dir, "card_usage_heatmap.png")


def _plot_card_win_correlation(result: MonteCarloResult, plots_dir: Path) -> Path:
    card_stats = collect_card_stats(result)
    sorted_cards = sorted(card_stats.values(), key=lambda c: c.win_corr)
    names = [c.card_id for c in sorted_cards]
    corrs = [c.win_corr for c in sorted_cards]

    fig, ax = plt.subplots(figsize=(8, max(4, len(names) * 0.35)))
    colors = ["#d73027" if c < 0 else "#4575b4" for c in corrs]
    ax.barh(names, corrs, color=colors, alpha=0.8)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Win Correlation")
    ax.set_title("Cards Sorted by Win Correlation")
    return _save(fig, plots_dir, "card_win_correlation.png")


def _plot_upgrade_branch_rates(result: MonteCarloResult, plots_dir: Path) -> Path:
    upgrade_stats = collect_upgrade_stats(result)
    if not upgrade_stats:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No upgrade data available", ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Upgrade Branch Pick Rates")
        return _save(fig, plots_dir, "upgrade_branch_rates.png")

    cards = list(upgrade_stats.keys())
    a_rates = [upgrade_stats[c].branch_a_rate for c in cards]
    b_rates = [upgrade_stats[c].branch_b_rate for c in cards]
    x = np.arange(len(cards))
    width = 0.35

    fig, ax = plt.subplots(figsize=(max(6, len(cards) * 1.2), 5))
    bars_a = ax.bar(x - width / 2, a_rates, width, label="Branch A", color="#4575b4", alpha=0.8)
    bars_b = ax.bar(x + width / 2, b_rates, width, label="Branch B", color="#d73027", alpha=0.8)
    ax.axhline(0.70, color="orange", linestyle="--", linewidth=1.5, label="70% dominance threshold")
    ax.set_xticks(x)
    ax.set_xticklabels(cards, rotation=30, ha="right")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Pick Rate in Winning Runs")
    ax.set_title("Upgrade Branch Pick Rates")
    ax.legend()
    return _save(fig, plots_dir, "upgrade_branch_rates.png")


def _plot_world_card_accept_rates(result: MonteCarloResult, plots_dir: Path) -> Path:
    wc_stats = collect_world_card_stats(result)
    if not wc_stats:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No world card data", ha="center")
        return _save(fig, plots_dir, "world_card_accept_rates.png")

    sorted_wc = sorted(wc_stats.values(), key=lambda w: w.accept_rate, reverse=True)
    names = [w.card_id for w in sorted_wc]
    rates = [w.accept_rate for w in sorted_wc]

    fig, ax = plt.subplots(figsize=(8, max(4, len(names) * 0.35)))
    colors = ["#d73027" if r > 0.9 else "#4575b4" for r in rates]
    ax.barh(names, rates, color=colors, alpha=0.8)
    ax.axvline(0.90, color="orange", linestyle="--", linewidth=1.5, label="90% threshold")
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Accept Rate")
    ax.set_title("World Card Accept Rate")
    ax.legend()
    return _save(fig, plots_dir, "world_card_accept_rates.png")


def _plot_speed_ratio_distribution(result: MonteCarloResult, plots_dir: Path) -> Path:
    speed = collect_speed_stats(result)
    ratios = speed.ratios

    fig, ax = plt.subplots(figsize=(8, 5))
    if ratios:
        ax.hist(ratios, bins=50, color="#4575b4", alpha=0.8, edgecolor="white")
        ax.axvline(3.0, color="orange", linestyle="--", linewidth=1.5, label="3x threshold")
        ax.axvline(5.0, color="red", linestyle="--", linewidth=1.5, label="5x threshold")
        ax.legend()
    else:
        ax.text(0.5, 0.5, "No speed data", ha="center")
    ax.set_xlabel("Speed Action Ratio (player turns / avg enemy turns)")
    ax.set_ylabel("Count")
    ax.set_title("Speed Action Ratio Distribution")
    return _save(fig, plots_dir, "speed_ratio_distribution.png")


def _plot_combat_duration_by_region(result: MonteCarloResult, plots_dir: Path) -> Path:
    dur = collect_combat_duration(result)

    fig, ax = plt.subplots(figsize=(9, 5))
    if dur.durations_by_region:
        sorted_regions = sorted(dur.durations_by_region.keys())
        data = [dur.durations_by_region[idx] for idx in sorted_regions]
        labels = [str(idx) for idx in sorted_regions]
        ax.boxplot(data, labels=labels, patch_artist=True,
                   boxprops=dict(facecolor="#a6cee3", alpha=0.7))
    else:
        ax.text(0.5, 0.5, "No combat duration data", ha="center")
    ax.set_xlabel("Region Index (assault order)")
    ax.set_ylabel("Combat Turn Count")
    ax.set_title("Combat Duration Distribution by Region")
    return _save(fig, plots_dir, "combat_duration_by_region.png")


def _plot_turn_cap_rate_by_region(result: MonteCarloResult, plots_dir: Path) -> Path:
    dur = collect_combat_duration(result)
    if not dur.turn_cap_rate_by_region:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.text(0.5, 0.5, "No turn-cap data", ha="center")
        ax.set_title("Turn Cap Rate by Region")
        return _save(fig, plots_dir, "turn_cap_rate_by_region.png")

    sorted_regions = sorted(dur.turn_cap_rate_by_region.keys())
    rates = [dur.turn_cap_rate_by_region[idx] for idx in sorted_regions]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(sorted_regions, rates, color="#d73027", alpha=0.8)
    ax.set_xlabel("Region Index")
    ax.set_ylabel("Fraction of Combats Hitting 200-Turn Cap")
    ax.set_title("Turn Cap Rate by Region")
    return _save(fig, plots_dir, "turn_cap_rate_by_region.png")


def _plot_seed_tier_distribution(result: MonteCarloResult, plots_dir: Path) -> Path:
    sc = collect_seed_classification(result)
    labels = ["All Win", "Strategy Dependent", "All Loss"]
    sizes = [len(sc.all_win_seeds), len(sc.strategy_dependent_seeds), len(sc.all_loss_seeds)]
    colors = ["#4dac26", "#f1b6da", "#d01c8b"]

    fig, ax = plt.subplots(figsize=(6, 6))
    non_zero = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
    if non_zero:
        lbls, szs, clrs = zip(*non_zero)
        wedges, texts, autotexts = ax.pie(
            szs, labels=lbls, colors=clrs, autopct="%1.1f%%",
            startangle=90, pctdistance=0.8
        )
    else:
        ax.text(0.5, 0.5, "No seed data", ha="center")
    ax.set_title(f"Seed Tier Distribution (n={sc.total_seeds})")
    return _save(fig, plots_dir, "seed_tier_distribution.png")


def _plot_strategy_agreement_matrix(result: MonteCarloResult, plots_dir: Path) -> Path:
    conv = collect_convergence_deep(result)
    strategies = result.config.strategies
    matrix = np.array([
        [conv.strategy_correlation.get(s1, {}).get(s2, 0.0) for s2 in strategies]
        for s1 in strategies
    ])

    fig, ax = plt.subplots(figsize=(6, 5))
    if HAS_SEABORN:
        import seaborn as sns
        sns.heatmap(matrix, xticklabels=strategies, yticklabels=strategies,
                    ax=ax, cmap="RdYlGn", vmin=0, vmax=1, annot=True, fmt=".2f")
    else:
        im = ax.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=1)
        ax.set_xticks(range(len(strategies)))
        ax.set_xticklabels(strategies)
        ax.set_yticks(range(len(strategies)))
        ax.set_yticklabels(strategies)
        plt.colorbar(im, ax=ax)
        for i in range(len(strategies)):
            for j in range(len(strategies)):
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=9)
    ax.set_title("Pairwise Strategy Win/Loss Agreement Rate")
    return _save(fig, plots_dir, "strategy_agreement_matrix.png")


def _plot_difficulty_curve(result: MonteCarloResult, plots_dir: Path) -> Path:
    """Enemy stat budget vs region index (using region_difficulties data) + win prob."""
    curve = collect_difficulty_curve(result)
    fig, ax1 = plt.subplots(figsize=(9, 5))

    colors = plt.cm.tab10.colors
    for i, (strategy, probs) in enumerate(curve.conditional_win_prob.items()):
        ax1.plot(curve.region_indices, probs, marker="o", label=f"Win prob ({strategy})",
                 color=colors[i], alpha=0.8)
    ax1.set_xlabel("Region Index (assault order, 0-based)")
    ax1.set_ylabel("Conditional Win Probability")
    ax1.set_ylim(0, 1.05)
    ax1.set_title("Difficulty Curve: Win Probability vs Region Index")
    ax1.legend(loc="upper right")
    return _save(fig, plots_dir, "difficulty_curve.png")


def _plot_damage_per_energy(result: MonteCarloResult, plots_dir: Path) -> Path:
    """Per-card damage-per-energy, sized by usage frequency."""
    # Collect per-card data with energy cost
    plays_count: dict[str, int] = {}
    total_dmg: dict[str, int] = {}
    energy_cost: dict[str, int] = {}

    for seed, strats in result.per_seed_results.items():
        for sname, cr in strats.items():
            for enc in cr.encounter_results:
                if isinstance(enc, CombatResult):
                    for cp in enc.card_plays:
                        cid = cp.card_id
                        plays_count[cid] = plays_count.get(cid, 0) + 1
                        total_dmg[cid] = total_dmg.get(cid, 0) + cp.damage_total
                        energy_cost[cid] = cp.energy_cost  # last seen, should be constant

    cards = list(plays_count.keys())
    if not cards:
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.text(0.5, 0.5, "No card play data", ha="center")
        ax.set_title("Damage per Energy Cost")
        return _save(fig, plots_dir, "damage_per_energy.png")

    dpe = []
    sizes = []
    labels = []
    for cid in cards:
        cost = max(energy_cost.get(cid, 1), 1)
        plays = plays_count[cid]
        dmg = total_dmg.get(cid, 0)
        avg_dmg = dmg / plays if plays > 0 else 0
        dpe.append(avg_dmg / cost)
        sizes.append(math.log1p(plays) * 30)
        labels.append(cid)

    fig, ax = plt.subplots(figsize=(9, 6))
    scatter = ax.scatter(range(len(cards)), dpe, s=sizes, alpha=0.7, color="#4575b4")
    ax.set_xticks(range(len(cards)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("Avg Damage per Energy Cost (display scale)")
    ax.set_title("Damage per Energy Cost (bubble size = log usage frequency)")
    return _save(fig, plots_dir, "damage_per_energy.png")


def _plot_convergence_region_order(result: MonteCarloResult, plots_dir: Path) -> Path:
    """Region ordering patterns (simplified alluvial using bar chart of first-region choices)."""
    strategies = result.config.strategies
    first_region_counts: dict[str, dict[str, int]] = {s: {} for s in strategies}

    for seed, strats in result.per_seed_results.items():
        for sname, cr in strats.items():
            if cr.region_order:
                r = cr.region_order[0]
                first_region_counts[sname][r] = first_region_counts[sname].get(r, 0) + 1

    all_regions = sorted(set(
        r for s in strategies for r in first_region_counts[s]
    ))
    if not all_regions:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.text(0.5, 0.5, "No region ordering data", ha="center")
        ax.set_title("First Region Choice by Strategy")
        return _save(fig, plots_dir, "convergence_region_order.png")

    total_per_strategy: dict[str, int] = {
        s: sum(first_region_counts[s].values()) for s in strategies
    }
    x = np.arange(len(all_regions))
    width = 0.8 / max(len(strategies), 1)
    colors = plt.cm.tab10.colors

    fig, ax = plt.subplots(figsize=(max(8, len(all_regions) * 1.5), 5))
    for i, sname in enumerate(strategies):
        total = max(total_per_strategy[sname], 1)
        rates = [first_region_counts[sname].get(r, 0) / total for r in all_regions]
        offset = (i - len(strategies) / 2 + 0.5) * width
        ax.bar(x + offset, rates, width, label=sname, color=colors[i], alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(all_regions, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Fraction of Campaigns")
    ax.set_title("First Region Choice by Strategy")
    ax.legend()
    return _save(fig, plots_dir, "convergence_region_order.png")
