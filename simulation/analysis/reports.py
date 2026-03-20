"""Generates the markdown balance report from MonteCarloResult."""
from __future__ import annotations

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

WIN_RATE_LOW = 0.40
WIN_RATE_HIGH = 0.70
UPGRADE_DOMINANCE_THRESHOLD = 0.70
WORLD_CARD_AUTO_THRESHOLD = 0.90
SPEED_FLAG_THRESHOLD = 3.0
COMBO_WIN_CORR_THRESHOLD = 0.90


def _pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def generate_balance_report(result: MonteCarloResult, output_dir: Path) -> Path:
    """Produce reports/m3-analysis/balance-report.md."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "balance-report.md"

    # Run all collectors
    card_stats = collect_card_stats(result)
    upgrade_stats = collect_upgrade_stats(result)
    region_stats = collect_region_stats(result)
    world_card_stats = collect_world_card_stats(result)
    speed_stats = collect_speed_stats(result)
    difficulty_curve = collect_difficulty_curve(result)
    seed_class = collect_seed_classification(result)
    combat_duration = collect_combat_duration(result)
    convergence = collect_convergence_deep(result)

    lines: list[str] = []

    # -----------------------------------------------------------------------
    # 1. Executive Summary
    # -----------------------------------------------------------------------
    lines.append("# M3a Balance Analysis Report\n")
    lines.append(f"**Seeds:** {result.config.seed_count}  |  "
                 f"**Strategies:** {', '.join(result.config.strategies)}\n")

    lines.append("## 1. Executive Summary\n")
    win_rates = {m.strategy_name: m.win_rate for m in result.strategy_results}
    in_band = all(WIN_RATE_LOW <= wr <= WIN_RATE_HIGH for wr in win_rates.values())
    band_status = "✅ IN BAND" if in_band else "❌ OUT OF BAND"
    lines.append(f"**Win-rate band ({_pct(WIN_RATE_LOW)}–{_pct(WIN_RATE_HIGH)}):** {band_status}\n")
    for m in result.strategy_results:
        flag = "✅" if WIN_RATE_LOW <= m.win_rate <= WIN_RATE_HIGH else "❌"
        lines.append(f"- {flag} **{m.strategy_name}**: {_pct(m.win_rate)} "
                     f"({m.wins}/{m.total_runs}) | avg regions {m.avg_regions_cleared:.2f} "
                     f"| avg turns {m.avg_total_turns:.1f}")
    lines.append(f"\n**Win-rate spread:** {_pct(result.win_rate_spread)}")
    lines.append(f"\n**Convergence warning:** {'YES' if result.convergence_warning else 'no'}\n")

    # -----------------------------------------------------------------------
    # 2. GDD Degenerate Signal Checklist
    # -----------------------------------------------------------------------
    lines.append("## 2. GDD Degenerate Signal Checklist\n")
    flagged_issues: list[str] = []

    # Signal 1: Win rate in band
    lines.append("### Signal 1: Win Rate In Range\n")
    for sname, wr in win_rates.items():
        ok = WIN_RATE_LOW <= wr <= WIN_RATE_HIGH
        status = "PASS" if ok else "FAIL"
        lines.append(f"- {sname}: {_pct(wr)} → **{status}**")
        if not ok:
            flagged_issues.append(f"[Signal 1] {sname} win rate {_pct(wr)} outside {_pct(WIN_RATE_LOW)}–{_pct(WIN_RATE_HIGH)}")
    lines.append("")

    # Signal 2: Upgrade path dominance
    lines.append("### Signal 2: Upgrade Path Pick Rate\n")
    if not upgrade_stats:
        lines.append("- No upgrade data (no upgrade trees in game data) → **N/A**\n")
    else:
        upgrade_flags = []
        for cid, ua in upgrade_stats.items():
            if ua.branch_a_rate > UPGRADE_DOMINANCE_THRESHOLD:
                upgrade_flags.append(f"  - {cid}: Branch A {_pct(ua.branch_a_rate)} in winning runs")
                flagged_issues.append(f"[Signal 2] {cid} Branch A dominance {_pct(ua.branch_a_rate)}")
            if ua.branch_b_rate > UPGRADE_DOMINANCE_THRESHOLD:
                upgrade_flags.append(f"  - {cid}: Branch B {_pct(ua.branch_b_rate)} in winning runs")
                flagged_issues.append(f"[Signal 2] {cid} Branch B dominance {_pct(ua.branch_b_rate)}")
        if upgrade_flags:
            lines.append(f"- **FAIL** — dominant branches detected:")
            lines.extend(upgrade_flags)
        else:
            lines.append("- **PASS** — no branch >70% dominance in winning runs")
        lines.append("")

    # Signal 3: World card skip rate
    lines.append("### Signal 3: World Card Skip/Accept Rate\n")
    wc_flags = []
    for cid, wca in world_card_stats.items():
        if wca.accept_rate > WORLD_CARD_AUTO_THRESHOLD:
            wc_flags.append(f"  - {cid}: accept {_pct(wca.accept_rate)}")
            flagged_issues.append(f"[Signal 3] {cid} auto-accept rate {_pct(wca.accept_rate)}")
        if wca.skip_rate > WORLD_CARD_AUTO_THRESHOLD:
            wc_flags.append(f"  - {cid}: skip {_pct(wca.skip_rate)}")
            flagged_issues.append(f"[Signal 3] {cid} auto-skip rate {_pct(wca.skip_rate)}")
    if wc_flags:
        lines.append(f"- **FAIL** — auto-accept/skip cards:")
        lines.extend(wc_flags)
    else:
        lines.append("- **PASS** — no world card >90% auto-accept or auto-skip")
    lines.append("")

    # Signal 4: Speed ceiling
    lines.append("### Signal 4: Speed Stat Ceiling\n")
    if speed_stats.pct_above_3x > 0:
        lines.append(f"- Entities acting >3x/cycle: {_pct(speed_stats.pct_above_3x)} of (entity,combat) pairs → **FAIL**")
        lines.append(f"- Entities acting >5x/cycle: {_pct(speed_stats.pct_above_5x)}")
        lines.append(f"- Max observed ratio: {speed_stats.max_ratio:.2f}")
        lines.append(f"- Flagged combats: {speed_stats.flagged_count}")
        flagged_issues.append(f"[Signal 4] Speed dominance: {_pct(speed_stats.pct_above_3x)} of entity-combats >3x")
    else:
        lines.append(f"- **PASS** — no entity acting >3x per enemy cycle")
        lines.append(f"- Max observed ratio: {speed_stats.max_ratio:.2f}")
    lines.append("")

    # Signal 5: Card combo win rate
    lines.append("### Signal 5: Card Combo Win Rate\n")
    # Simple 2-card combination check using win_corr
    sorted_cards = sorted(card_stats.values(), key=lambda c: c.win_corr, reverse=True)
    top_corr = sorted_cards[:2] if len(sorted_cards) >= 2 else sorted_cards
    if top_corr and top_corr[0].win_corr > COMBO_WIN_CORR_THRESHOLD:
        lines.append(f"- **FAIL** — high win correlation cards: "
                     + ", ".join(f"{c.card_id} ({c.win_corr:.3f})" for c in top_corr))
        flagged_issues.append(f"[Signal 5] Card win correlation: {top_corr[0].card_id} ({top_corr[0].win_corr:.3f})")
    else:
        top_str = ", ".join(f"{c.card_id} ({c.win_corr:.3f})" for c in top_corr)
        lines.append(f"- **PASS** — no card combination >90% correlated with wins")
        lines.append(f"- Top win-correlated cards: {top_str}")
    lines.append("")

    # -----------------------------------------------------------------------
    # 3. Strategy Differentiation
    # -----------------------------------------------------------------------
    lines.append("## 3. Strategy Differentiation\n")
    lines.append(f"- First-region agreement across strategies: {_pct(convergence.first_region_agreement)}")
    lines.append(f"- Full region-order agreement: {_pct(convergence.full_order_agreement)}")
    lines.append(f"- Seeds where all strategies agree (win or all lose): "
                 f"{seed_class.all_win_rate + seed_class.all_loss_rate:.1%}")
    lines.append(f"- Strategy-dependent seeds: {_pct(seed_class.strategy_dependent_rate)}\n")

    lines.append("**Pairwise win/loss agreement rate:**\n")
    strategies = result.config.strategies
    header = "| | " + " | ".join(strategies) + " |"
    sep = "|---|" + "---|" * len(strategies)
    lines.append(header)
    lines.append(sep)
    for s1 in strategies:
        row = f"| **{s1}** | "
        row += " | ".join(
            _pct(convergence.strategy_correlation.get(s1, {}).get(s2, 0.0))
            for s2 in strategies
        )
        row += " |"
        lines.append(row)
    lines.append("")

    # -----------------------------------------------------------------------
    # 4. Card Balance
    # -----------------------------------------------------------------------
    lines.append("## 4. Card Balance\n")
    sorted_by_corr = sorted(card_stats.values(), key=lambda c: c.win_corr, reverse=True)
    top10 = sorted_by_corr[:10]
    bot10 = sorted_by_corr[-10:]

    lines.append("**Top 10 cards by win correlation:**\n")
    lines.append("| Card | Win Corr | Plays/Campaign | Avg Damage/Play |")
    lines.append("|------|----------|----------------|-----------------|")
    for c in top10:
        lines.append(f"| {c.card_id} | {c.win_corr:.4f} | {c.plays_per_campaign:.2f} | {c.avg_damage_per_play:.1f} |")
    lines.append("")

    lines.append("**Bottom 10 cards by win correlation:**\n")
    lines.append("| Card | Win Corr | Plays/Campaign | Avg Damage/Play |")
    lines.append("|------|----------|----------------|-----------------|")
    for c in bot10:
        lines.append(f"| {c.card_id} | {c.win_corr:.4f} | {c.plays_per_campaign:.2f} | {c.avg_damage_per_play:.1f} |")
    lines.append("")

    never_played = [c for c in card_stats.values() if c.total_plays == 0]
    if never_played:
        lines.append(f"**Never-played cards:** {', '.join(c.card_id for c in never_played)}\n")
    else:
        lines.append("**Never-played cards:** none\n")

    if upgrade_stats:
        lines.append("**Upgrade branch dominance:**\n")
        lines.append("| Card | Branch A rate | Branch B rate | A win rate | B win rate |")
        lines.append("|------|---------------|---------------|------------|------------|")
        for cid, ua in upgrade_stats.items():
            a_flag = " ⚠️" if ua.branch_a_rate > UPGRADE_DOMINANCE_THRESHOLD else ""
            b_flag = " ⚠️" if ua.branch_b_rate > UPGRADE_DOMINANCE_THRESHOLD else ""
            lines.append(f"| {cid} | {_pct(ua.branch_a_rate)}{a_flag} | "
                         f"{_pct(ua.branch_b_rate)}{b_flag} | "
                         f"{_pct(ua.branch_a_win_rate)} | {_pct(ua.branch_b_win_rate)} |")
        lines.append("")

    # -----------------------------------------------------------------------
    # 5. Region Analysis
    # -----------------------------------------------------------------------
    lines.append("## 5. Region Analysis\n")
    lines.append("| Region Idx | Win Rate (given reached) | Death Rate | Ordering Freq |")
    lines.append("|------------|--------------------------|------------|---------------|")
    for idx, ra in sorted(region_stats.items()):
        lines.append(f"| {idx} | {_pct(ra.win_rate)} | {_pct(ra.death_rate)} | {_pct(ra.ordering_frequency)} |")
    lines.append("")

    lines.append("**Difficulty curve (conditional win prob by region):**\n")
    header = "| Region Idx | " + " | ".join(difficulty_curve.conditional_win_prob.keys()) + " | Attrition |"
    sep = "|---|" + "---|" * (len(difficulty_curve.conditional_win_prob) + 1)
    lines.append(header)
    lines.append(sep)
    for i, idx in enumerate(difficulty_curve.region_indices):
        row = f"| {idx} | "
        row += " | ".join(
            _pct(probs[i]) if i < len(probs) else "—"
            for probs in difficulty_curve.conditional_win_prob.values()
        )
        atr = difficulty_curve.attrition_rate[i] if i < len(difficulty_curve.attrition_rate) else 0.0
        row += f" | {_pct(atr)} |"
        lines.append(row)
    lines.append("")

    # -----------------------------------------------------------------------
    # 6. World Card Economics
    # -----------------------------------------------------------------------
    lines.append("## 6. World Card Economics\n")
    sorted_wc = sorted(world_card_stats.values(), key=lambda w: w.accept_rate, reverse=True)
    lines.append("| Card | Accept Rate | Skip Rate | Accept (wins) | Accept (losses) |")
    lines.append("|------|-------------|-----------|---------------|-----------------|")
    for wca in sorted_wc:
        auto_a = " ⚠️" if wca.accept_rate > WORLD_CARD_AUTO_THRESHOLD else ""
        auto_s = " ⚠️" if wca.skip_rate > WORLD_CARD_AUTO_THRESHOLD else ""
        lines.append(f"| {wca.card_id} | {_pct(wca.accept_rate)}{auto_a} | "
                     f"{_pct(wca.skip_rate)}{auto_s} | "
                     f"{_pct(wca.accept_rate_in_wins)} | {_pct(wca.accept_rate_in_losses)} |")
    lines.append("")

    # -----------------------------------------------------------------------
    # 7. Speed System Health
    # -----------------------------------------------------------------------
    lines.append("## 7. Speed System Health\n")
    lines.append(f"- Mean action ratio: {speed_stats.mean_ratio:.3f}")
    lines.append(f"- Max observed ratio: {speed_stats.max_ratio:.3f}")
    lines.append(f"- % entity-combats >3x: {_pct(speed_stats.pct_above_3x)}")
    lines.append(f"- % entity-combats >5x: {_pct(speed_stats.pct_above_5x)}")
    lines.append(f"- Flagged combats (any entity >3x): {speed_stats.flagged_count}")
    lines.append("")

    # -----------------------------------------------------------------------
    # 8. Seed Characterization
    # -----------------------------------------------------------------------
    lines.append("## 8. Seed Characterization\n")
    lines.append(f"- Total seeds: {seed_class.total_seeds}")
    lines.append(f"- All-win seeds: {len(seed_class.all_win_seeds)} ({_pct(seed_class.all_win_rate)})")
    lines.append(f"- All-loss seeds: {len(seed_class.all_loss_seeds)} ({_pct(seed_class.all_loss_rate)})")
    lines.append(f"- Strategy-dependent seeds: {len(seed_class.strategy_dependent_seeds)} ({_pct(seed_class.strategy_dependent_rate)})")
    if seed_class.all_loss_seeds[:5]:
        lines.append(f"- Sample all-loss seeds: {seed_class.all_loss_seeds[:5]}")
    if seed_class.all_win_seeds[:5]:
        lines.append(f"- Sample all-win seeds: {seed_class.all_win_seeds[:5]}")
    lines.append("")

    # -----------------------------------------------------------------------
    # 9. Combat Health
    # -----------------------------------------------------------------------
    lines.append("## 9. Combat Health\n")
    lines.append(f"- Mean combat duration: {combat_duration.mean_duration:.1f} turns")
    lines.append(f"- Median combat duration: {combat_duration.median_duration:.1f} turns")
    lines.append(f"- P95 combat duration: {combat_duration.p95_duration:.1f} turns")
    lines.append(f"- Turn-cap hit rate: {_pct(combat_duration.turn_cap_rate)}")
    if combat_duration.turn_cap_rate > 0.05:
        flagged_issues.append(f"[Section 9] Turn cap hit rate {_pct(combat_duration.turn_cap_rate)} — >5% of combats stall")
    lines.append("")
    if combat_duration.turn_cap_rate_by_region:
        lines.append("**Turn-cap rate by region index:**\n")
        lines.append("| Region Idx | Cap Rate |")
        lines.append("|------------|----------|")
        for idx, rate in sorted(combat_duration.turn_cap_rate_by_region.items()):
            lines.append(f"| {idx} | {_pct(rate)} |")
        lines.append("")

    # Damage vs healing
    total_dmg = sum(c.total_plays * c.avg_damage_per_play for c in card_stats.values())
    total_heals = sum(
        cp.healing_total
        for seed, strats in result.per_seed_results.items()
        for strategy_name, cr in strats.items()
        for enc in cr.encounter_results
        if isinstance(enc, CombatResult)
        for cp in enc.card_plays
    )
    lines.append(f"- Aggregate damage dealt (all plays, display scale): {total_dmg:.0f}")
    lines.append(f"- Aggregate healing done (all plays, display scale): {total_heals}")
    lines.append("")

    # -----------------------------------------------------------------------
    # 10. Flagged Issues
    # -----------------------------------------------------------------------
    lines.append("## 10. Flagged Issues\n")
    if not flagged_issues:
        lines.append("No degenerate signals detected. All checks passed.\n")
    else:
        for i, issue in enumerate(flagged_issues, 1):
            lines.append(f"{i}. {issue}")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
