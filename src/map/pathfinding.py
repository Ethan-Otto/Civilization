"""A* pathfinding implementation."""

import heapq
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.map.grid import Grid
    from src.map.tile import Tile
    from src.entities.unit import Unit


def heuristic(a: 'Tile', b: 'Tile') -> int:
    """Calculate Manhattan distance heuristic.

    Args:
        a: Start tile
        b: Goal tile

    Returns:
        Estimated distance
    """
    return abs(a.x - b.x) + abs(a.y - b.y)


def find_path(
    grid: 'Grid',
    start: 'Tile',
    goal: 'Tile',
    unit: Optional['Unit'] = None
) -> list['Tile']:
    """Find optimal path using A* algorithm.

    Args:
        grid: The game grid
        start: Starting tile
        goal: Goal tile
        unit: Optional unit (for checking enemy units)

    Returns:
        List of tiles from start to goal (excluding start, including goal),
        or empty list if no path found
    """
    if start == goal:
        return []

    if not goal.is_passable:
        return []

    # Priority queue: (f_score, counter, tile)
    # Counter is used to break ties in a deterministic way
    counter = 0
    open_set = []
    heapq.heappush(open_set, (0, counter, start))

    came_from: dict['Tile', 'Tile'] = {}
    g_score: dict['Tile', float] = {start: 0}
    f_score: dict['Tile', float] = {start: heuristic(start, goal)}

    open_set_hash = {start}

    while open_set:
        current = heapq.heappop(open_set)[2]
        open_set_hash.discard(current)

        if current == goal:
            return _reconstruct_path(came_from, current)

        for neighbor in grid.get_neighbors(current):
            # Check if passable
            if not neighbor.is_passable:
                continue

            # Check if blocked by unit (unless it's the goal and we're attacking)
            if neighbor.has_unit():
                if neighbor != goal:
                    continue
                # Allow moving to goal if it has an enemy unit (for attack)
                if unit and neighbor.unit and neighbor.unit.owner == unit.owner:
                    continue  # Can't move onto friendly units

            movement_cost = neighbor.movement_cost
            tentative_g = g_score[current] + movement_cost

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)

                if neighbor not in open_set_hash:
                    counter += 1
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))
                    open_set_hash.add(neighbor)

    return []  # No path found


def _reconstruct_path(came_from: dict['Tile', 'Tile'], current: 'Tile') -> list['Tile']:
    """Reconstruct path from came_from dict.

    Args:
        came_from: Dictionary mapping tiles to their predecessor
        current: Goal tile

    Returns:
        Path from start to goal (excluding start, including goal)
    """
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)

    # Remove start tile and reverse
    path.pop()  # Remove start
    path.reverse()
    return path


def get_reachable_tiles(
    grid: 'Grid',
    start: 'Tile',
    movement: int,
    unit: Optional['Unit'] = None
) -> dict['Tile', int]:
    """Get all tiles reachable within movement range.

    Uses Dijkstra's algorithm to find all reachable tiles.

    Args:
        grid: The game grid
        start: Starting tile
        movement: Available movement points
        unit: Optional unit (for checking enemy units)

    Returns:
        Dictionary mapping reachable tiles to their movement cost
    """
    reachable: dict['Tile', int] = {start: 0}

    # Priority queue: (cost, counter, tile)
    counter = 0
    open_set = []
    heapq.heappush(open_set, (0, counter, start))

    while open_set:
        current_cost, _, current = heapq.heappop(open_set)

        if current_cost > reachable.get(current, float('inf')):
            continue

        for neighbor in grid.get_neighbors(current):
            # Check if passable
            if not neighbor.is_passable:
                continue

            # Check if blocked by unit
            if neighbor.has_unit():
                if unit and neighbor.unit.owner == unit.owner:
                    continue  # Can't move through friendly units
                # Can move to enemy units (for attack), but can't pass through
                # So we add it as reachable but don't continue from it

            new_cost = current_cost + neighbor.movement_cost

            if new_cost <= movement and new_cost < reachable.get(neighbor, float('inf')):
                reachable[neighbor] = new_cost
                counter += 1
                heapq.heappush(open_set, (new_cost, counter, neighbor))

    # Remove start tile from result
    del reachable[start]
    return reachable


def get_path_cost(path: list['Tile']) -> int:
    """Calculate total movement cost of a path.

    Args:
        path: List of tiles in the path

    Returns:
        Total movement cost
    """
    return sum(tile.movement_cost for tile in path)


def get_tiles_in_attack_range(
    grid: 'Grid',
    unit: 'Unit'
) -> list['Tile']:
    """Get all tiles a unit can attack from current position.

    Args:
        grid: The game grid
        unit: The attacking unit

    Returns:
        List of tiles within attack range
    """
    start_tile = grid.get_tile(unit.x, unit.y)
    if not start_tile:
        return []

    attackable = []
    attack_range = unit.range

    # Get all tiles within range
    for tile in grid.get_tiles_in_range(unit.x, unit.y, attack_range):
        if tile == start_tile:
            continue

        distance = abs(tile.x - unit.x) + abs(tile.y - unit.y)

        # Melee units can only attack adjacent
        if unit.is_melee and distance != 1:
            continue

        # Ranged units can attack at any distance up to range
        if unit.is_ranged and distance > attack_range:
            continue

        attackable.append(tile)

    return attackable
