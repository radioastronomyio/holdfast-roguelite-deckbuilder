"""Tests for enemy generation."""

import random

import pytest

from models.entity import Enemy
from models.modifier import STAT_SCALE
from models.enums import Stat, AiHeuristic
from generation.enemies import generate_enemy


CARD_IDS = ["arcane_strike_01", "shield_bash_01", "sweeping_blade_01", "frost_bolt_01", "power_surge_01"]


class TestEnemyGeneration:
    def test_higher_difficulty_higher_stats(self):
        """difficulty=6 has higher total stats than difficulty=1."""
        rng1 = random.Random(42)
        low = generate_enemy(rng1, difficulty=1, available_card_ids=CARD_IDS)
        rng2 = random.Random(42)
        high = generate_enemy(rng2, difficulty=6, available_card_ids=CARD_IDS)

        total_low = sum(low.base_stats.values())
        total_high = sum(high.base_stats.values())
        assert total_high > total_low

    def test_elite_enemies_stronger(self):
        """Elite has higher total stats than non-elite at same difficulty."""
        rng1 = random.Random(42)
        normal = generate_enemy(rng1, difficulty=3, available_card_ids=CARD_IDS, is_elite=False)
        rng2 = random.Random(42)
        elite = generate_enemy(rng2, difficulty=3, available_card_ids=CARD_IDS, is_elite=True)

        total_normal = sum(normal.base_stats.values())
        total_elite = sum(elite.base_stats.values())
        assert total_elite > total_normal

    def test_card_pool_from_available(self):
        """Enemy card_pool is a subset of available_card_ids."""
        rng = random.Random(42)
        enemy = generate_enemy(rng, difficulty=3, available_card_ids=CARD_IDS)
        for card in enemy.card_pool:
            assert card in CARD_IDS

    def test_card_pool_non_empty(self):
        """Card pool has at least 2 cards."""
        rng = random.Random(42)
        enemy = generate_enemy(rng, difficulty=3, available_card_ids=CARD_IDS)
        assert len(enemy.card_pool) >= 2

    def test_deterministic_same_seed(self):
        """Same seed + params produce identical enemies."""
        e1 = generate_enemy(random.Random(42), difficulty=3, available_card_ids=CARD_IDS)
        e2 = generate_enemy(random.Random(42), difficulty=3, available_card_ids=CARD_IDS)
        assert e1.base_stats == e2.base_stats
        assert e1.card_pool == e2.card_pool
        assert e1.ai_heuristic_tag == e2.ai_heuristic_tag

    def test_valid_ai_heuristic_tag(self):
        """Tag is one of aggressive/defensive/balanced."""
        for seed in range(20):
            rng = random.Random(seed)
            enemy = generate_enemy(rng, difficulty=3, available_card_ids=CARD_IDS)
            assert enemy.ai_heuristic_tag in [
                AiHeuristic.aggressive,
                AiHeuristic.defensive,
                AiHeuristic.balanced,
            ]

    def test_stats_pre_scaled(self):
        """All base_stats values are multiples of STAT_SCALE."""
        rng = random.Random(42)
        enemy = generate_enemy(rng, difficulty=3, available_card_ids=CARD_IDS)
        for stat in Stat:
            assert enemy.base_stats[stat] % STAT_SCALE == 0, (
                f"{stat} = {enemy.base_stats[stat]} not a multiple of {STAT_SCALE}"
            )

    def test_elite_flag_set(self):
        """is_elite=True produces enemy with is_elite=True."""
        rng = random.Random(42)
        enemy = generate_enemy(rng, difficulty=3, available_card_ids=CARD_IDS, is_elite=True)
        assert enemy.is_elite is True
