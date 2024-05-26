"""

CS Trade Up Analyzer

src/main.py

Developed by Keagan Bowman
Copyright 2024

Main file for analyzer start up. Attempts to use all combinations of Counter Strike weapon skins and
Steam Community Market price data to identify trade ups with both a net positive and negative result.

Things to check/do:
StatTracks
Multi-step trade ups
Steam inventory scanner
Trade up generation should be based on buy orders, not sell orders -> special circumstances
"""

import os
import pathlib
from src import db_handler, market_handler, tradeup_generator, resource_collector

WORKING_PATH = pathlib.Path(os.curdir)
THREAD_COUNT = 64

COLLECT_SKIN_DATA = False
COLLECT_PRICE_DATA = False
GENERATE_TRADE_UPS = True


def main():
    # gather the data from the resource files
    items_game, translations = resource_collector.gather_file_data(
        os.path.join(WORKING_PATH.absolute(), "data/items_game.json"),
        os.path.join(WORKING_PATH.absolute(), "data/csgo_english.json")
    )

    if os.path.exists(os.path.join(WORKING_PATH.absolute(), "data/.steam-creds")):
        with open(os.path.join(WORKING_PATH.absolute(), "data/.steam-creds"), "r") as f:
            steam_creds = tuple(f.readlines())
            f.close()
    else:
        steam_creds = ("", "")

    if os.path.exists(os.path.join(WORKING_PATH.absolute(), "data/.db-creds")):
        with open(os.path.join(WORKING_PATH.absolute(), "data/.db-creds"), "r") as f:
            db_creds = tuple(f.readlines())
            f.close()
    else:
        db_creds = ("", "", "", "", "")

    # establish connection to database
    print("Establishing connection to database...")
    db_handler.establish_db(db_creds,
                            wipe_skin_data=COLLECT_SKIN_DATA,
                            wipe_price_data=COLLECT_PRICE_DATA,
                            wipe_trade_up_data=GENERATE_TRADE_UPS
                            )

    if COLLECT_SKIN_DATA:
        # collect crate information
        print("Collecting crate info...")
        resource_collector.collect_crates(items_game, translations)

        # collect skin information
        print("Collecting skin info...")
        resource_collector.collect_skins(items_game, translations)

        # collect rarities
        print("Collecting skin rarities...")
        resource_collector.collect_rarities(items_game)

    if COLLECT_PRICE_DATA:
        # gather prices
        print("Gathering market prices...")
        market_handler.get_prices(steam_creds)

        # find cheapest prices per crate per rarity
        print("Collecting cheapest prices...")
        market_handler.find_cheapest()

    if GENERATE_TRADE_UPS:
        # generate all possible trade-ups
        print("Generating trade-ups...")
        tradeup_generator.start_generator_threads(db_creds, THREAD_COUNT)

    # close out working database
    db_handler.WORKING_DB.close()


if __name__ == "__main__":
    main()
