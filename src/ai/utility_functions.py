"""Utility calculation functions for AI decision making."""

from typing import TYPE_CHECKING

from src.systems.combat_system import CombatSystem

if TYPE_CHECKING:
    from src.core.game_state import GameState
    from src.entities.civilization import Civilization
    from src.entities.unit import Unit
    from src.entities.city import City
    from src.map.tile import Tile


def calculate_attack_utility(
    attacker: 'Unit',
    defender: 'Unit',
    defender_tile: 'Tile',
    personality_weights: dict[str, float]
) -> float:
    """Calculate utility of attacking a target.

    Args:
        attacker: Attacking unit
        defender: Target unit
        defender_tile: Tile defender is on
        personality_weights: AI personality weights

    Returns:
        Utility score (higher = better attack)
    """
    # Get expected damage exchange
    damage_dealt, damage_received = CombatSystem.calculate_expected_damage(
        attacker, defender, defender_tile
    )

    # Base utility from damage ratio
    if damage_received == 0:
        damage_ratio = 10.0  # Very favorable
    else:
        damage_ratio = damage_dealt / damage_received

    # Target value based on unit strength
    target_value = (defender.attack + defender.defense) / 25.0

    # Kill bonus if we can kill the target
    kill_bonus = 0.0
    if damage_dealt >= defender.health:
        kill_bonus = 2.0

    # Risk penalty if we might die
    risk_penalty = 0.0
    if damage_received >= attacker.health:
        risk_penalty = -3.0

    # Apply personality weight
    military_weight = personality_weights.get("military_weight", 1.0)

    utility = (damage_ratio + target_value + kill_bonus + risk_penalty) * military_weight

    return max(0.0, utility)


def calculate_movement_utility(
    unit: 'Unit',
    target_tile: 'Tile',
    game_state: 'GameState',
    personality_weights: dict[str, float]
) -> float:
    """Calculate utility of moving to a target tile.

    Args:
        unit: Unit to move
        target_tile: Destination tile
        game_state: Current game state
        personality_weights: AI personality weights

    Returns:
        Utility score (higher = better move)
    """
    utility = 0.0

    # Distance to enemy units (closer = higher utility for aggressive)
    enemy_units = [u for u in game_state.get_all_units() if u.owner != unit.owner]
    if enemy_units:
        min_enemy_dist = min(
            abs(target_tile.x - e.x) + abs(target_tile.y - e.y)
            for e in enemy_units
        )
        # Aggressive AI wants to be closer, balanced less so
        military_weight = personality_weights.get("military_weight", 1.0)
        utility += (10 - min_enemy_dist) * 0.1 * military_weight

    # Distance to enemy cities
    enemy_cities = [c for c in game_state.get_all_cities() if c.owner != unit.owner]
    if enemy_cities:
        min_city_dist = min(
            abs(target_tile.x - c.x) + abs(target_tile.y - c.y)
            for c in enemy_cities
        )
        expansion_weight = personality_weights.get("expansion_weight", 1.0)
        utility += (10 - min_city_dist) * 0.15 * expansion_weight

    # Terrain defense bonus
    utility += target_tile.defense_bonus * 0.5

    # Resource proximity
    if target_tile.resource:
        economy_weight = personality_weights.get("economy_weight", 1.0)
        utility += 0.3 * economy_weight

    return utility


def calculate_retreat_utility(
    unit: 'Unit',
    game_state: 'GameState'
) -> float:
    """Calculate utility of retreating.

    Args:
        unit: Unit considering retreat
        game_state: Current game state

    Returns:
        Utility score (higher = should retreat more)
    """
    # Base on health ratio
    health_ratio = unit.health / unit.max_health

    if health_ratio > 0.5:
        return 0.0  # No need to retreat
    elif health_ratio > 0.3:
        return 0.3  # Consider retreating
    else:
        return 0.8  # Strongly consider retreating


def calculate_production_utility(
    city: 'City',
    unit_type,
    game_state: 'GameState',
    civ: 'Civilization',
    personality_weights: dict[str, float]
) -> float:
    """Calculate utility of producing a unit type.

    Args:
        city: City producing
        unit_type: Unit type to produce
        game_state: Current game state
        civ: Civilization producing
        personality_weights: AI personality weights

    Returns:
        Utility score
    """
    from src.data.unit_data import get_unit_stats, CombatType

    stats = get_unit_stats(unit_type)
    utility = 0.0

    # Base utility from combat stats
    combat_power = (stats.attack + stats.defense) / 20.0
    utility += combat_power

    # Weight by personality
    military_weight = personality_weights.get("military_weight", 1.0)
    utility *= military_weight

    # Ranged units slightly preferred for safety
    if stats.combat_type == CombatType.RANGED:
        utility += 0.2

    # Mobile units preferred for expansion
    if stats.movement >= 3:
        expansion_weight = personality_weights.get("expansion_weight", 1.0)
        utility += 0.3 * expansion_weight

    # Can we afford it?
    if not civ.can_afford(stats.cost):
        utility *= 0.1  # Heavy penalty if we can't afford

    return utility


def calculate_research_utility(
    tech_id: str,
    civ: 'Civilization',
    personality_weights: dict[str, float]
) -> float:
    """Calculate utility of researching a technology.

    Args:
        tech_id: Technology ID
        civ: Civilization researching
        personality_weights: AI personality weights

    Returns:
        Utility score
    """
    from src.data.tech_data import get_technology

    tech = get_technology(tech_id)
    if not tech:
        return 0.0

    utility = 0.0

    # Units unlocked are valuable
    if tech.unlocks_units:
        military_weight = personality_weights.get("military_weight", 1.0)
        utility += len(tech.unlocks_units) * 2.0 * military_weight

    # Bonuses are valuable
    for bonus_name, bonus_value in tech.bonuses.items():
        if "production" in bonus_name:
            utility += bonus_value * 3.0
        elif "research" in bonus_name:
            research_weight = personality_weights.get("research_weight", 1.0)
            utility += bonus_value * 4.0 * research_weight
        elif "food" in bonus_name or "economy" in bonus_name:
            economy_weight = personality_weights.get("economy_weight", 1.0)
            utility += bonus_value * 2.0 * economy_weight

    # Cheaper techs are slightly preferred
    cost_factor = 100 / (tech.cost + 50)
    utility += cost_factor

    return utility
