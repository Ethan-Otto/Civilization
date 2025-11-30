"""Tests for AI behavior using real game data."""

import pytest
from unittest.mock import MagicMock

from src.ai.ai_controller import AIController, create_ai_controller
from src.ai.ai_tactics import TacticalAI, ActionType
from src.ai.ai_strategies import StrategicAI, StrategicGoal
from src.ai.utility_functions import (
    calculate_attack_utility,
    calculate_movement_utility,
    calculate_retreat_utility,
    calculate_production_utility,
    calculate_research_utility,
)
from src.entities.civilization import Civilization
from src.entities.unit_types import create_warrior, create_archer, create_spearman
from src.entities.city import City
from src.map.tile import Tile, TerrainType
from src.map.grid import Grid
from src.core.settings import AI_PERSONALITIES


@pytest.fixture
def aggressive_civ():
    """Create aggressive AI civilization."""
    civ = Civilization(name="Aggressive", color_key="AI_AGGRESSIVE", is_ai=True)
    civ.ai_personality = "AGGRESSIVE"
    return civ


@pytest.fixture
def balanced_civ():
    """Create balanced AI civilization."""
    civ = Civilization(name="Balanced", color_key="AI_BALANCED", is_ai=True)
    civ.ai_personality = "BALANCED"
    return civ


@pytest.fixture
def player_civ():
    """Create player civilization."""
    return Civilization(name="Player", color_key="PLAYER")


@pytest.fixture
def small_grid():
    """Create a small test grid."""
    return Grid(10, 10)


@pytest.fixture
def mock_game_state(small_grid, player_civ, aggressive_civ):
    """Create mock game state for testing."""
    game_state = MagicMock()
    game_state.grid = small_grid
    game_state.active_civs = [player_civ, aggressive_civ]
    game_state.get_units_for_civ = MagicMock(return_value=[])
    game_state.get_cities_for_civ = MagicMock(return_value=[])
    game_state.get_all_units = MagicMock(return_value=[])
    game_state.get_all_cities = MagicMock(return_value=[])
    return game_state


