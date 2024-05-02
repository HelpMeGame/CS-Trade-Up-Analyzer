"""

CS Trade Up Analyzer

src/main.py

Developed by Keagan Bowman
Copyright 2024

Main file for analyzer start up. Attempts to use all combinations of Counter Strike weapon skins and
Steam Community Market price data to identify ideal trade ups with a net positive result.

Things to check/do:
Ensure all prices are being properly gathered (wear ratings)
StatTracks
Multi-step trade ups
Float checker?
Steam inventory scanner
Discord bot integration
Double check best fit skin algorithm

"""

import os
import bot
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
            f.close()
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

    if os.path.exists(os.path.join(WORKING_PATH.absolute(), "data/.bot-creds")):
        print("Starting bot...")
        with open(os.path.join(WORKING_PATH.absolute(), "data/.bot-creds"), "r") as f:
            token = f.read()
            f.close()

        bot.start_bot(token.strip())

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

        input_price = (tradeup.skin_1_price * tradeup.skin_1_count) + (
                tradeup.skin_2_price * (10 - tradeup.skin_1_count))

        goal_skin_price = db_handler.get_prices(tradeup.goal_skin.internal_id, tradeup.goal_wear)

        if goal_skin_price is not None:
            possible_profit = f"${round(goal_skin_price[0][0] - input_price, 2):.2f}"
        else:
            possible_profit = "No price on market"

        print(f"\n\n\n"
              f"== Trade Up {tradeup.internal_id} ==\n"
              f"Target: {WeaponIntToStr[tradeup.goal_skin.weapon_type]} {tradeup.goal_skin.skin_name} ({wear_int_enum_to_str_enum[wear_int_to_enum[tradeup.goal_wear]]})\n"
              f"Success Chance: {round(tradeup.chance * 100, 2)}%\n"
              f"Possible Profit: {possible_profit}\n"
              f"\n"
              f"Simulation Results:\n"
              f"\n"
              f"10:\n"
              f"\t> ROI: {round(tradeup.roi_10 * 100, 2)}%\n"
              f"\t> Profit: ${round(tradeup.profit_10, 2)}\n"
              f"100:\n"
              f"\t> ROI: {round(tradeup.roi_100 * 100, 2)}%\n"
              f"\t> Profit: ${round(tradeup.profit_100, 2)}\n"
              f"\n"
              f"Inputs (${round(input_price, 2)} total):\n"
              f"\n"
              f"\t> {tradeup.skin_1_count}x {WeaponIntToStr[tradeup.skin_1.weapon_type]} \"{tradeup.skin_1.skin_name}\" (${round(tradeup.skin_1_price, 2)} per skin)\n")

        if tradeup.skin_2 is not None:
            print(
                f"\t> {10 - tradeup.skin_1_count}x {WeaponIntToStr[tradeup.skin_2.weapon_type]} \"{tradeup.skin_2.skin_name}\" (${round(tradeup.skin_2_price, 2)} per skin)\n"
                f"\n")


if __name__ == "__main__":
    main()
