"""Tests for combat system using real game data."""

import pytest

from src.systems.combat_system import CombatSystem, CombatResult
from src.entities.civilization import Civilization
from src.entities.unit_types import create_warrior, create_archer, create_spearman
from src.map.tile import Tile, TerrainType


@pytest.fixture
def player_civ():
    """Create player civilization."""
    return Civilization(name="Player", color_key="PLAYER")


@pytest.fixture
def enemy_civ():
    """Create enemy civilization."""
    return Civilization(name="Enemy", color_key="AI_AGGRESSIVE", is_ai=True)


@pytest.fixture
def grass_tile():
    """Create grass tile (no defense bonus)."""
    return Tile(x=0, y=0, terrain=TerrainType.GRASS)


@pytest.fixture
def forest_tile():
    """Create forest tile (25% defense bonus)."""
    return Tile(x=1, y=0, terrain=TerrainType.FOREST)


class TestDamageCalculation:
    """Tests for damage calculation."""

    def test_warrior_vs_warrior_on_grass(self, player_civ, enemy_civ, grass_tile):
        """Test damage with equal units on grass.

        Warrior stats: ATK=15, DEF=10
        Base damage = 15 * (100 / (100 + 10)) = 13.64 -> 13
        """
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 1, 0)

        damage = CombatSystem.calculate_damage(attacker, defender, grass_tile, distance=1)

        # Expected: 15 * (100/110) * 1.0 * 1.0 * 1.0 = 13.64 -> 13
        assert damage == 13

    def test_warrior_vs_spearman_on_grass(self, player_civ, enemy_civ, grass_tile):
        """Test warrior attacking high-defense spearman.

        Spearman stats: DEF=15
        """
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_spearman(enemy_civ, 1, 0)

        damage = CombatSystem.calculate_damage(attacker, defender, grass_tile, distance=1)

        # Expected: 15 * (100/115) = 13.04 -> 13
        assert damage == 13

    def test_terrain_defense_reduces_damage(self, player_civ, enemy_civ, grass_tile, forest_tile):
        """Test that forest terrain reduces damage by 25%."""
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 1, 0)

        damage_grass = CombatSystem.calculate_damage(attacker, defender, grass_tile, distance=1)
        damage_forest = CombatSystem.calculate_damage(attacker, defender, forest_tile, distance=1)

        # Forest should reduce damage by roughly 25%
        assert damage_forest < damage_grass
        # Allow for rounding: forest damage should be 70-80% of grass damage
        ratio = damage_forest / damage_grass
        assert 0.70 <= ratio <= 0.80

    def test_damaged_attacker_deals_less_damage(self, player_civ, enemy_civ, grass_tile):
        """Test that damaged units deal less damage."""
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 1, 0)

        full_health_damage = CombatSystem.calculate_damage(attacker, defender, grass_tile, distance=1)

        # Damage the attacker to 50% health
        attacker.health = attacker.max_health // 2

        half_health_damage = CombatSystem.calculate_damage(attacker, defender, grass_tile, distance=1)

        # At 50% health, damage modifier is 0.5 + (0.5 * 0.5) = 0.75
        assert half_health_damage < full_health_damage
        # Allow for rounding
        ratio = half_health_damage / full_health_damage
        assert 0.70 <= ratio <= 0.80

    def test_ranged_max_range_penalty(self, player_civ, enemy_civ, grass_tile):
        """Test that ranged units deal 75% damage at max range."""
        attacker = create_archer(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 2, 0)

        # Archer at range 1
        damage_close = CombatSystem.calculate_damage(attacker, defender, grass_tile, distance=1)

        # Archer at max range (2)
        damage_far = CombatSystem.calculate_damage(attacker, defender, grass_tile, distance=2)

        # Max range should deal roughly 75% damage
        assert damage_far < damage_close
        # Allow for rounding
        ratio = damage_far / damage_close
        assert 0.70 <= ratio <= 0.80

    def test_minimum_damage_is_one(self, player_civ, enemy_civ, forest_tile):
        """Test that minimum damage is always 1."""
        attacker = create_archer(player_civ, 0, 0)
        defender = create_spearman(enemy_civ, 2, 0)  # High defense

        # Even weak attack should do at least 1 damage
        attacker.health = 10  # Very damaged

        damage = CombatSystem.calculate_damage(attacker, defender, forest_tile, distance=2)

        assert damage >= 1