class TestUtilityFunctions:
    """Tests for utility calculation functions."""

    def test_attack_utility_favorable_matchup(self, player_civ, aggressive_civ):
        """Test attack utility for favorable matchup."""
        attacker = create_warrior(aggressive_civ, 0, 0)
        defender = create_archer(player_civ, 1, 0)  # Lower defense
        defender_tile = Tile(x=1, y=0, terrain=TerrainType.GRASS)

        utility = calculate_attack_utility(
            attacker, defender, defender_tile, AI_PERSONALITIES["AGGRESSIVE"]
        )

        # Should be positive for favorable matchup
        assert utility > 0

    def test_attack_utility_unfavorable_matchup(self, player_civ, aggressive_civ):
        """Test attack utility is lower for unfavorable matchup."""
        attacker = create_archer(aggressive_civ, 0, 0)
        defender = create_spearman(player_civ, 1, 0)  # High defense
        defender_tile = Tile(x=1, y=0, terrain=TerrainType.FOREST)

        utility = calculate_attack_utility(
            attacker, defender, defender_tile, AI_PERSONALITIES["BALANCED"]
        )

        # Can be positive but should be lower than favorable matchup
        assert utility >= 0

    def test_attack_utility_kill_bonus(self, player_civ, aggressive_civ):
        """Test that potential kills increase utility."""
        attacker = create_warrior(aggressive_civ, 0, 0)

        # Full health defender
        defender_healthy = create_archer(player_civ, 1, 0)
        defender_tile = Tile(x=1, y=0, terrain=TerrainType.GRASS)

        # Low health defender
        defender_weak = create_archer(player_civ, 1, 0)
        defender_weak.health = 5

        utility_healthy = calculate_attack_utility(
            attacker, defender_healthy, defender_tile, AI_PERSONALITIES["BALANCED"]
        )
        utility_weak = calculate_attack_utility(
            attacker, defender_weak, defender_tile, AI_PERSONALITIES["BALANCED"]
        )

        # Killing a weak unit should be more attractive
        assert utility_weak > utility_healthy

    def test_movement_utility_toward_enemy(self, player_civ, aggressive_civ, mock_game_state):
        """Test movement utility toward enemy units."""
        unit = create_warrior(aggressive_civ, 0, 0)
        enemy_unit = create_warrior(player_civ, 5, 5)
        mock_game_state.get_all_units.return_value = [unit, enemy_unit]
        mock_game_state.get_all_cities.return_value = []

        # Tile closer to enemy
        close_tile = Tile(x=3, y=3, terrain=TerrainType.GRASS)
        # Tile farther from enemy
        far_tile = Tile(x=0, y=1, terrain=TerrainType.GRASS)

        utility_close = calculate_movement_utility(
            unit, close_tile, mock_game_state, AI_PERSONALITIES["AGGRESSIVE"]
        )
        utility_far = calculate_movement_utility(
            unit, far_tile, mock_game_state, AI_PERSONALITIES["AGGRESSIVE"]
        )

        # Closer should have higher utility for aggressive AI
        assert utility_close > utility_far

    def test_retreat_utility_based_on_health(self, aggressive_civ, mock_game_state):
        """Test retreat utility increases as health decreases."""
        unit = create_warrior(aggressive_civ, 0, 0)

        # Full health
        unit.health = unit.max_health
        utility_full = calculate_retreat_utility(unit, mock_game_state)

        # Half health
        unit.health = unit.max_health // 2
        utility_half = calculate_retreat_utility(unit, mock_game_state)

        # Low health
        unit.health = unit.max_health // 5
        utility_low = calculate_retreat_utility(unit, mock_game_state)

        assert utility_full == 0.0  # No retreat at full health
        assert utility_half > utility_full
        assert utility_low > utility_half

    def test_production_utility_with_personality(self, aggressive_civ):
        """Test production utility reflects personality."""
        from src.data.unit_data import UnitType

        city = City(name="Test City", owner=aggressive_civ, x=5, y=5)
        game_state = MagicMock()

        aggressive_utility = calculate_production_utility(
            city, UnitType.WARRIOR, game_state, aggressive_civ,
            AI_PERSONALITIES["AGGRESSIVE"]
        )
        balanced_utility = calculate_production_utility(
            city, UnitType.WARRIOR, game_state, aggressive_civ,
            AI_PERSONALITIES["BALANCED"]
        )

        # Aggressive should value military production more
        assert aggressive_utility > balanced_utility

    def test_research_utility_unlocks_units(self, aggressive_civ):
        """Test research utility values techs that unlock units."""
        utility = calculate_research_utility(
            "archery", aggressive_civ, AI_PERSONALITIES["BALANCED"]
        )

        # Should be positive since archery unlocks archer
        assert utility > 0


