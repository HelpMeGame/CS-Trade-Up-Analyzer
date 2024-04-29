from skin import Skin

class TradeUp:
    def __init__(self, internal_id: int, skins: list[Skin]):
        self.internal_id = internal_id
        self.skins = skins

    def calculate_chances(self):
        pass