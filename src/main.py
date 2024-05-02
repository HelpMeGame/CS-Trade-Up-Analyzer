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
"""

import os
import pathlib
import db_handler
import market_handler
import tradeup_generator
import resource_collector


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

    should_wipe = True

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

        # find cheapest prices
        print("Collecting cheapest prices...")
        # market_handler.find_cheapest()

        # generate all possible trade-ups
        print("Generating trade-ups...")
        tradeup_generator.generate_tradeups()


if __name__ == "__main__":
    main()
