"""Tests for technology tree system using real game data."""

import pytest

from src.systems.tech_tree import TechTree
from src.data.tech_data import get_technology, get_available_techs, TECHNOLOGIES
from src.entities.civilization import Civilization
from src.data.unit_data import UnitType


@pytest.fixture
def player_civ():
    """Create player civilization."""
    return Civilization(name="Player", color_key="PLAYER")


@pytest.fixture
def tech_tree(player_civ):
    """Create tech tree for player civilization."""
    return TechTree(player_civ)


class TestTechnologyData:
    """Tests for technology data definitions."""

    def test_all_techs_have_required_fields(self):
        """All technologies should have required fields."""
        for tech_id, tech in TECHNOLOGIES.items():
            assert tech.id == tech_id
            assert tech.name
            assert tech.description
            assert tech.cost > 0
            assert isinstance(tech.prerequisites, tuple)
            assert isinstance(tech.unlocks_units, tuple)
            assert isinstance(tech.bonuses, dict)

    def test_tech_prerequisites_exist(self):
        """All tech prerequisites should reference existing techs."""
        for tech in TECHNOLOGIES.values():
            for prereq in tech.prerequisites:
                assert prereq in TECHNOLOGIES, f"{tech.id} has invalid prereq: {prereq}"

    def test_starting_techs_have_no_prerequisites(self):
        """Some techs should have no prerequisites (starting techs)."""
        starting_techs = [t for t in TECHNOLOGIES.values() if not t.prerequisites]
        assert len(starting_techs) >= 3  # At least 3 starting techs

    def test_archery_unlocks_archer(self):
        """Archery tech should unlock Archer unit."""
        archery = get_technology("archery")
        assert archery is not None
        assert UnitType.ARCHER in archery.unlocks_units


class TestTechTreeAvailability:
    """Tests for tech availability checking."""

    def test_starting_techs_available(self, tech_tree):
        """Starting techs should be available immediately."""
        available = tech_tree.get_available()

        # Should have agriculture, mining, archery, writing available
        available_ids = {t.id for t in available}
        assert "agriculture" in available_ids
        assert "mining" in available_ids
        assert "archery" in available_ids
        assert "writing" in available_ids

    def test_advanced_techs_not_initially_available(self, tech_tree):
        """Advanced techs should not be available without prerequisites."""
        available = tech_tree.get_available()
        available_ids = {t.id for t in available}

        # These require prerequisites
        assert "bronze_working" not in available_ids  # Requires mining
        assert "horseback_riding" not in available_ids  # Requires animal_husbandry

    def test_tech_becomes_available_after_prereq(self, tech_tree, player_civ):
        """Tech should become available after researching prerequisites."""
        # Initially bronze_working not available
        available = tech_tree.get_available()
        available_ids = {t.id for t in available}
        assert "bronze_working" not in available_ids

        # Research mining
        player_civ.research_complete("mining")

        # Now bronze_working should be available
        available = tech_tree.get_available()
        available_ids = {t.id for t in available}
        assert "bronze_working" in available_ids


class TestTechResearch:
    """Tests for tech research functionality."""

    def test_can_start_research(self, tech_tree):
        """Should be able to start researching available tech."""
        assert tech_tree.start_research("archery")
        assert tech_tree.current_research == "archery"

    def test_cannot_research_unavailable_tech(self, tech_tree):
        """Should not be able to research tech without prerequisites."""
        assert not tech_tree.start_research("bronze_working")
        assert tech_tree.current_research is None

    def test_cannot_research_already_researched(self, tech_tree, player_civ):
        """Should not be able to research already researched tech."""
        player_civ.research_complete("archery")

        assert not tech_tree.start_research("archery")

    def test_progress_tracking(self, tech_tree):
        """Research progress should be tracked correctly."""
        tech_tree.start_research("archery")  # Cost: 30

        assert tech_tree.research_progress == 0

        completed = tech_tree.add_progress(10)
        assert completed is None
        assert tech_tree.research_progress == 10

        completed = tech_tree.add_progress(10)
        assert completed is None
        assert tech_tree.research_progress == 20

    def test_research_completes(self, tech_tree, player_civ):
        """Research should complete when progress reaches cost."""
        tech_tree.start_research("agriculture")  # Cost: 20

        completed = tech_tree.add_progress(20)

        assert completed == "agriculture"
        assert "agriculture" in player_civ.researched_techs
        assert tech_tree.current_research is None
        assert tech_tree.research_progress == 0

    def test_progress_ratio(self, tech_tree):
        """Progress ratio should be calculated correctly."""
        tech_tree.start_research("agriculture")  # Cost: 20

        assert tech_tree.get_progress_ratio() == 0.0

        tech_tree.add_progress(10)
        assert tech_tree.get_progress_ratio() == 0.5

        tech_tree.add_progress(10)
        # After completion, ratio should be 0 (no current research)
        assert tech_tree.get_progress_ratio() == 0.0


class TestTechBonuses:
    """Tests for tech bonus system."""

    def test_no_bonus_without_tech(self, tech_tree):
        """Should have no bonus without researching tech."""
        bonus = tech_tree.get_bonus("research_bonus")
        assert bonus == 0.0

    def test_bonus_after_research(self, tech_tree, player_civ):
        """Should have bonus after researching tech."""
        player_civ.research_complete("writing")

        bonus = tech_tree.get_bonus("research_bonus")
        assert bonus == 0.5

    def test_multiple_bonuses_stack(self, tech_tree, player_civ):
        """Multiple tech bonuses of same type should stack."""
        # Both agriculture and mining provide per-city bonuses
        player_civ.research_complete("agriculture")
        player_civ.research_complete("mining")

        food_bonus = tech_tree.get_bonus("food_per_city")
        stone_bonus = tech_tree.get_bonus("stone_per_city")

        assert food_bonus == 2
        assert stone_bonus == 1


class TestTechTreeIntegration:
    """Integration tests for complete tech tree flow."""

    def test_research_chain_to_machinery(self, tech_tree, player_civ):
        """Test researching all the way to machinery."""
        # Research path: mining -> masonry -> mathematics -> engineering -> machinery
        # But mathematics also needs writing

        # Research starting techs
        player_civ.research_complete("mining")
        player_civ.research_complete("writing")
        player_civ.research_complete("masonry")

        assert tech_tree.can_research("mathematics")
        player_civ.research_complete("mathematics")

        assert tech_tree.can_research("engineering")
        player_civ.research_complete("engineering")

        assert tech_tree.can_research("machinery")
        player_civ.research_complete("machinery")

        assert UnitType.CROSSBOWMAN in get_technology("machinery").unlocks_units

    def test_turns_remaining_estimate(self, tech_tree):
        """Turns remaining should be calculated correctly."""
        tech_tree.start_research("agriculture")  # Cost: 20

        # With 5 research per turn, should take 4 turns
        turns = tech_tree.get_turns_remaining(research_per_turn=5)
        assert turns == 4

        # After 10 progress, should take 2 more turns
        tech_tree.add_progress(10)
        turns = tech_tree.get_turns_remaining(research_per_turn=5)
        assert turns == 2
