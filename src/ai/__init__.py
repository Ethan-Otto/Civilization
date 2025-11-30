# AI package
"""AI system for controlling enemy civilizations."""

from src.ai.ai_controller import AIController, create_ai_controller, process_ai_turn
from src.ai.ai_tactics import TacticalAI, TacticalAction, ActionType
from src.ai.ai_strategies import StrategicAI, StrategicAssessment, StrategicGoal
from src.ai.utility_functions import (
    calculate_attack_utility,
    calculate_movement_utility,
    calculate_retreat_utility,
    calculate_production_utility,
    calculate_research_utility,
)

__all__ = [
    "AIController",
    "create_ai_controller",
    "process_ai_turn",
    "TacticalAI",
    "TacticalAction",
    "ActionType",
    "StrategicAI",
    "StrategicAssessment",
    "StrategicGoal",
    "calculate_attack_utility",
    "calculate_movement_utility",
    "calculate_retreat_utility",
    "calculate_production_utility",
    "calculate_research_utility",
]
