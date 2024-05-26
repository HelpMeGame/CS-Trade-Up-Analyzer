"""

CS Trade Up Analyzer

src/resource_collector.py

Developed by Keagan Bowman
Copyright 2024

Collects the resources required for trade up generation from extracted game files

"""

import re
import json
import db_handler
from models.weapon_classifiers import str_to_weapon, get_rarity


def gather_file_data(items_game_path: str, csgo_english_path: str) -> [dict, dict]:
    # open and read items_game.txt file
    with open(items_game_path, "r") as f:
        items_game = json.load(f)
        f.close()

    # open and read csgo_english.txt file
    with open(csgo_english_path, "r") as f:
        csgo_english = json.load(f)
        f.close()

    return items_game['items_game'], csgo_english['lang']


def collect_crates(item_json: dict, translation_json: dict) -> None:
    """
    Parses the items_game.txt and csgo_english.txt files to find crates to add to the database

    :return: Nothing. All discovered crates are added to the database.
    """

    for item in item_json['items']:
        # get object
        obj = item_json['items'][item]

        # check if item is a weapon case
        try:
            if obj['prefab'] == "weapon_case" or obj['prefab'] == "weapon_case_base" or obj['prefab'] == "weapon_case_souvenirpkg":
                if obj['prefab'] == "weapon_case_souvenirpkg":
                    item_id = obj['tags']['itemset']['tag_text'].lower().replace("#", "")
                else:
                    item_id = obj['item_name'].lower().replace("#", "")

                # get crate/set name
                name = translation_json['tokens'][item_id]

                if obj['prefab'] == "weapon_case_base":
                    # get loot table ID from loot list
                    loot_table_id = obj['loot_list_name']
                else:
                    # get loot table ID from supply crate series value
                    loot_table_index = obj['attributes']['set supply crate series']['value']
                    loot_table_id = item_json['revolving_loot_lists'][loot_table_index]

                    if obj['prefab'] == "weapon_case_souvenirpkg":
                        loot_table_id = list(item_json['client_loot_lists'][loot_table_id].keys())[0]

                # get crate set id
                set_id = obj['tags']['itemset']['tag_value']

                if db_handler.get_crate_from_set(set_id) is None:
                    # add crate to DB
                    db_handler.add_crate(item_id, name, set_id, loot_table_id)
        except KeyError:
            pass

    for item in item_json['quest_reward_loot_lists']:
        set_id = item_json['quest_reward_loot_lists'][item]

        if db_handler.get_crate_from_set(set_id) is not None:
            continue

        item_id = item_json['item_sets'][set_id]['name'].replace("#", "").lower()
        name = translation_json['tokens'][item_id]

        db_handler.add_crate(item_id, name, set_id, set_id)

    db_handler.WORKING_DB.commit()


def collect_skins(item_json: dict, translation_json: dict) -> None:
    """
    Gathers skin information from the parsed items_game.txt and csgo_english.txt files and adds it to the database.

    :param item_json: parsed items_game.txt data
    :param translation_json: parsed csgo_english.txt data
    :return: Nothing. Adds all skins to the database.
    """

    items_by_name = {}

    for item in item_json['paint_kits']:
        # get current item
        item = item_json['paint_kits'][item]

        try:
            if "wear_remap_min" in item.keys():
                wear_remap_min = item['wear_remap_min']
            else:
                wear_remap_min = 0

            if "wear_remap_max" in item.keys():
                wear_remap_max = item['wear_remap_max']
            else:
                wear_remap_max = 1

            # add item to items_by_name dictionary
            items_by_name[item['name'].lower()] = (
                translation_json['tokens'][item['description_tag'].lower().replace("#", "")],
                wear_remap_min,
                wear_remap_max
            )
        except KeyError:
            pass

    item_finder = re.compile("\[(.*)\]weapon_(.*)")

    for set_id in item_json['item_sets']:
        set_dict = item_json['item_sets'][set_id]

        # clean set_id to match DB
        set_id = set_id.lower().replace("#", "")

        # attempt to get the case from the set_id
        case = db_handler.get_crate_from_set(set_id)

        if case is None:
            continue

        # loop through items and add them to DB
        for item in set_dict['items'].keys():
            # gather weapon information
            skin_name, weapon_type = item_finder.match(item).groups()

            # get weapon_type int
            weapon_type = str_to_weapon[weapon_type].value

            name, min_wear, max_wear = items_by_name[skin_name]

            to_replace = [
                ("Ã¶", "ö"),
                ("é¾çŽ‹", "龍王"),
                ("å£±", "壱"),
                ("å¼", "弐")
            ]

            for old, new in to_replace:
                name = name.replace(old, new)

            db_handler.add_skin(item, skin_name, name, weapon_type, -1, min_wear, max_wear, case.internal_id)

    db_handler.WORKING_DB.commit()


def collect_rarities(item_json: dict):
    loot_lists = item_json['client_loot_lists']
    for crate in db_handler.get_all_crates():
        try:
            rarities = loot_lists[crate.loot_table_id]
        except KeyError:
            continue

        for key in rarities.keys():
            try:
                rarity = get_rarity(key.split("_")[-1]).value
            except AttributeError:
                continue

            for skin in loot_lists[key].keys():
                db_handler.update_skin_rarity(skin, rarity)

    # handle remaining skins
    for skin in db_handler.get_skins_by_rarity(-1):
        rarity = get_rarity(item_json['paint_kits_rarity'][skin.skin_tag]).value
        db_handler.update_skin_rarity(skin.skin_id, rarity)

    for case in db_handler.get_all_crates():
        counts = [0 for i in range(0, 6)]

        skins = db_handler.get_skins_by_crate(case.internal_id)

        for skin in skins:
            counts[skin.rarity] += 1

        db_handler.update_crate_counts(case.internal_id, counts[0], counts[1], counts[2], counts[3], counts[4],
                                       counts[5])

    db_handler.WORKING_DB.commit()
