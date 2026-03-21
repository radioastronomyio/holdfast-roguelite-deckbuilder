"""Tests for deck mechanics (M3b Task 6.1)."""
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.card import Card
from models.enums import Stat, Operation, Target, Stacking
from engine.turn_order import (
    CombatEntity,
    initialize_deck,
    draw_cards,
    discard_hand,
    discard_card,
    HAND_SIZE,
)
from engine.encounters import resolve_combat


def make_mod(stat, operation, value, duration=0, target=Target.ENEMY_SINGLE):
    return Modifier(stat=stat, operation=operation, value=value, duration=duration,
                    target=target, stacking=Stacking.replace, tags=[])


def make_card(id, cost=1, damage=5, deck_copies=1, target=Target.ENEMY_SINGLE):
    return Card(
        id=id, name=id, energy_cost=cost, deck_copies=deck_copies,
        effects=[make_mod(Stat.HP, Operation.FLAT_SUB, damage * STAT_SCALE, target=target)],
    )


def make_entity(id, hp=100, speed=100000, energy=10, is_player=True, card_pool=None):
    return CombatEntity(
        id=id, name=id,
        base_stats={
            Stat.HP: hp * STAT_SCALE,
            Stat.Speed: speed,
            Stat.Power: 0,
            Stat.Defense: 0,
            Stat.Energy: energy,
        },
        is_player=is_player,
        card_pool=card_pool or [],
        active_modifiers=[],
    )


class TestInitializeDeck:
    def test_initialize_deck(self):
        """deck_copies controls how many copies appear in draw_pile."""
        cards = {
            "a": make_card("a", deck_copies=3),
            "b": make_card("b", deck_copies=2),
            "c": make_card("c", deck_copies=1),
        }
        entity = make_entity("p", card_pool=["a", "b", "c"])
        rng = random.Random(1)
        initialize_deck(entity, cards, rng)
        assert len(entity.draw_pile) == 6  # 3+2+1
        assert entity.hand == []
        assert entity.discard_pile == []

    def test_initialize_deck_empty_pool(self):
        """Empty card_pool → empty draw pile."""
        entity = make_entity("p", card_pool=[])
        rng = random.Random(1)
        initialize_deck(entity, {}, rng)
        assert entity.draw_pile == []
        assert entity.hand == []
        assert entity.discard_pile == []


class TestDrawCards:
    def test_draw_cards_basic(self):
        """Drawing 5 from a 28-card deck leaves 23 in draw_pile."""
        cards = {"x": make_card("x", deck_copies=1)}
        # Build entity with 28-card pool manually
        pool = ["x"] * 28
        entity = make_entity("p", card_pool=["x"])
        entity.draw_pile = list(pool)
        entity.hand = []
        entity.discard_pile = []
        rng = random.Random(1)
        draw_cards(entity, 5, rng)
        assert len(entity.hand) == 5
        assert len(entity.draw_pile) == 23

    def test_draw_cards_reshuffle(self):
        """When draw_pile runs out, discard is reshuffled in and drawing continues."""
        entity = make_entity("p", card_pool=[])
        entity.draw_pile = ["a", "b", "c"]
        entity.discard_pile = ["d", "e", "f", "g", "h", "i", "j", "k", "l", "m"]
        entity.hand = []
        rng = random.Random(42)
        draw_cards(entity, 8, rng)
        assert len(entity.hand) == 8
        # draw_pile had 3, discard had 10 → reshuffle → total available 13 → drew 8, 5 remain
        assert len(entity.draw_pile) + len(entity.discard_pile) == 5

    def test_draw_cards_empty(self):
        """Drawing from an empty deck does not crash and leaves hand empty."""
        entity = make_entity("p", card_pool=[])
        entity.draw_pile = []
        entity.discard_pile = []
        entity.hand = []
        rng = random.Random(1)
        draw_cards(entity, 5, rng)
        assert entity.hand == []


class TestDiscardFunctions:
    def test_discard_hand(self):
        """discard_hand moves all cards from hand to discard_pile."""
        entity = make_entity("p", card_pool=[])
        entity.hand = ["a", "b", "c"]
        entity.discard_pile = []
        discard_hand(entity)
        assert entity.hand == []
        assert len(entity.discard_pile) == 3
        assert set(entity.discard_pile) == {"a", "b", "c"}

    def test_discard_card(self):
        """discard_card removes a specific card from hand to discard_pile."""
        entity = make_entity("p", card_pool=[])
        entity.hand = ["a", "b", "c"]
        entity.discard_pile = []
        discard_card(entity, "b")
        assert entity.hand == ["a", "c"]
        assert entity.discard_pile == ["b"]


class TestDeterminism:
    def test_deterministic_shuffle(self):
        """Same RNG seed produces same draw_pile order."""
        cards = {"x": make_card("x", deck_copies=3), "y": make_card("y", deck_copies=2)}
        pool = ["x", "y"]

        e1 = make_entity("p1", card_pool=pool)
        e2 = make_entity("p2", card_pool=pool)
        initialize_deck(e1, cards, random.Random(99))
        initialize_deck(e2, cards, random.Random(99))
        assert e1.draw_pile == e2.draw_pile

        e3 = make_entity("p3", card_pool=pool)
        initialize_deck(e3, cards, random.Random(100))
        # Different seed → different order (with high probability for >=5 cards)
        # We just verify the content is the same even if order differs
        assert sorted(e1.draw_pile) == sorted(e3.draw_pile)


class TestMultiPlayTurn:
    def test_multi_play_turn(self):
        """An entity with enough Energy plays multiple cards in one CT turn."""
        # Player has 10 energy, cards cost 1 each — should play multiple cards
        card = make_card("atk", cost=1, damage=1, deck_copies=3)
        player = make_entity("player", hp=200, speed=200000, energy=5, is_player=True,
                             card_pool=["atk"])
        enemy = make_entity("enemy", hp=500, speed=100000, energy=1, is_player=False,
                            card_pool=["atk"])
        cards_by_id = {"atk": card}
        result = resolve_combat([player], [enemy], cards_by_id=cards_by_id,
                                rng=random.Random(42))
        # Player has 5 energy and cost-1 cards → can play up to 5 cards per turn
        player_plays = [cp for cp in result.card_plays if cp.caster_id == "player"]
        first_turn_plays = [cp for cp in player_plays if cp.turn_number == 1]
        assert len(first_turn_plays) >= 2, (
            f"Expected multiple plays in turn 1, got {len(first_turn_plays)}"
        )
