from enum import StrEnum

class Stat(StrEnum):
    HP = "HP"
    Power = "Power"
    Speed = "Speed"
    Defense = "Defense"
    Energy = "Energy"

class Operation(StrEnum):
    FLAT_ADD = "FLAT_ADD"
    FLAT_SUB = "FLAT_SUB"
    PCT_ADD = "PCT_ADD"
    PCT_SUB = "PCT_SUB"
    MULTIPLY = "MULTIPLY"

class Target(StrEnum):
    SELF = "SELF"
    ALLY_SINGLE = "ALLY_SINGLE"
    ALLY_ALL = "ALLY_ALL"
    ENEMY_SINGLE = "ENEMY_SINGLE"
    ENEMY_ALL = "ENEMY_ALL"
    GLOBAL = "GLOBAL"

class Stacking(StrEnum):
    stack = "stack"
    replace = "replace"
    max = "max"

class AiHeuristic(StrEnum):
    aggressive = "aggressive"
    defensive = "defensive"
    balanced = "balanced"

class NarrativePosition(StrEnum):
    approach = "approach"
    settlement = "settlement"
    stronghold = "stronghold"

class EncounterType(StrEnum):
    combat = "combat"
    hazard = "hazard"
    event = "event"
