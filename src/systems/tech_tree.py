"""Technology tree system."""

from typing import TYPE_CHECKING, Optional

from src.data.tech_data import (
    Technology,
    get_technology,
    get_available_techs,
    TECHNOLOGIES,
)

if TYPE_CHECKING:
    from src.entities.civilization import Civilization


class TechTree:
    """Manages technology research for a civilization."""

    def __init__(self, civ: 'Civilization'):
        """Initialize tech tree.

        Args:
            civ: Civilization this tech tree belongs to
        """
        self.civ = civ

    @property
    def researched(self) -> set[str]:
        """Get set of researched tech IDs."""
        return self.civ.researched_techs

    @property
    def current_research(self) -> Optional[str]:
        """Get current research tech ID."""
        return self.civ.current_research

    @property
    def research_progress(self) -> int:
        """Get current research progress."""
        return self.civ.research_progress

    def get_available(self) -> list[Technology]:
        """Get technologies available to research.

        Returns:
            List of researchable technologies
        """
        return get_available_techs(self.researched)

    def can_research(self, tech_id: str) -> bool:
        """Check if a technology can be researched.

        Args:
            tech_id: Technology ID

        Returns:
            True if can research
        """
        tech = get_technology(tech_id)
        if not tech:
            return False

        # Already researched
        if tech_id in self.researched:
            return False

        # Check prerequisites
        return all(prereq in self.researched for prereq in tech.prerequisites)

    def start_research(self, tech_id: str) -> bool:
        """Start researching a technology.

        Args:
            tech_id: Technology ID

        Returns:
            True if research started
        """
        if not self.can_research(tech_id):
            return False

        self.civ.start_research(tech_id)
        return True

    def add_progress(self, amount: int) -> Optional[str]:
        """Add research progress.

        Args:
            amount: Research points to add

        Returns:
            Completed tech ID if research finished, None otherwise
        """
        if self.current_research is None:
            return None

        tech = get_technology(self.current_research)
        if not tech:
            return None

        self.civ.add_research_progress(amount)

        if self.research_progress >= tech.cost:
            completed_id = self.current_research
            self.civ.research_complete(completed_id)
            return completed_id

        return None

    def get_progress_ratio(self) -> float:
        """Get research progress as a ratio.

        Returns:
            Progress ratio (0.0 to 1.0)
        """
        if self.current_research is None:
            return 0.0

        tech = get_technology(self.current_research)
        if not tech:
            return 0.0

        return min(1.0, self.research_progress / tech.cost)

    def get_turns_remaining(self, research_per_turn: int = 5) -> int:
        """Estimate turns remaining for current research.

        Args:
            research_per_turn: Research points gained per turn

        Returns:
            Estimated turns remaining, or 0 if no research
        """
        if self.current_research is None:
            return 0

        tech = get_technology(self.current_research)
        if not tech:
            return 0

        remaining = tech.cost - self.research_progress
        if research_per_turn <= 0:
            return 999

        return (remaining + research_per_turn - 1) // research_per_turn

    def has_tech(self, tech_id: str) -> bool:
        """Check if a technology has been researched.

        Args:
            tech_id: Technology ID

        Returns:
            True if researched
        """
        return tech_id in self.researched

    def get_bonus(self, bonus_name: str) -> float:
        """Get total bonus from researched technologies.

        Args:
            bonus_name: Name of bonus to check

        Returns:
            Total bonus value
        """
        total = 0.0
        for tech_id in self.researched:
            tech = get_technology(tech_id)
            if tech and bonus_name in tech.bonuses:
                total += tech.bonuses[bonus_name]
        return total
