from .base import Entity, ENTITY_TYPES, register
from .platform import Platform, MovingPlatform
from .wall import Wall
from .hazard import Hazard
from .goal import Goal
from .trapdoor import TrapDoor

__all__ = [
    "Entity", "ENTITY_TYPES", "register",
    "Platform", "MovingPlatform", "Wall", "Hazard", "Goal", "TrapDoor",
]
