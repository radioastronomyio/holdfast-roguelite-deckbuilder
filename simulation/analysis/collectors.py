"""Telemetry collectors — aggregate raw MonteCarloResult into analysis-ready dataclasses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from agents.monte_carlo import MonteCarloResult
from campaign.runner import CampaignResult
from engine.encounters import CombatResult


# ---------------------------------------------------------------------------
# Per-collector output dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CardAnalysis:
    card_id: str
    total_plays: int
    plays_per_campaign: float         # avg across all campaigns that had this card available
    win_corr: float                   # Pearson-like: avg plays in wins minus avg plays in losses
    avg_damage_per_play: float        # display scale
    pick_rate_in_wins: float          # fraction of winning campaigns where card was played


@dataclass
class UpgradeAnalysis:
    card_id: str
    branch_a_picks: int
    branch_b_picks: int
    branch_a_rate: float              # branch A / (A + B)
    branch_b_rate: float
    branch_a_win_rate: float
    branch_b_win_rate: float
    pick_rate_in_wins: float


@dataclass
class RegionAnalysis:
    region_index: int                 # 0-based position in assault order
    win_rate: float                   # win rate given reaching this region
    death_rate: float                 # % of all campaigns that end (die) at this region
    ordering_frequency: float         # fraction of campaigns where this position is assaulted


@dataclass
class WorldCardAnalysis:
    card_id: str
    total_drawn: int
    total_accepted: int
    total_skipped: int
    accept_rate: float
    skip_rate: float
    accept_rate_in_wins: float
    accept_rate_in_losses: float


@dataclass
class SpeedAnalysis:
    ratios: list[float]               # all observed speed_action_ratios across all combats/entities
    mean_ratio: float
    max_ratio: float
    pct_above_3x: float               # % of (entity, combat) pairs with ratio > 3
    pct_above_5x: float
    flagged_count: int                # combats with any entity > 3x


@dataclass
class DifficultyCurve:
    region_indices: list[int]
    conditional_win_prob: dict[str, list[float]]  # strategy → list indexed by region_index
    attrition_rate: list[float]       # fraction dying per region (across all strategies)


@dataclass
class SeedClassification:
    all_win_seeds: list[int]
    all_loss_seeds: list[int]
    strategy_dependent_seeds: list[int]
    total_seeds: int
    all_win_rate: float
    all_loss_rate: float
    strategy_dependent_rate: float


@dataclass
class CombatDurationAnalysis:
    all_durations: list[int]
    mean_duration: float
    median_duration: float
    p95_duration: float
    turn_cap_rate: float              # fraction of combats hitting 200 turns
    durations_by_region: dict[int, list[int]]  # region_index → list of turn counts
    turn_cap_rate_by_region: dict[int, float]


@dataclass
class ConvergenceAnalysis:
    first_region_agreement: float     # fraction of seeds where all strategies pick same first region
    strategy_correlation: dict[str, dict[str, float]]  # pairwise win/loss agreement rates
    full_order_agreement: float       # fraction of seeds where all strategies use identical full region order


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _all_combat_results(mc_result: MonteCarloResult) -> list[tuple[int, str, int, CombatResult]]:
    """Yield (seed, strategy, region_idx, CombatResult) tuples."""
    out = []
    for seed, strats in mc_result.per_seed_results.items():
        for strategy_name, cr in strats.items():
            region_idx = 0
            for enc in cr.encounter_results:
                if isinstance(enc, CombatResult):
                    out.append((seed, strategy_name, region_idx, enc))
                    region_idx += 1
    return out


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------

def collect_card_stats(result: MonteCarloResult) -> dict[str, CardAnalysis]:
    """Per-card pick count, win-correlated usage, avg damage per play, plays per campaign."""
    plays_in_wins: dict[str, int] = {}
    plays_in_losses: dict[str, int] = {}
    total_plays: dict[str, int] = {}
    total_damage: dict[str, int] = {}
    winning_campaigns_played: dict[str, int] = {}  # card_id → # winning campaigns where card was played

    total_campaigns = 0
    total_wins = 0

    for seed, strats in result.per_seed_results.items():
        for strategy_name, cr in strats.items():
            total_campaigns += 1
            won = cr.victory
            if won:
                total_wins += 1
            played_this_campaign: set[str] = set()
            for enc in cr.encounter_results:
                if isinstance(enc, CombatResult):
                    for cp in enc.card_plays:
                        cid = cp.card_id
                        total_plays[cid] = total_plays.get(cid, 0) + 1
                        total_damage[cid] = total_damage.get(cid, 0) + cp.damage_total
                        if won:
                            plays_in_wins[cid] = plays_in_wins.get(cid, 0) + 1
                        else:
                            plays_in_losses[cid] = plays_in_losses.get(cid, 0) + 1
                        played_this_campaign.add(cid)
            if won:
                for cid in played_this_campaign:
                    winning_campaigns_played[cid] = winning_campaigns_played.get(cid, 0) + 1

    # campaigns per strategy
    campaigns_per_strategy = total_campaigns / len(result.config.strategies) if result.config.strategies else 1

    out: dict[str, CardAnalysis] = {}
    all_card_ids = set(total_plays) | set(plays_in_wins) | set(plays_in_losses)
    for cid in all_card_ids:
        tp = total_plays.get(cid, 0)
        w_plays = plays_in_wins.get(cid, 0)
        l_plays = plays_in_losses.get(cid, 0)
        win_corr = (w_plays / max(total_wins, 1)) - (l_plays / max(total_campaigns - total_wins, 1))
        avg_dmg = total_damage.get(cid, 0) / tp if tp > 0 else 0.0
        ppc = tp / campaigns_per_strategy if campaigns_per_strategy > 0 else 0.0
        pick_rate_win = winning_campaigns_played.get(cid, 0) / max(total_wins, 1)
        out[cid] = CardAnalysis(
            card_id=cid,
            total_plays=tp,
            plays_per_campaign=ppc,
            win_corr=win_corr,
            avg_damage_per_play=avg_dmg,
            pick_rate_in_wins=pick_rate_win,
        )
    return out


def _classify_branch(branch_key: str) -> str:
    """Classify a branch key as 'A' or 'B' family.

    Keys follow the pattern "1A", "1B", "2A_from_1A", "2B_from_1B", etc.
    The first 'A' or 'B' character found determines the family.
    """
    for char in branch_key:
        if char == 'A':
            return 'A'
        if char == 'B':
            return 'B'
    return 'unknown'


def collect_upgrade_stats(result: MonteCarloResult) -> dict[str, UpgradeAnalysis]:
    """Branch A vs B pick rates, win rate per branch."""
    branch_picks: dict[str, dict[str, int]] = {}  # card_id → {branch: count}
    branch_wins: dict[str, dict[str, int]] = {}
    total_with_upgrade: dict[str, int] = {}

    for seed, strats in result.per_seed_results.items():
        for strategy_name, cr in strats.items():
            for card_id, branch in cr.upgrade_branches_chosen.items():
                if card_id not in branch_picks:
                    branch_picks[card_id] = {}
                    branch_wins[card_id] = {}
                    total_with_upgrade[card_id] = 0
                branch_picks[card_id][branch] = branch_picks[card_id].get(branch, 0) + 1
                if cr.victory:
                    branch_wins[card_id][branch] = branch_wins[card_id].get(branch, 0) + 1
                total_with_upgrade[card_id] += 1

    out: dict[str, UpgradeAnalysis] = {}
    total_wins = sum(
        1 for strats in result.per_seed_results.values()
        for cr in strats.values() if cr.victory
    )

    for card_id, picks in branch_picks.items():
        a_picks = sum(count for key, count in picks.items() if _classify_branch(key) == 'A')
        b_picks = sum(count for key, count in picks.items() if _classify_branch(key) == 'B')
        total = a_picks + b_picks
        a_rate = a_picks / total if total > 0 else 0.0
        b_rate = b_picks / total if total > 0 else 0.0
        wins_by_branch = branch_wins[card_id]
        a_wins = sum(count for key, count in wins_by_branch.items() if _classify_branch(key) == 'A')
        b_wins = sum(count for key, count in wins_by_branch.items() if _classify_branch(key) == 'B')
        a_win_rate = a_wins / a_picks if a_picks > 0 else 0.0
        b_win_rate = b_wins / b_picks if b_picks > 0 else 0.0
        pick_rate_win = total_with_upgrade[card_id] / max(total_wins, 1)
        out[card_id] = UpgradeAnalysis(
            card_id=card_id,
            branch_a_picks=a_picks,
            branch_b_picks=b_picks,
            branch_a_rate=a_rate,
            branch_b_rate=b_rate,
            branch_a_win_rate=a_win_rate,
            branch_b_win_rate=b_win_rate,
            pick_rate_in_wins=pick_rate_win,
        )
    return out


def collect_region_stats(result: MonteCarloResult) -> dict[int, RegionAnalysis]:
    """Win/loss rate at each assault position, death rate, ordering frequency."""
    total_campaigns = 0
    campaigns_reaching: dict[int, int] = {}    # region_index → # campaigns that reached it
    wins_at_or_after: dict[int, int] = {}       # region_index → # campaigns that won after reaching it
    deaths_at: dict[int, int] = {}              # region_index → # campaigns that ended here

    for seed, strats in result.per_seed_results.items():
        for strategy_name, cr in strats.items():
            total_campaigns += 1
            n_regions = len(cr.region_order)
            for idx in range(n_regions):
                campaigns_reaching[idx] = campaigns_reaching.get(idx, 0) + 1
                if cr.victory:
                    wins_at_or_after[idx] = wins_at_or_after.get(idx, 0) + 1
            # Where did this campaign die?
            if not cr.victory and n_regions > 0:
                last_region_idx = n_regions - 1
                deaths_at[last_region_idx] = deaths_at.get(last_region_idx, 0) + 1

    out: dict[int, RegionAnalysis] = {}
    max_idx = max(campaigns_reaching.keys()) if campaigns_reaching else 0
    for idx in range(max_idx + 1):
        reached = campaigns_reaching.get(idx, 0)
        wins = wins_at_or_after.get(idx, 0)
        deaths = deaths_at.get(idx, 0)
        win_rate = wins / reached if reached > 0 else 0.0
        death_rate = deaths / total_campaigns if total_campaigns > 0 else 0.0
        ordering_freq = reached / total_campaigns if total_campaigns > 0 else 0.0
        out[idx] = RegionAnalysis(
            region_index=idx,
            win_rate=win_rate,
            death_rate=death_rate,
            ordering_frequency=ordering_freq,
        )
    return out


def collect_world_card_stats(result: MonteCarloResult) -> dict[str, WorldCardAnalysis]:
    """Accept rate, skip rate, accept rate in wins vs losses."""
    total_drawn: dict[str, int] = {}
    total_accepted: dict[str, int] = {}
    total_skipped: dict[str, int] = {}
    accepted_in_wins: dict[str, int] = {}
    accepted_in_losses: dict[str, int] = {}
    drawn_in_wins: dict[str, int] = {}
    drawn_in_losses: dict[str, int] = {}

    for seed, strats in result.per_seed_results.items():
        for strategy_name, cr in strats.items():
            won = cr.victory
            for cid in cr.world_cards_accepted_ids:
                total_drawn[cid] = total_drawn.get(cid, 0) + 1
                total_accepted[cid] = total_accepted.get(cid, 0) + 1
                if won:
                    accepted_in_wins[cid] = accepted_in_wins.get(cid, 0) + 1
                    drawn_in_wins[cid] = drawn_in_wins.get(cid, 0) + 1
                else:
                    accepted_in_losses[cid] = accepted_in_losses.get(cid, 0) + 1
                    drawn_in_losses[cid] = drawn_in_losses.get(cid, 0) + 1
            for cid in cr.world_cards_skipped_ids:
                total_drawn[cid] = total_drawn.get(cid, 0) + 1
                total_skipped[cid] = total_skipped.get(cid, 0) + 1
                if won:
                    drawn_in_wins[cid] = drawn_in_wins.get(cid, 0) + 1
                else:
                    drawn_in_losses[cid] = drawn_in_losses.get(cid, 0) + 1

    out: dict[str, WorldCardAnalysis] = {}
    for cid in total_drawn:
        td = total_drawn[cid]
        ta = total_accepted.get(cid, 0)
        ts = total_skipped.get(cid, 0)
        accept_rate = ta / td if td > 0 else 0.0
        skip_rate = ts / td if td > 0 else 0.0
        dw = drawn_in_wins.get(cid, 0)
        dl = drawn_in_losses.get(cid, 0)
        aw = accepted_in_wins.get(cid, 0)
        al = accepted_in_losses.get(cid, 0)
        accept_rate_wins = aw / dw if dw > 0 else 0.0
        accept_rate_losses = al / dl if dl > 0 else 0.0
        out[cid] = WorldCardAnalysis(
            card_id=cid,
            total_drawn=td,
            total_accepted=ta,
            total_skipped=ts,
            accept_rate=accept_rate,
            skip_rate=skip_rate,
            accept_rate_in_wins=accept_rate_wins,
            accept_rate_in_losses=accept_rate_losses,
        )
    return out


def collect_speed_stats(result: MonteCarloResult) -> SpeedAnalysis:
    """Distribution of action ratios, flagged combats."""
    all_ratios: list[float] = []
    flagged_combats = 0

    for seed, strats in result.per_seed_results.items():
        for strategy_name, cr in strats.items():
            for enc in cr.encounter_results:
                if isinstance(enc, CombatResult) and enc.speed_action_ratios:
                    ratios = list(enc.speed_action_ratios.values())
                    all_ratios.extend(ratios)
                    if any(r > 3 for r in ratios):
                        flagged_combats += 1

    if not all_ratios:
        return SpeedAnalysis(
            ratios=[], mean_ratio=0.0, max_ratio=0.0,
            pct_above_3x=0.0, pct_above_5x=0.0, flagged_count=0,
        )

    n = len(all_ratios)
    mean_r = sum(all_ratios) / n
    max_r = max(all_ratios)
    above3 = sum(1 for r in all_ratios if r > 3) / n
    above5 = sum(1 for r in all_ratios if r > 5) / n

    return SpeedAnalysis(
        ratios=all_ratios,
        mean_ratio=mean_r,
        max_ratio=max_r,
        pct_above_3x=above3,
        pct_above_5x=above5,
        flagged_count=flagged_combats,
    )


def collect_difficulty_curve(result: MonteCarloResult) -> DifficultyCurve:
    """Conditional win probability given reaching region N, attrition rate per region."""
    strategies = result.config.strategies
    # For each strategy: how many campaigns reach region idx, how many win
    reached: dict[str, dict[int, int]] = {s: {} for s in strategies}
    wins: dict[str, dict[int, int]] = {s: {} for s in strategies}
    total_reaching: dict[int, int] = {}
    total_dying: dict[int, int] = {}
    total_campaigns = 0

    for seed, strats in result.per_seed_results.items():
        for strategy_name, cr in strats.items():
            total_campaigns += 1
            n = len(cr.region_order)
            for idx in range(n):
                reached[strategy_name][idx] = reached[strategy_name].get(idx, 0) + 1
                total_reaching[idx] = total_reaching.get(idx, 0) + 1
                if cr.victory:
                    wins[strategy_name][idx] = wins[strategy_name].get(idx, 0) + 1
            if not cr.victory and n > 0:
                total_dying[n - 1] = total_dying.get(n - 1, 0) + 1

    max_idx = max(total_reaching.keys()) if total_reaching else 0
    region_indices = list(range(max_idx + 1))

    conditional_win_prob: dict[str, list[float]] = {}
    for s in strategies:
        probs = []
        for idx in region_indices:
            r = reached[s].get(idx, 0)
            w = wins[s].get(idx, 0)
            probs.append(w / r if r > 0 else 0.0)
        conditional_win_prob[s] = probs

    attrition = []
    total_all = total_campaigns
    for idx in region_indices:
        dying = total_dying.get(idx, 0)
        attrition.append(dying / total_all if total_all > 0 else 0.0)

    return DifficultyCurve(
        region_indices=region_indices,
        conditional_win_prob=conditional_win_prob,
        attrition_rate=attrition,
    )


def collect_seed_classification(result: MonteCarloResult) -> SeedClassification:
    """Bucket seeds into tiers."""
    all_win: list[int] = []
    all_loss: list[int] = []
    strategy_dependent: list[int] = []

    for seed, strats in result.per_seed_results.items():
        outcomes = [cr.victory for cr in strats.values()]
        if all(outcomes):
            all_win.append(seed)
        elif not any(outcomes):
            all_loss.append(seed)
        else:
            strategy_dependent.append(seed)

    total = len(result.per_seed_results)
    return SeedClassification(
        all_win_seeds=all_win,
        all_loss_seeds=all_loss,
        strategy_dependent_seeds=strategy_dependent,
        total_seeds=total,
        all_win_rate=len(all_win) / total if total > 0 else 0.0,
        all_loss_rate=len(all_loss) / total if total > 0 else 0.0,
        strategy_dependent_rate=len(strategy_dependent) / total if total > 0 else 0.0,
    )


def collect_combat_duration(result: MonteCarloResult) -> CombatDurationAnalysis:
    """Turn count distributions, turn-cap hit rate, by region."""
    all_durations: list[int] = []
    cap_hits = 0
    total_combats = 0
    durations_by_region: dict[int, list[int]] = {}
    cap_hits_by_region: dict[int, int] = {}

    for seed, strats in result.per_seed_results.items():
        for strategy_name, cr in strats.items():
            region_idx = 0
            for enc in cr.encounter_results:
                if isinstance(enc, CombatResult):
                    d = enc.turns_taken
                    all_durations.append(d)
                    total_combats += 1
                    if enc.hit_turn_cap:
                        cap_hits += 1
                        cap_hits_by_region[region_idx] = cap_hits_by_region.get(region_idx, 0) + 1
                    if region_idx not in durations_by_region:
                        durations_by_region[region_idx] = []
                    durations_by_region[region_idx].append(d)
                    region_idx += 1

    if not all_durations:
        return CombatDurationAnalysis(
            all_durations=[], mean_duration=0.0, median_duration=0.0,
            p95_duration=0.0, turn_cap_rate=0.0,
            durations_by_region={}, turn_cap_rate_by_region={},
        )

    sorted_d = sorted(all_durations)
    n = len(sorted_d)
    mean_d = sum(sorted_d) / n
    median_d = float(sorted_d[n // 2])
    p95_d = float(sorted_d[int(n * 0.95)])
    cap_rate = cap_hits / total_combats if total_combats > 0 else 0.0

    cap_rate_by_region: dict[int, float] = {}
    for idx, durs in durations_by_region.items():
        ch = cap_hits_by_region.get(idx, 0)
        cap_rate_by_region[idx] = ch / len(durs) if durs else 0.0

    return CombatDurationAnalysis(
        all_durations=all_durations,
        mean_duration=mean_d,
        median_duration=median_d,
        p95_duration=p95_d,
        turn_cap_rate=cap_rate,
        durations_by_region=durations_by_region,
        turn_cap_rate_by_region=cap_rate_by_region,
    )


def collect_convergence_deep(result: MonteCarloResult) -> ConvergenceAnalysis:
    """Strategy correlation matrix and region ordering agreement."""
    strategies = result.config.strategies
    seeds = list(result.per_seed_results.keys())
    total = len(seeds)

    # First-region agreement
    first_agree = 0
    full_agree = 0
    for seed in seeds:
        strats = result.per_seed_results[seed]
        first_regions = set()
        full_orders = set()
        for sname, cr in strats.items():
            if cr.region_order:
                first_regions.add(cr.region_order[0])
                full_orders.add(tuple(cr.region_order))
        if len(first_regions) <= 1:
            first_agree += 1
        if len(full_orders) <= 1:
            full_agree += 1

    # Pairwise win/loss agreement
    pairwise: dict[str, dict[str, float]] = {s: {} for s in strategies}
    for i, s1 in enumerate(strategies):
        for j, s2 in enumerate(strategies):
            if s1 == s2:
                pairwise[s1][s2] = 1.0
                continue
            agree = 0
            compared = 0
            for seed in seeds:
                strats = result.per_seed_results[seed]
                if s1 in strats and s2 in strats:
                    if strats[s1].victory == strats[s2].victory:
                        agree += 1
                    compared += 1
            pairwise[s1][s2] = agree / compared if compared > 0 else 0.0

    return ConvergenceAnalysis(
        first_region_agreement=first_agree / total if total > 0 else 0.0,
        strategy_correlation=pairwise,
        full_order_agreement=full_agree / total if total > 0 else 0.0,
    )
