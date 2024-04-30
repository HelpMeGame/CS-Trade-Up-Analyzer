"""

CS Trade Up Analyzer

src/models/tradeup.py

Developed by Keagan Bowman
Copyright 2024

Trade up class type for use with the database

"""

from skin import Skin


class TradeUp:
    def __init__(self, internal_id: int, skins: list[Skin]):
        self.internal_id = internal_id
        self.skins = skins

    def calculate_chances(self):
        pass
