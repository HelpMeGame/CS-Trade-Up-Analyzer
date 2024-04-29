import re
import json
import db_handler
from models.weapon_classifiers import str_to_weapon, get_rarity


def gather_file_data(items_game_path: str, csgo_english_path: str) -> [dict, dict]:
    with open(items_game_path, "r") as f:
        items_game = json.load(f)
        f.close()

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
            if "wear_default" in item.keys():
                wear_remap_min = item['wear_default']
                wear_remap_max = item['wear_default']
            elif "wear_remap_min" in item.keys():
                wear_remap_min = item['wear_remap_min']
                wear_remap_max = item['wear_remap_max']
            else:
                wear_remap_min = 0
                wear_remap_max = 1

            # add item to items_by_name dictionary
            items_by_name[item['name'].lower()] = (
                item['description_tag'].lower().replace("#", ""),
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

            rarity = get_rarity(item_json['paint_kits_rarity'][skin_name]).value

            db_handler.add_skin(item, skin_name, name, weapon_type, rarity, min_wear, max_wear, case.internal_id)

    db_handler.WORKING_DB.commit()
