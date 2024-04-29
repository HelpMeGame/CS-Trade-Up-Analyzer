"""

CS Trade Up Analyzer

src/models/skin.py

Developed by Keagan Bowman
Copyright 2024

Skin class type for use with the database

"""

import src.db_handler



class Skin:
    def __init__(self, internal_id: int, skin_id: int, skin_name: str, weapon_type: int, rarity: int, min_wear: float,
                 max_wear: float, crate_id: int):
        self.internal_id = internal_id
        self.skin_id = skin_id
        self.skin_name = skin_name
        self.weapon_type = weapon_type
        self.rarity = rarity
        self.min_wear = min_wear
        self.max_wear = max_wear
        self.crate_id = crate_id

        self.crate = 0
