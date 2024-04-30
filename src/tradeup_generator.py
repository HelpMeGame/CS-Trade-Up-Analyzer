"""

CS Trade Up Analyzer

src/tradeup.py

Developed by Keagan Bowman
Copyright 2024

Generator algorithm for determining best possible trade ups for a given skin

"""

import db_handler


def generate_tradeups():
    for i in range(1, 6):

        # get skins of this rarity
        skins = db_handler.get_skins_by_rarity(i)

        print(f"\t > Generating combinations for rarity {i} ({len(skins)} items)...")

        for skin in skins:
            # get this skin's crate
            crate = db_handler.get_crate_from_internal(skin.crate_id)

