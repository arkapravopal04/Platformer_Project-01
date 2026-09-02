import pygame


class Entity(pygame.sprite.Sprite):
    """Common base for every obstacle-course sprite.

    TAGS classifies what an entity *does*, independent of its class -
    e.g. {"landable"} for things the player can stand on, {"blocking"}
    for things that stop horizontal movement, {"damaging"} for hazards,
    {"trigger"} for things that fire an event on overlap (the goal,
    eventually checkpoints). Level-building/loading code groups entities
    by tag instead of isinstance-checking each concrete type, so a new
    entity that combines behaviors (e.g. a moving hazard) just declares
    both tags and needs no changes anywhere else.
    """

    TAGS = frozenset()

    # Draw order within a frame, low to high - platforms are the backdrop
    # everything else sits on, so hazards/markers must paint over them.
    # Anything new defaults to 0 unless it overrides this.
    DRAW_LAYER = 0

    def update(self):
        """Default no-op so groups can call update() uniformly across
        entities that don't animate or move."""
        pass


# name -> Entity subclass, populated by @register(...) on each class.
# Lets level data refer to entities by a short string ("platform",
# "moving", ...) instead of importing every concrete class by hand.
ENTITY_TYPES = {}


def register(name):
    def _decorator(cls):
        ENTITY_TYPES[name] = cls
        return cls
    return _decorator
