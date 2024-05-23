"""

CS Trade Up Analyzer

src/resource_collector.py

Developed by Keagan Bowman
Copyright 2024

Collects the resources required for trade up generation

"""

import re
import json
import db_handler
from models.weapon_classifiers import str_to_weapon, get_rarity, RarityToInt

# the following is a manually defined list of sets
# that aren't "crates" but can still have trade ups.
MANUAL_SETS = [
    ["CSGO_set_dust", "set_dust"],
    ["CSGO_set_aztec", "set_aztec"],
    ["CSGO_set_vertigo", "set_vertigo"],
    ["CSGO_set_inferno", "set_inferno"],
    ["CSGO_set_militia", "set_militia"],
    ["CSGO_set_nuke", "set_nuke"],
    ["CSGO_set_office", "set_office"],
    ["CSGO_set_assault", "set_assault"],
    ["CSGO_set_dust_2", "set_dust_2"],
    ["CSGO_set_train", "set_train"],
    ["CSGO_set_mirage", "set_mirage"],
    ["CSGO_set_italy", "set_italy"],
    ["CSGO_set_lake", "set_lake"],
    ["CSGO_set_safehouse", "set_safehouse"],
    ["CSGO_set_bank", "set_bank"],
    ["CSGO_set_overpass", "set_overpass"],
    ["CSGO_set_cobblestone", "set_cobblestone"],
    ["CSGO_set_baggage", "set_baggage"],
    ["CSGO_set_cache", "set_cache"],
    ["CSGO_set_gods_and_monsters", "set_gods_and_monsters"],
    ["CSGO_set_chopshop", 'set_chopshop'],
    ["CSGO_set_kimono", "set_kimono"],
    ["CSGO_set_nuke_2", "set_nuke_2"],
    ["CSGO_set_inferno_2", "set_inferno_2"],
    ["CSGO_set_xraymachine", "set_xraymachine"],
    ["CSGO_set_blacksite", "set_blacksite"],
    ["CSGO_set_stmarc", "set_stmarc"],
    ["CSGO_set_canals", "set_canals"],
    ["CSGO_set_norse", "set_norse"],
    ["CSGO_set_dust_2_2021", "set_dust_2_2021"],
    ["CSGO_set_mirage_2021", "set_mirage_2021"],
    ["CSGO_set_op10_ancient", "set_op10_ancient"],
    ["CSGO_set_train_2021", "set_train_2021"],
    ["CSGO_set_vertigo_2021", "set_vertigo_2021"],
    ["CSGO_set_anubis", "set_anubis"]
]

MANUAL_RARITY_OVERRIDES = {
    "[cu_usp_spitfire]weapon_usps_silencer": RarityToInt.Legendary,
    "[hy_blam_simple]weapon_awp": RarityToInt.Legendary
}


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

    for crate_id, set_id in MANUAL_SETS:
        name = translation_json['tokens'][crate_id.lower()]
        db_handler.add_crate(crate_id.lower(), name, set_id)

    for item in item_json['items']:
        # get object
        obj = item_json['items'][item]

        # check if item is a weapon case
        try:
            if obj['prefab'] == "weapon_case":
                # get crate ID
                item_id = obj['item_name'].lower().replace("#", "")

                # get crate name
                name = translation_json['tokens'][item_id]

                # get crate set id
                set_id = obj['tags']['itemset']['tag_value']

                # add crate to DB
                db_handler.add_crate(item_id, name, set_id)
        except KeyError:
            pass

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
        try:
            case = db_handler.get_crate_from_set(set_id)
        except TypeError:
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
    for set_id in item_json['client_loot_lists'].keys():
        set_data = set_id.split("_")

        rarity = get_rarity(set_data.pop(-1))

        if rarity is None:
            continue

        set_name = "_".join(set_data)

        try:
            db_handler.get_crate_from_set(set_name.replace("crate", "set").lower())
        except TypeError:
            continue

        for skin in item_json['client_loot_lists'][set_id].keys():
            db_handler.update_skin_rarity(skin, rarity.value)

    for skin in db_handler.get_skins_by_rarity(-1):
        if skin.skin_id in MANUAL_RARITY_OVERRIDES:
            rarity = MANUAL_RARITY_OVERRIDES[skin.skin_id]
        else:
            rarity = get_rarity(item_json['paint_kits_rarity'][skin.skin_tag])
        db_handler.update_skin_rarity(skin.skin_id, rarity.value)

    for case in db_handler.get_all_crates():
        counts = [0 for i in range(0, 6)]

        skins = db_handler.get_skins_by_crate(case.internal_id)

        for skin in skins:
            counts[skin.rarity] += 1

        db_handler.update_crate_counts(case.internal_id, counts[0], counts[1], counts[2], counts[3], counts[4],
                                       counts[5])

    db_handler.WORKING_DB.commit()
