"""

CS Trade Up Analyzer

src/db-handler.py

Developed by Keagan Bowman
Copyright 2024

Database operation handler for requests

"""

import json
import sqlite3
from src.models.skin import Skin
from models.crate import Crate

WORKING_DB: sqlite3.Connection = None


def connect_to_db(path: str, wipe_db=False):
    global WORKING_DB

    db = sqlite3.connect(path)
    WORKING_DB = db

    cursor = db.cursor()

    if wipe_db:
        cursor.execute("DROP TABLE IF EXISTS crates")
        cursor.execute("DROP TABLE IF EXISTS skins")
        cursor.execute("DROP TABLE IF EXISTS tradeups")
        cursor.execute("DROP TABLE IF EXISTS tradeup_skins")
        # cursor.execute("DROP TABLE IF EXISTS cheapest")
        # cursor.execute("DROP TABLE IF EXISTS prices")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crates (
        internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        crate_id TEXT,
        crate_name TEXT,
        set_id TEXT,
        rarity_0_count INTEGER,
        rarity_1_count INTEGER,
        rarity_2_count INTEGER,
        rarity_3_count INTEGER,
        rarity_4_count INTEGER,
        rarity_5_count INTEGER
                   );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skins (
        internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        skin_id TEXT UNIQUE,
        skin_tag TEXT,
        skin_name TEXT,
        weapon_type INTEGER,
        rarity INTEGER,
        min_wear FLOAT,
        max_wear FLOAT,
        crate_id INTEGER,
        FOREIGN KEY (crate_id) REFERENCES crates(internal_id)
                   );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tradeups (
        internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chance FLOAT,
        roi_10 FLOAT,
        profit_10 FLOAT,
        roi_100 FLOAT,
        profit_100 FLOAT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tradeup_skins (
        tradeup_id INTEGER NOT NULL,
        skin_id INTEGER NOT NULL,
        FOREIGN KEY (tradeup_id) REFERENCES tradeups(internal_id),
        FOREIGN KEY (skin_id) REFERENCES skins(internal_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cheapest (
        internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        crate_id INTEGER,
        skin_id INTEGER,
        rarity INTEGER,
        wear INTEGER,
        price FLOAT,
        FOREIGN KEY (crate_id) REFERENCES crates(internal_id),
        FOREIGN KEY (skin_id) REFERENCES skins(internal_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prices (
        internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        skin_id INTEGER,
        wear_rating INTEGER,
        market_id INTEGER,
        price_data TEXT,
        FOREIGN KEY (skin_id) REFERENCES skins(internal_id)
    );
    """)

    cursor.close()

    db.commit()

    return db


def add_crate(crate_id, crate_name, set_id, commit=False):
    cursor = WORKING_DB.cursor()

    cursor.execute("INSERT INTO crates (crate_name, crate_id, set_id) VALUES (?, ?, ?);",
                   (crate_name, crate_id, set_id))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def update_crate_counts(crate_id: int, rarity_0: int, rarity_1: int, rarity_2: int, rarity_3: int, rarity_4: int,
                        rarity_5: int, commit: bool = False):
    cursor = WORKING_DB.cursor()

    cursor.execute("UPDATE crates SET rarity_0_count = ?, rarity_1_count = ?, rarity_2_count = ?, rarity_3_count = ?, rarity_4_count = ?, rarity_5_count = ? WHERE internal_id = ?",
                   (rarity_0, rarity_1, rarity_2, rarity_3, rarity_4, rarity_5, crate_id))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def get_crate_from_internal(internal_id: int):
    cursor = WORKING_DB.cursor()

    crate = cursor.execute("SELECT * FROM crates WHERE internal_id = ?;", (internal_id,)).fetchone()

    cursor.close()

    return Crate(crate)


def get_crate_from_set(set_id: str):
    cursor = WORKING_DB.cursor()

    crate = cursor.execute("SELECT * FROM crates WHERE set_id = ?;", (set_id,)).fetchone()

    cursor.close()

    return Crate(crate)


def get_all_crates():
    cursor = WORKING_DB.cursor()

    data = cursor.execute("SELECT * FROM CRATES").fetchall()

    cursor.close()

    crates = []
    for crate in data:
        crates.append(Crate(crate))

    return crates


def add_skin(skin_id: str, skin_tag: str, skin_name: str, weapon_type: int, rarity: int, min_wear: float,
             max_wear: float,
             crate_id: int, commit=False):
    cursor = WORKING_DB.cursor()

    cursor.execute("INSERT INTO skins (skin_id, skin_tag, skin_name, weapon_type, rarity, min_wear, max_wear, crate_id)"
                   " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (skin_id, skin_tag, skin_name, weapon_type, rarity, min_wear, max_wear, crate_id))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def update_skin_rarity(skin_id: str, rarity: int, commit: bool = False):
    cursor = WORKING_DB.cursor()

    cursor.execute("UPDATE skins SET rarity = ? WHERE skin_id = ?", (rarity, skin_id))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def get_all_skins():
    cursor = WORKING_DB.cursor()

    data = cursor.execute("SELECT * FROM skins").fetchall()

    cursor.close()

    skins = []
    for skin in data:
        skins.append(Skin(skin))

    return skins


def get_skins_by_rarity(rarity: int):
    cursor = WORKING_DB.cursor()

    data = cursor.execute("SELECT * FROM skins WHERE rarity = ?", (rarity,)).fetchall()

    cursor.close()

    skins = []
    for skin in data:
        skins.append(Skin(skin))

    return skins


def get_skins_by_crate(internal_id: int):
    cursor = WORKING_DB.cursor()

    data = cursor.execute("SELECT * FROM skins WHERE crate_id = ?", (internal_id,)).fetchall()

    cursor.close()

    skins = []
    for skin in data:
        skins.append(Skin(skin))

    return skins


def get_skin_prices_by_crate_rarity_and_wear(crate_id:int, rarity:int, wear:int):
    cursor = WORKING_DB.cursor()

    data = cursor.execute("SELECT internal_id FROM skins WHERE crate_id = ? AND rarity = ?", (crate_id, rarity)).fetchall()

    skins = []
    prices = []

    for skin in data:
        price = get_prices(skin[0], wear)

        skins.append(skin[0])

        if price is not None:
            prices.append(price[0][0])
        else:
            prices.append(0)

    return skins, prices


def get_prices(skin_id: int, wear: int):
    cursor = WORKING_DB.cursor()

    data = cursor.execute("SELECT price_data FROM prices WHERE skin_id = ? AND wear_rating = ?",
                          (skin_id, wear)).fetchone()

    cursor.close()

    if data is None:
        return None

    data = json.loads(data[0])

    if data == {} or data == []:
        return None

    return data


def add_tradeup(skin_ids: list[int], chance: float, roi_10: float, roi_100: float, profit_10:float , profit_100: float, commit: bool=False):
    cursor = WORKING_DB.cursor()

    cursor.execute("INSERT INTO tradeups (chance, roi_10, roi_100, profit_10, profit_100) VALUES (?, ?, ?, ?, ?)", (chance, roi_10, roi_100, profit_10, profit_100))
    tradeup_id = cursor.execute("SELECT internal_id FROM tradeups WHERE ROWID = ?", (cursor.lastrowid,)).fetchone()[0]

    for skin in skin_ids:
        cursor.execute("INSERT INTO tradeup_skins (tradeup_id, skin_id) VALUES (?, ?)", (tradeup_id, skin))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def add_price(skin_id: int, wear: int, market_id: int, price: str, commit: bool = False):
    cursor = WORKING_DB.cursor()

    cursor.execute("INSERT INTO prices (skin_id, wear_rating, market_id, price_data) VALUES (?, ?, ?, ?)",
                   (skin_id, wear, market_id, price))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def add_cheapest(crate_id: int, skin_id: int, rarity: int, wear: int, price: float, commit: bool = False):
    cursor = WORKING_DB.cursor()

    cursor.execute("INSERT INTO cheapest (crate_id, skin_id, rarity, wear, price) VALUES (?, ?, ?, ?, ?)",
                   (crate_id, skin_id, rarity, wear, price))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def get_cheapest_by_crate_rarity_and_wear(crate_id: int, rarity: int, wear: int):
    cursor = WORKING_DB.cursor()

    data = cursor.execute("SELECT skin_id, price FROM cheapest WHERE crate_id = ? AND rarity = ? AND wear = ?",
                          (crate_id, rarity, wear)).fetchone()

    cursor.close()

    return data
