"""

CS Trade Up Analyzer

src/db-handler.py

Developed by Keagan Bowman
Copyright 2024

Database operation handler for requests

"""

import sqlite3
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crates (
        internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        crate_id TEXT,
        crate_name TEXT,
        set_id TEXT
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
        FOREIGN KEY (crate_id) REFERENCES crates(crate_id)
                   );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tradeups (
        internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        skin_1_id INTEGER,
        skin_2_id INTEGER,
        skin_3_id INTEGER,
        skin_4_id INTEGER,
        skin_5_id INTEGER,
        skin_6_id INTEGER,
        skin_7_id INTEGER,
        skin_8_id INTEGER,
        skin_9_id INTEGER,
        skin_10_id INTEGER
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


def get_crate_from_internal(internal_id: int):
    cursor = WORKING_DB.cursor()

    crate = cursor.execute("SELECT * FROM crates WHERE internal_id = ?;", (internal_id,)).fetchone()

    cursor.close()

    return Crate(crate[0], crate[1], crate[2], crate[3])


def get_crate_from_set(set_id: str):
    cursor = WORKING_DB.cursor()

    crate = cursor.execute("SELECT * FROM crates WHERE set_id = ?;", (set_id,)).fetchone()

    cursor.close()

    return Crate(crate[0], crate[1], crate[2], crate[3])


def add_skin(skin_id: str, skin_tag: str, skin_name: str, weapon_type: int, rarity: int, min_wear: float, max_wear: float,
             crate_id: int, commit=False):
    cursor = WORKING_DB.cursor()

    cursor.execute("INSERT INTO skins (skin_id, skin_tag, skin_name, weapon_type, rarity, min_wear, max_wear, crate_id)"
                   " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (skin_id, skin_tag, skin_name, weapon_type, rarity, min_wear, max_wear, crate_id))

    cursor.close()

    if commit:
        WORKING_DB.commit()