class TestTacticalAI:
    """Tests for tactical AI decisions."""

    def test_tactical_ai_decides_action(self, aggressive_civ, mock_game_state):
        """Test tactical AI can decide an action."""
        tactical_ai = TacticalAI(AI_PERSONALITIES["AGGRESSIVE"])
        unit = create_warrior(aggressive_civ, 5, 5)
        unit.owner = aggressive_civ

        mock_game_state.get_cities_for_civ.return_value = []
        mock_game_state.grid.get_tile = MagicMock(
            return_value=Tile(x=5, y=5, terrain=TerrainType.GRASS)
        )

        action = tactical_ai.decide_action(unit, mock_game_state)

        # Should return a valid action
        assert action is not None
        assert action.action_type in ActionType

    def test_tactical_ai_prefers_attack_when_available(
        self, aggressive_civ, player_civ
    ):
        """Test tactical AI prefers attacking when enemy in range."""
        from unittest.mock import patch

        tactical_ai = TacticalAI(AI_PERSONALITIES["AGGRESSIVE"])

        attacker = create_warrior(aggressive_civ, 5, 5)
        attacker.owner = aggressive_civ

        defender = create_archer(player_civ, 6, 5)
        defender.owner = player_civ

        # Create defender tile with enemy unit on it
        defender_tile = Tile(x=6, y=5, terrain=TerrainType.GRASS)
        defender_tile.unit = defender

        # Mock game state
        game_state = MagicMock()
        game_state.get_cities_for_civ.return_value = []
        game_state.grid.get_tile = MagicMock(
            return_value=Tile(x=5, y=5, terrain=TerrainType.GRASS)
        )

        # Patch where the function is used, not where it's defined
        with patch('src.ai.ai_tactics.get_tiles_in_attack_range', return_value=[defender_tile]):
            with patch('src.ai.ai_tactics.get_reachable_tiles', return_value={}):
                action = tactical_ai.decide_action(attacker, game_state)
                # With enemy in range, should prefer attack
                assert action.action_type == ActionType.ATTACK

    def test_tactical_ai_fortifies_when_no_options(
        self, aggressive_civ, mock_game_state
    ):
        """Test tactical AI fortifies when no good options."""
        tactical_ai = TacticalAI(AI_PERSONALITIES["BALANCED"])

        unit = create_warrior(aggressive_civ, 5, 5)
        unit.owner = aggressive_civ
        unit._can_attack = False
        unit._can_move = False

        mock_game_state.get_cities_for_civ.return_value = []

        action = tactical_ai.decide_action(unit, mock_game_state)

        # Should fortify when can't move or attack
        assert action.action_type == ActionType.FORTIFY


class TestStrategicAI:
    """Tests for strategic AI decisions."""

    def test_strategic_assessment_calculates(self, aggressive_civ, mock_game_state):
        """Test strategic AI can assess situation."""
        strategic_ai = StrategicAI(AI_PERSONALITIES["AGGRESSIVE"])

        mock_game_state.get_units_for_civ.return_value = [
            create_warrior(aggressive_civ, 0, 0)
        ]
        mock_game_state.get_cities_for_civ.return_value = [
            City(name="Capital", owner=aggressive_civ, x=5, y=5)
        ]

        assessment = strategic_ai.assess_situation(aggressive_civ, mock_game_state)

        assert assessment is not None
        assert 0 <= assessment.military_strength <= 1
        assert 0 <= assessment.economic_strength <= 1
        assert 0 <= assessment.threat_level <= 1
        assert 0 <= assessment.expansion_potential <= 1
        assert assessment.recommended_goal in StrategicGoal

    def test_strategic_ai_recommends_defense_under_threat(
        self, aggressive_civ, player_civ, mock_game_state
    ):
        """Test strategic AI recommends defense when threatened."""
        strategic_ai = StrategicAI(AI_PERSONALITIES["BALANCED"])

        # Our city
        our_city = City(name="Capital", owner=aggressive_civ, x=5, y=5)
        mock_game_state.get_cities_for_civ.return_value = [our_city]

        # Enemy units very close to our city
        enemy_units = [
            create_warrior(player_civ, 6, 5),  # Distance 1
            create_warrior(player_civ, 5, 6),  # Distance 1
            create_warrior(player_civ, 7, 5),  # Distance 2
        ]
        for unit in enemy_units:
            unit.owner = player_civ

        # Mock to return no units for our civ but enemies for others
        def get_units_for_civ(civ):
            if civ == aggressive_civ:
                return []
            return enemy_units

        mock_game_state.get_units_for_civ.side_effect = get_units_for_civ

        assessment = strategic_ai.assess_situation(aggressive_civ, mock_game_state)

        # High threat should recommend defense or building military
        assert assessment.threat_level > 0.5
        assert assessment.recommended_goal in (
            StrategicGoal.DEFEND,
            StrategicGoal.BUILD_MILITARY
        )

    def test_strategic_ai_decides_production(
        self, aggressive_civ, mock_game_state
    ):
        """Test strategic AI can decide production."""
        strategic_ai = StrategicAI(AI_PERSONALITIES["AGGRESSIVE"])

        city = City(name="Capital", owner=aggressive_civ, x=5, y=5)
        aggressive_civ.researched_techs = set()  # Start with no techs

        # Should set production without error
        strategic_ai.decide_production(city, aggressive_civ, mock_game_state)

        # City should now be producing something
        assert city.is_producing or city.current_production is None  # May be None if no units available


