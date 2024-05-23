"""

CS Trade Up Analyzer

src/main.py

Developed by Keagan Bowman
Copyright 2024

Main file for analyzer start up. Attempts to use all combinations of Counter Strike weapon skins and
Steam Community Market price data to identify ideal trade ups with a net positive result.

Things to check/do:
StatTracks
Multi-step trade ups
Steam inventory scanner
Discord bot integration reworks
Check all skins from crate, not just cheapest? Maybe sort by cheapest first.
Trade up generation should be based on buy orders, not sell orders
"""

import os
import bot
import pathlib
import db_handler
import market_handler
import tradeup_generator
import resource_collector

WORKING_PATH = pathlib.Path(os.curdir)


def main():
    should_wipe = True

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
    db_handler.establish_db(db_creds, wipe_db=should_wipe)

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
        print("Gathering market prices...")
        # market_handler.get_prices(steam_creds)

        # find cheapest prices per crate per rarity
        print("Collecting cheapest prices...")
        # market_handler.find_cheapest()

        # generate all possible trade-ups
        print("Generating trade-ups...")
        tradeup_generator.generate_tradeups(db_creds)

    if os.path.exists(os.path.join(WORKING_PATH.absolute(), "data/.bot-creds")):
        print("Starting bot...")
        with open(os.path.join(WORKING_PATH.absolute(), "data/.bot-creds"), "r") as f:
            token = f.read()
            f.close()

        bot.start_bot(token.strip())


if __name__ == "__main__":
    main()
