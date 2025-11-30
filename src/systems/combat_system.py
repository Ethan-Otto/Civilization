"""Combat system for resolving battles."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.data.unit_data import CombatType

if TYPE_CHECKING:
    from src.entities.unit import Unit
    from src.map.tile import Tile


@dataclass
class CombatResult:
    """Result of a combat encounter."""
    attacker_damage: int  # Damage dealt to attacker
    defender_damage: int  # Damage dealt to defender
    attacker_killed: bool
    defender_killed: bool


class CombatSystem:
    """Handles combat calculations between units."""

    @staticmethod
    def calculate_damage(
        attacker: 'Unit',
        defender: 'Unit',
        defender_tile: 'Tile',
        distance: int = 1
    ) -> int:
        """Calculate damage from attacker to defender.

        Formula:
        - Base damage = attacker.attack * (100 / (100 + defender.defense))
        - Terrain modifier = 1 - tile.defense_bonus
        - Health modifier = 0.5 + (attacker_health_ratio * 0.5)
        - Range penalty = 0.75 at max range for ranged units

        Args:
            attacker: Attacking unit
            defender: Defending unit
            defender_tile: Tile the defender is on
            distance: Distance between units

        Returns:
            Damage to deal
        """
        # Base damage formula
        base_damage = attacker.attack * (100 / (100 + defender.defense))

        # Terrain defense modifier
        terrain_modifier = 1 - defender_tile.defense_bonus

        # Health modifier (damaged units deal less damage)
        health_modifier = attacker.get_damage_modifier()

        # Range penalty for ranged units at max range
        range_modifier = 1.0
        if attacker.is_ranged and distance == attacker.range:
            range_modifier = 0.75

        # Calculate final damage
        final_damage = base_damage * terrain_modifier * health_modifier * range_modifier

        return max(1, int(final_damage))  # Minimum 1 damage

    @staticmethod
    def can_counterattack(defender: 'Unit', attacker: 'Unit', distance: int) -> bool:
        """Check if defender can counterattack.

        Rules:
        - Melee defenders can counter melee attackers (distance 1)
        - Ranged defenders can counter if attacker is in their range
        - Ranged attackers don't receive counterattacks from melee

        Args:
            defender: Defending unit
            attacker: Attacking unit
            distance: Distance between units

        Returns:
            True if defender can counterattack
        """
        if not defender.is_alive:
            return False

        # Ranged attackers at range > 1 don't receive counterattacks from melee
        if attacker.is_ranged and distance > 1 and defender.is_melee:
            return False

        # Defender must be able to attack at this distance
        return defender.can_attack_at_range(distance)

    @staticmethod
    def resolve_combat(
        attacker: 'Unit',
        defender: 'Unit',
        attacker_tile: 'Tile',
        defender_tile: 'Tile'
    ) -> CombatResult:
        """Resolve a complete combat encounter.

        Args:
            attacker: Attacking unit
            defender: Defending unit
            attacker_tile: Tile the attacker is on
            defender_tile: Tile the defender is on

        Returns:
            CombatResult with outcome
        """
        distance = abs(attacker.x - defender.x) + abs(attacker.y - defender.y)

        # Calculate and apply attacker's damage to defender
        attacker_damage_dealt = CombatSystem.calculate_damage(
            attacker, defender, defender_tile, distance
        )
        defender.take_damage(attacker_damage_dealt)

        # Check for counterattack
        defender_damage_dealt = 0
        if CombatSystem.can_counterattack(defender, attacker, distance):
            defender_damage_dealt = CombatSystem.calculate_damage(
                defender, attacker, attacker_tile, distance
            )
            attacker.take_damage(defender_damage_dealt)

        # Mark attacker as having attacked
        attacker.attack_target()

        return CombatResult(
            attacker_damage=defender_damage_dealt,
            defender_damage=attacker_damage_dealt,
            attacker_killed=not attacker.is_alive,
            defender_killed=not defender.is_alive,
        )

    @staticmethod
    def calculate_expected_damage(
        attacker: 'Unit',
        defender: 'Unit',
        defender_tile: 'Tile'
    ) -> tuple[int, int]:
        """Calculate expected damage for AI evaluation.

        Args:
            attacker: Attacking unit
            defender: Defending unit
            defender_tile: Tile the defender is on

        Returns:
            Tuple of (damage_to_defender, expected_counterattack_damage)
        """
        distance = abs(attacker.x - defender.x) + abs(attacker.y - defender.y)

        damage_to_defender = CombatSystem.calculate_damage(
            attacker, defender, defender_tile, distance
        )

        # Estimate counterattack damage
        damage_to_attacker = 0
        if CombatSystem.can_counterattack(defender, attacker, distance):
            # Create a copy of defender with reduced health to estimate
            simulated_health = defender.health - damage_to_defender
            if simulated_health > 0:
                # Estimate counterattack damage with reduced health
                health_ratio = simulated_health / defender.max_health
                base_counter = defender.attack * (100 / (100 + attacker.defense))
                damage_to_attacker = int(base_counter * (0.5 + health_ratio * 0.5))

        return (damage_to_defender, damage_to_attacker)

    @staticmethod
    def get_combat_odds(attacker: 'Unit', defender: 'Unit', defender_tile: 'Tile') -> float:
        """Get combat odds as a ratio.

        Args:
            attacker: Attacking unit
            defender: Defending unit
            defender_tile: Tile defender is on

        Returns:
            Ratio of expected damage dealt vs received (> 1 means favorable)
        """
        damage_dealt, damage_received = CombatSystem.calculate_expected_damage(
            attacker, defender, defender_tile
        )

        if damage_received == 0:
            return float('inf') if damage_dealt > 0 else 1.0

        return damage_dealt / damage_received
