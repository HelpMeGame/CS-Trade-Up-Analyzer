"""

CS Trade Up Analyzer

src/models/skin.py

Developed by Keagan Bowman
Copyright 2024

Skin class type for use with the database

"""


class Skin:
    def __init__(self, skin_data):
        self.internal_id = skin_data[0]
        self.skin_id = skin_data[1]
        self.skin_tag = skin_data[2]
        self.skin_name = skin_data[3]
        self.weapon_type = skin_data[4]
        self.rarity = skin_data[5]
        self.min_wear = skin_data[6]
        self.max_wear = skin_data[7]
        self.crate_id = skin_data[8]

        self.crate = None
