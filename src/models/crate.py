"""

CS Trade Up Analyzer

src/models/crate.py

Developed by Keagan Bowman
Copyright 2024

Crate class type for use with the database

"""


class Crate:
    def __init__(self, crate_data):
        self.internal_id = crate_data[0]
        self.crate_name = crate_data[1]
        self.crate_id = crate_data[2]
        self.set_id = crate_data[3]
        self.rarity_0_count = crate_data[4]
        self.rarity_1_count = crate_data[5]
        self.rarity_2_count = crate_data[6]
        self.rarity_3_count = crate_data[7]
        self.rarity_4_count = crate_data[8]
        self.rarity_5_count = crate_data[9]

        self.rarity_counts = [crate_data[4], crate_data[5], crate_data[6], crate_data[7], crate_data[8], crate_data[9]]