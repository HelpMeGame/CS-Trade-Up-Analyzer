"""

CS Trade Up Analyzer

src/models/weapon_classifier.py

Developed by Keagan Bowman
Copyright 2024

Enum declarations for classifying Counter Strike weapons to string/int counterparts

"""

import enum


class WeaponToInt(enum.Enum):
    P2000 = 1
    USPS = 2
    GLOCK = 3
    P250 = 4
    FIVESEVEN = 5
    TEC9 = 6
    CZ75 = 7
    DUALBERETTAS = 8
    DEAGLE = 9
    R8 = 10
    NOVA = 11
    XM1014 = 12
    MAG7 = 13
    SAWEDOFF = 14
    MP9 = 15
    MAC10 = 16
    PPBIZON = 17
    MP7 = 18
    UMP45 = 19
    P90 = 20
    MP5 = 21
    FAMAS = 22
    GALIL = 23
    M4A1 = 24
    M4A1S = 25
    AK47 = 26
    AUG = 27
    SG553 = 28
    SSG08 = 29
    AWP = 30
    SCAR20 = 31
    G3SG1 = 32
    M249 = 33
    NEGEV = 34
    MP5SD = 35
    ZEUS = 36
    KNIFE = 37


WeaponIntToStr = {
    1: "P2000",
    2: "USP-S",
    3: "Glock-18",
    4: "P250",
    5: "Five-SeveN",
    6: "Tec-9",
    7: "CZ75-Auto",
    8: "Dual Berettas",
    9: "Desert Eagle",
    10: "R8 Revolver",
    11: "Nova",
    12: "XM1014",
    13: "MAG-7",
    14: "Sawed-Off",
    15: "MP9",
    16: "MAC-10",
    17: "PP-Bizon",
    18: "MP7",
    19: "UMP-45",
    20: "P90",
    21: "MP5",
    22: "FAMAS",
    23: "Galil AR",
    24: "M4A4",
    25: "M4A1-S",
    26: "AK-47",
    27: "AUG",
    28: "SG 553",
    29: "SSG 08",
    30: "AWP",
    31: "SCAR-20",
    32: "G3SG1",
    33: "M249",
    34: "Negev",
    35: "MP5-SD",
    36: "ZEUS",
    37: "Knife"
}


class RarityToInt(enum.Enum):
    Common = 0  # Consumer
    Uncommon = 1  # Industrial
    Rare = 2  # Mil-Spec
    Mythical = 3  # Restricted
    Legendary = 4  # Classified
    Ancient = 5  # Covert
    Immortal = 6  # Exceedingly Rare


class WearsToStr(enum.StrEnum):
    FACTORYNEW = "Factory New"
    MINWEAR = "Minimal Wear"
    FIELDTESTED = "Field-Tested"
    WELLWORN = "Well-Worn"
    BATTLESCARRED = "Battle-Scarred"


class WearsToInt(enum.Enum):
    FACTORYNEW = 0
    MINWEAR = 1
    FIELDTESTED = 2
    WELLWORN = 3
    BATTLESCARRED = 4


str_to_wear = {
    "Factory New": WearsToInt.FACTORYNEW,
    "Minimal Wear": WearsToInt.MINWEAR,
    "Field-Tested": WearsToInt.FIELDTESTED,
    "Well-Worn": WearsToInt.WELLWORN,
    "Battle-Scarred": WearsToInt.BATTLESCARRED
}

wear_int_enum_to_str_enum = {
    WearsToInt.FACTORYNEW: WearsToStr.FACTORYNEW,
    WearsToInt.MINWEAR: WearsToStr.MINWEAR,
    WearsToInt.FIELDTESTED: WearsToStr.FIELDTESTED,
    WearsToInt.WELLWORN: WearsToStr.WELLWORN,
    WearsToInt.BATTLESCARRED: WearsToStr.BATTLESCARRED
}

wear_int_to_enum = {
    0: WearsToInt.FACTORYNEW,
    1: WearsToInt.MINWEAR,
    2: WearsToInt.FIELDTESTED,
    3: WearsToInt.WELLWORN,
    4: WearsToInt.BATTLESCARRED
}

str_to_rarity = {
    "common": RarityToInt.Common,  # Consumer
    "uncommon": RarityToInt.Uncommon,  # Industrial
    "rare": RarityToInt.Rare,  # Mil-Spec
    "mythical": RarityToInt.Mythical,  # Restricted
    "legendary": RarityToInt.Legendary,  # Classified
    "ancient": RarityToInt.Ancient,  # Covert
    "immortal": RarityToInt.Immortal  # Exceedingly Rare
}

game_rarity_to_rarity = {
    "consumer": RarityToInt.Common,  # Consumer
    "industrial": RarityToInt.Uncommon,  # Industrial
    "mil-spec": RarityToInt.Rare,  # Mil-Spec
    "restricted": RarityToInt.Mythical,  # Restricted
    "classified": RarityToInt.Legendary,  # Classified
    "covert": RarityToInt.Ancient,  # Covert
    "exceedingly rare": RarityToInt.Immortal  # Exceedingly Rare
}

