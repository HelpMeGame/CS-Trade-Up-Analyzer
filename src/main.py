"""

CS Trade Up Analyzer

src/main.py

Developed by Keagan Bowman
Copyright 2024

Main file for analyzer start up. Attempts to use all combinations of Counter Strike weapon skins and
Steam Community Market price data to identify ideal trade ups with a net positive result.

"""

"""
Things to check/do:
Ensure all prices are being properly gathered (wear ratings)
StatTracks
Multi-step trade ups
Float checker?
Steam inventory scanner
Discord bot integration
Double check best fit skin algorithm
Ensure rarities are getting properly gathered
"""

import os
import pathlib
import db_handler
import market_handler
import tradeup_generator
import resource_collector
from models.weapon_classifiers import wear_int_to_enum, wear_int_enum_to_str_enum, WeaponIntToStr


WORKING_PATH = pathlib.Path(os.curdir)


def main():
    # gather the data from the resource files
    items_game, translations = resource_collector.gather_file_data(
        os.path.join(WORKING_PATH.absolute(), "data/items_game.json"),
        os.path.join(WORKING_PATH.absolute(), "data/csgo_english.json")
    )

    if os.path.exists(os.path.join(WORKING_PATH.absolute(), "data/.creds")):
        with open(os.path.join(WORKING_PATH.absolute(), "data/.creds"), "r") as f:
            steam_creds = tuple(f.readlines())
    else:
        steam_creds = ("", "")

    should_wipe = False

    # establish connection to database
    db_handler.connect_to_db(os.path.join(WORKING_PATH.absolute(), "data/skins.db"), wipe_db=should_wipe)

    if should_wipe:
        # collect crate information
        print("Collecting crate info...")
        resource_collector.collect_crates(items_game, translations)

        # collect skin information
        print("Collecting skin info...")
        resource_collector.collect_skins(items_game, translations)

        # collect rarities
        print("Collecting skin rarities...")
        resource_collector.collect_rarities(items_game, translations)

        # gather prices
        # market_handler.get_prices(steam_creds)

        # find cheapest prices per crate per rarity
        print("Collecting cheapest prices...")
        # market_handler.find_cheapest()

        # generate all possible trade-ups
        print("Generating trade-ups...")
        tradeup_generator.generate_tradeups()

        print("\n\n")

    while True:
        tradeup_id = input("Please enter the trade up ID to receive information on (-1 to exit): ")

        if tradeup_id == "-1":
            break

        try:
            tradeup = db_handler.get_tradeup_by_id(tradeup_id)
        except ValueError:
            print("Invalid ID.")
            continue

        if tradeup is None:
            print("Trade up not found")
            continue

        print(f"== Trade Up {tradeup.internal_id} ==\n"
              f"Target: {tradeup.goal_skin.skin_name} ({wear_int_enum_to_str_enum[wear_int_to_enum[tradeup.goal_wear]]})\n"
              f"\n"
              f"Simulation Results:\n"
              f"\n"
              f"10:\n"
              f"\t> ROI: {tradeup.roi_10}\n"
              f"\t> Profit: {tradeup.profit_10}\n"
              f"100:\n"
              f"\t> ROI: {tradeup.roi_100}\n"
              f"\t> Profit: {tradeup.profit_100}\n"
              f"\n"
              f"Inputs:\n"
              f"\n"
              f"\t> {tradeup.skin_1_count}x {WeaponIntToStr[tradeup.skin_1.weapon_type]} \"{tradeup.skin_1.skin_name}\"\n"
              f"\t> {10 - tradeup.skin_1_count}x {WeaponIntToStr[tradeup.skin_2.weapon_type]} \"{tradeup.skin_2.skin_name}\"\n"
              f"\n")


if __name__ == "__main__":
    main()