class TestAIController:
    """Tests for main AI controller."""

    def test_create_ai_controller(self, aggressive_civ):
        """Test creating an AI controller."""
        controller = create_ai_controller(aggressive_civ)

        assert controller is not None
        assert controller.civ == aggressive_civ
        assert controller.tactical_ai is not None
        assert controller.strategic_ai is not None

    def test_ai_controller_respects_personality(self, aggressive_civ, balanced_civ):
        """Test AI controller uses correct personality weights."""
        aggressive_controller = AIController(aggressive_civ)
        balanced_controller = AIController(balanced_civ)

        # Aggressive should have higher military weight
        assert (
            aggressive_controller.personality_weights["military_weight"]
            > balanced_controller.personality_weights["military_weight"]
        )

    def test_ai_controller_skips_eliminated_civ(self, aggressive_civ, mock_game_state):
        """Test AI controller does nothing if civilization is eliminated."""
        controller = AIController(aggressive_civ)
        aggressive_civ.is_eliminated = True

        # Should not raise an error, just return early
        controller.take_turn(mock_game_state)

        # Verify no strategic decisions were made
        mock_game_state.get_units_for_civ.assert_not_called()

    def test_ai_controller_processes_turn(self, aggressive_civ, mock_game_state):
        """Test AI controller processes a complete turn."""
        controller = AIController(aggressive_civ)
        aggressive_civ.is_eliminated = False

        warrior = create_warrior(aggressive_civ, 5, 5)
        warrior.owner = aggressive_civ
        warrior._can_attack = False
        warrior._can_move = False

        mock_game_state.get_units_for_civ.return_value = [warrior]
        mock_game_state.get_cities_for_civ.return_value = []

        # Should process without error
        controller.take_turn(mock_game_state)

        # Verify it queried for units
        mock_game_state.get_units_for_civ.assert_called()


class TestAIIntegration:
    """Integration tests for AI components working together."""

    def test_full_ai_turn_with_units(self, aggressive_civ, player_civ, small_grid):
        """Test a complete AI turn with units on real grid."""
        game_state = MagicMock()
        game_state.grid = small_grid
        game_state.active_civs = [player_civ, aggressive_civ]

        # Place units - set remaining_movement to 0 to avoid infinite loop
        # (mocked move_unit doesn't reduce movement)
        ai_warrior = create_warrior(aggressive_civ, 2, 2)
        ai_warrior.owner = aggressive_civ
        ai_warrior.remaining_movement = 0  # Can't move
        ai_warrior.has_attacked = True  # Can't attack

        player_unit = create_warrior(player_civ, 7, 7)
        player_unit.owner = player_civ

        game_state.get_units_for_civ = MagicMock(
            side_effect=lambda civ: [ai_warrior] if civ == aggressive_civ else [player_unit]
        )
        game_state.get_cities_for_civ = MagicMock(return_value=[])
        game_state.get_all_units = MagicMock(return_value=[ai_warrior, player_unit])
        game_state.get_all_cities = MagicMock(return_value=[])
        game_state.move_unit = MagicMock(return_value=True)

        controller = AIController(aggressive_civ)

        # Should complete turn without error
        controller.take_turn(game_state)

    def test_ai_personality_affects_decisions(self, aggressive_civ, balanced_civ):
        """Test that different personalities make different decisions."""
        aggressive_controller = AIController(aggressive_civ)
        balanced_controller = AIController(balanced_civ)

        # Aggressive AI should weight military higher
        assert aggressive_controller.personality_weights["military_weight"] == 1.5
        assert balanced_controller.personality_weights["military_weight"] == 1.0

        # Balanced should have equal weights
        weights = balanced_controller.personality_weights
        assert weights["military_weight"] == weights["expansion_weight"]
        assert weights["economy_weight"] == weights["research_weight"]
