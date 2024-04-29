"""

CS Trade Up Analyzer

src/main.py

Developed by Keagan Bowman
Copyright 2024

Main file for analyzer start up. Attempts to use all combinations of Counter Strike weapon skins and
Steam Community Market price data to identify ideal trade ups with a net positive result.

"""

import os
import pathlib
import db_handler
import resource_collector

WORKING_PATH = pathlib.Path(os.curdir)


def main():
    # gather the data from the resource files
    items_game, translations = resource_collector.gather_file_data(
        os.path.join(WORKING_PATH.absolute(), "data/items_game.json"),
        os.path.join(WORKING_PATH.absolute(), "data/csgo_english.json")
    )

    should_wipe = True

    # establish connection to database
    db_handler.connect_to_db(os.path.join(WORKING_PATH.absolute(), "data/skins.db"), wipe_db=should_wipe)

    if should_wipe:
        # collect crate information
        resource_collector.collect_crates(items_game, translations)

        # collect skin information
        resource_collector.collect_skins(items_game, translations)


if __name__ == "__main__":
    main()
