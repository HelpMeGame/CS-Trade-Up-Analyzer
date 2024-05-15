"""

CS Trade Up Analyzer

src/models/simulation_possibility.py

Developed by Keagan Bowman
Copyright 2024

Simulation Possibility class for running simulated trade ups

"""

from src.models.skin import Skin


class SimulationPossibility:
    def __init__(self, skin: Skin):
        self.skin_id = skin.internal_id
        self.case_id = skin.crate_id
        self.min_wear = skin.min_wear
        self.max_wear = skin.max_wear
        self.rarity = skin.rarity
