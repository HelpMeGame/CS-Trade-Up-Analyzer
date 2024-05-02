"""

CS Trade Up Analyzer

src/models/tradeup.py

Developed by Keagan Bowman
Copyright 2024

Trade up class type for use with the database

"""

class TradeUp:
    def __init__(self, tradeup_data: list, skins):
        self.internal_id = tradeup_data[0]
        self.goal_skin= tradeup_data[1]
        self.goal_wear = tradeup_data[2]
        self.skin_1_count = tradeup_data[3]
        self.chance = tradeup_data[4]
        self.roi_10 = tradeup_data[5]
        self.profit_10 = tradeup_data[6]
        self.roi_100 = tradeup_data[7]
        self.profit_100 = tradeup_data[8]

        self.skin_1 = skins[0]

        if len(skins) > 1:
            self.skin_2 = skins[1]
        else:
            self.skin_2 = None

    def calculate_chances(self):
        pass