class TestCounterattack:
    """Tests for counterattack logic."""

    def test_melee_can_counter_melee(self, player_civ, enemy_civ):
        """Melee units can counterattack melee attackers."""
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 1, 0)

        assert CombatSystem.can_counterattack(defender, attacker, distance=1)

    def test_melee_cannot_counter_ranged_at_distance(self, player_civ, enemy_civ):
        """Melee units cannot counterattack ranged attackers at range > 1."""
        attacker = create_archer(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 2, 0)

        assert not CombatSystem.can_counterattack(defender, attacker, distance=2)

    def test_ranged_can_counter_melee(self, player_civ, enemy_civ):
        """Ranged units can counterattack melee at distance 1."""
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_archer(enemy_civ, 1, 0)

        assert CombatSystem.can_counterattack(defender, attacker, distance=1)

    def test_ranged_can_counter_ranged(self, player_civ, enemy_civ):
        """Ranged units can counterattack ranged attackers in range."""
        attacker = create_archer(player_civ, 0, 0)
        defender = create_archer(enemy_civ, 2, 0)

        assert CombatSystem.can_counterattack(defender, attacker, distance=2)

    def test_dead_defender_cannot_counter(self, player_civ, enemy_civ):
        """Dead defenders cannot counterattack."""
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 1, 0)
        defender.health = 0  # Dead

        assert not CombatSystem.can_counterattack(defender, attacker, distance=1)


class TestCombatResolution:
    """Tests for full combat resolution."""

    def test_combat_damages_both_units(self, player_civ, enemy_civ):
        """Combat should damage both attacker and defender."""
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 1, 0)
        attacker_tile = Tile(x=0, y=0, terrain=TerrainType.GRASS)
        defender_tile = Tile(x=1, y=0, terrain=TerrainType.GRASS)

        initial_attacker_hp = attacker.health
        initial_defender_hp = defender.health

        result = CombatSystem.resolve_combat(attacker, defender, attacker_tile, defender_tile)

        assert defender.health < initial_defender_hp
        assert attacker.health < initial_attacker_hp
        assert result.defender_damage > 0
        assert result.attacker_damage > 0

    def test_combat_marks_attacker_as_attacked(self, player_civ, enemy_civ):
        """Attacker should be marked as having attacked."""
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 1, 0)
        attacker_tile = Tile(x=0, y=0, terrain=TerrainType.GRASS)
        defender_tile = Tile(x=1, y=0, terrain=TerrainType.GRASS)

        assert not attacker.has_attacked

        CombatSystem.resolve_combat(attacker, defender, attacker_tile, defender_tile)

        assert attacker.has_attacked

    def test_ranged_attack_no_counterattack(self, player_civ, enemy_civ):
        """Ranged attacks at distance shouldn't receive counterattacks from melee."""
        attacker = create_archer(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 2, 0)
        attacker_tile = Tile(x=0, y=0, terrain=TerrainType.GRASS)
        defender_tile = Tile(x=2, y=0, terrain=TerrainType.GRASS)

        initial_attacker_hp = attacker.health

        result = CombatSystem.resolve_combat(attacker, defender, attacker_tile, defender_tile)

        # Attacker should take no damage
        assert attacker.health == initial_attacker_hp
        assert result.attacker_damage == 0
        assert result.defender_damage > 0

    def test_combat_can_kill_defender(self, player_civ, enemy_civ):
        """Combat should be able to kill the defender."""
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 1, 0)
        defender.health = 5  # Low health
        attacker_tile = Tile(x=0, y=0, terrain=TerrainType.GRASS)
        defender_tile = Tile(x=1, y=0, terrain=TerrainType.GRASS)

        result = CombatSystem.resolve_combat(attacker, defender, attacker_tile, defender_tile)

        assert not defender.is_alive
        assert result.defender_killed


class TestCombatOdds:
    """Tests for combat odds calculation."""

    def test_favorable_odds_when_stronger(self, player_civ, enemy_civ):
        """Stronger attacker should have favorable odds."""
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_archer(enemy_civ, 1, 0)  # Lower defense
        defender_tile = Tile(x=1, y=0, terrain=TerrainType.GRASS)

        odds = CombatSystem.get_combat_odds(attacker, defender, defender_tile)

        # Warrior attacking archer should be favorable
        assert odds > 1.0

    def test_terrain_affects_odds(self, player_civ, enemy_civ):
        """Forest terrain should reduce attacker's odds."""
        attacker = create_warrior(player_civ, 0, 0)
        defender = create_warrior(enemy_civ, 1, 0)
        grass_tile = Tile(x=1, y=0, terrain=TerrainType.GRASS)
        forest_tile = Tile(x=1, y=0, terrain=TerrainType.FOREST)

        odds_grass = CombatSystem.get_combat_odds(attacker, defender, grass_tile)
        odds_forest = CombatSystem.get_combat_odds(attacker, defender, forest_tile)

        assert odds_forest < odds_grass