rarity_int_to_game_rarity = {
    0: "Consumer",         # Consumer
    1: "Industrial",       # Industrial
    2: "Mil-Spec",         # Mil-Spec
    3: "Restricted",       # Restricted
    4: "Classified",       # Classified
    5: "Covert",           # Covert
    6: "Exceedingly Rare"  # Exceedingly Rare
}


str_to_weapon = {
    "tec9": WeaponToInt.TEC9,
    "ssg08": WeaponToInt.SSG08,
    "elite": WeaponToInt.DUALBERETTAS,
    "galilar": WeaponToInt.GALIL,
    "p90": WeaponToInt.P90,
    "cz75a": WeaponToInt.CZ75,
    "hkp2000": WeaponToInt.P2000,
    "aug": WeaponToInt.AUG,
    "bizon": WeaponToInt.PPBIZON,
    "mac10": WeaponToInt.MAC10,
    "xm1014": WeaponToInt.XM1014,
    "m4a1_silencer": WeaponToInt.M4A1S,
    "scar20": WeaponToInt.SCAR20,
    "usp_silencer": WeaponToInt.USPS,
    "ak47": WeaponToInt.AK47,
    "m4a1": WeaponToInt.M4A1,
    "mp7": WeaponToInt.MP7,
    "sg556": WeaponToInt.SG553,
    "glock": WeaponToInt.GLOCK,
    "deagle": WeaponToInt.DEAGLE,
    "awp": WeaponToInt.AWP,
    "mag7": WeaponToInt.MAG7,
    "famas": WeaponToInt.FAMAS,
    "sawedoff": WeaponToInt.SAWEDOFF,
    "p250": WeaponToInt.P250,
    "nova": WeaponToInt.NOVA,
    "ump45": WeaponToInt.UMP45,
    "g3sg1": WeaponToInt.G3SG1,
    "fiveseven": WeaponToInt.FIVESEVEN,
    "mp9": WeaponToInt.MP9,
    "m249": WeaponToInt.M249,
    "negev": WeaponToInt.NEGEV,
    "revolver": WeaponToInt.R8,
    "mp5sd": WeaponToInt.MP5SD,
    "taser": WeaponToInt.ZEUS,
}


def get_weapon(input_str: str) -> WeaponToInt | None:
    """
    Returns a WeaponToInt value based on the input string.

    :param input_str: string to attmept to translate
    :return: weapon value, None if no valid value is found
    """

    input_str = input_str.lower()
    if input_str in str_to_weapon.keys():
        return str_to_weapon[input_str]
    else:
        return None


def get_rarity(input_str: str) -> RarityToInt | None:
    """
    Returns a RarityToInt value based on the input string.

    :param input_str: string to attmept to translate
    :return: rarity value, None if no valid value is found
    """

    input_str = input_str.lower()
    if input_str in str_to_rarity.keys():
        return str_to_rarity[input_str]
    else:
        return None


def get_valid_wears(min_wear: float, max_wear: float, as_int: bool = False) -> list[WearsToStr] | list[WearsToInt]:
    """
    Returns a list of WearsToStr that fit inside the min_wear and max_wear arguments
    :param min_wear: minimum wear value
    :param max_wear:  maximum wear value
    :param as_int: should the valid wears be integers or strings?
    :return: a list of WearsToStr or WearsToInt values with all valid wear string values
    """

    # create list
    valid_wears = []

    # check Factory New
    if min_wear < 0.07 or 0.07 >= max_wear:
        if as_int:
            valid_wears.append(WearsToInt.FACTORYNEW)
        else:
            valid_wears.append(WearsToStr.FACTORYNEW)

    # check Minimal Wear
    if min_wear < 0.15 and (max_wear >= 0.15 or 0.07 <= max_wear):
        if as_int:
            valid_wears.append(WearsToInt.MINWEAR)
        else:
            valid_wears.append(WearsToStr.MINWEAR)

    # check Field-Tested
    if min_wear < 0.38 and (max_wear >= 0.38 or 0.15 <= max_wear):
        if as_int:
            valid_wears.append(WearsToInt.FIELDTESTED)
        else:
            valid_wears.append(WearsToStr.FIELDTESTED)

    # check Well-Worn
    if min_wear < 0.45 and (max_wear >= 0.45 or 0.38 <= max_wear):
        if as_int:
            valid_wears.append(WearsToInt.WELLWORN)
        else:
            valid_wears.append(WearsToStr.WELLWORN)

    # check Battle-Scarred
    if min_wear < 1 and (max_wear >= 1 or 0.45 <= max_wear):
        if as_int:
            valid_wears.append(WearsToInt.BATTLESCARRED)
        else:
            valid_wears.append(WearsToStr.BATTLESCARRED)

    return valid_wears

