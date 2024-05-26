"""

CS Trade Up Analyzer

src/db-handler.py

Developed by Keagan Bowman
Copyright 2024

Database operation handler for requests. Uses postgreSQL.

"""

import json
import psycopg2
from src.models.skin import Skin
from src.models.crate import Crate
from src.models.tradeup import TradeUp

WORKING_DB = None


def establish_db(creds, wipe_skin_data=False, wipe_price_data=False, wipe_trade_up_data=False):
    global WORKING_DB

    db = connect_to_db(creds)

    WORKING_DB = db

    cursor = db.cursor()

    if wipe_skin_data:
        cursor.execute("DROP TABLE IF EXISTS crates CASCADE")
        cursor.execute("DROP TABLE IF EXISTS skins CASCADE")
    if wipe_price_data:
        cursor.execute("DROP TABLE IF EXISTS cheapest CASCADE")
        cursor.execute("DROP TABLE IF EXISTS prices CASCADE")
    if wipe_trade_up_data:
        cursor.execute("DROP TABLE IF EXISTS tradeups CASCADE")
        cursor.execute("DROP TABLE IF EXISTS tradeup_skins CASCADE")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crates (
        internal_id SERIAL PRIMARY KEY,
        crate_id TEXT,
        crate_name TEXT,
        set_id TEXT,
        loot_table_id TEXT,
        rarity_0_count INTEGER,
        rarity_1_count INTEGER,
        rarity_2_count INTEGER,
        rarity_3_count INTEGER,
        rarity_4_count INTEGER,
        rarity_5_count INTEGER
                   );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skins (
        internal_id SERIAL PRIMARY KEY,
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
        internal_id SERIAL PRIMARY KEY,
        goal_skin INTEGER,
        goal_wear INTEGER,
        goal_rarity INTEGER,
        goal_weapon INTEGER,
        skin_1_count INTEGER,
        chance FLOAT,
        roi_10 FLOAT,
        profit_10 FLOAT,
        roi_100 FLOAT,
        profit_100 FLOAT,
        price_warning BOOLEAN,
        skin_1_price FLOAT,
        skin_2_price FLOAT,
        skin_1_max_wear FLOAT,
        skin_2_max_wear FLOAT,
        skin_1_margin FLOAT,
        skin_2_margin FLOAT,
        input_price FLOAT,
        FOREIGN KEY (goal_skin) REFERENCES skins(internal_id)
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
        internal_id SERIAL PRIMARY KEY,
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
        internal_id SERIAL PRIMARY KEY,
        skin_id INTEGER,
        wear_rating INTEGER,
        market_id INTEGER,
        price_data TEXT,
        buy_data TEXT,
        FOREIGN KEY (skin_id) REFERENCES skins(internal_id)
    );
    """)

    cursor.close()

    db.commit()

    return db


def connect_to_db(creds):
    db = psycopg2.connect(
        database=creds[0].strip(),
        host=creds[1].strip(),
        port=creds[2].strip(),
        user=creds[3].strip(),
        password=creds[4].strip()
    )

    return db


def add_crate(crate_id, crate_name, set_id, loot_table_id, commit=False):
    cursor = WORKING_DB.cursor()

    cursor.execute(f"INSERT INTO crates (crate_name, crate_id, set_id, loot_table_id) VALUES (%s, %s, %s, %s);",
                   (crate_name, crate_id, set_id, loot_table_id))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def update_crate_counts(crate_id: int, rarity_0: int, rarity_1: int, rarity_2: int, rarity_3: int, rarity_4: int,
                        rarity_5: int, commit: bool = False):
    cursor = WORKING_DB.cursor()

    cursor.execute(
        "UPDATE crates SET rarity_0_count = %s, rarity_1_count = %s, rarity_2_count = %s, rarity_3_count = %s, rarity_4_count = %s, rarity_5_count = %s WHERE internal_id = %s",
        (rarity_0, rarity_1, rarity_2, rarity_3, rarity_4, rarity_5, crate_id))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def get_crate_from_internal(internal_id: int):
    cursor = WORKING_DB.cursor()

    cursor.execute("SELECT * FROM crates WHERE internal_id = %s;", (internal_id,))
    crate = cursor.fetchone()

    cursor.close()

    if crate is None:
        return None

    return Crate(crate)


def get_crate_from_set(set_id: str):
    cursor = WORKING_DB.cursor()

    cursor.execute("SELECT * FROM crates WHERE set_id = %s;", (set_id,))
    crate = cursor.fetchone()

    cursor.close()

    if crate is None:
        return None

    return Crate(crate)


def get_all_crates(db=None):
    if db is None:
        db = WORKING_DB

    cursor = db.cursor()

    cursor.execute("SELECT * FROM CRATES")
    data = cursor.fetchall()

    cursor.close()

    crates = []
    for crate in data:
        crates.append(Crate(crate))

    return crates


def add_skin(skin_id: str, skin_tag: str, skin_name: str, weapon_type: int, rarity: int, min_wear: float,
             max_wear: float,
             crate_id: int, commit=False):
    cursor = WORKING_DB.cursor()

    cursor.execute(
        "INSERT INTO skins(skin_id, skin_tag, skin_name, weapon_type, rarity, min_wear, max_wear, crate_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (skin_id, skin_tag, skin_name, weapon_type, rarity, min_wear, max_wear, crate_id))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def update_skin_rarity(skin_id: str, rarity: int, commit: bool = False):
    cursor = WORKING_DB.cursor()

    cursor.execute("UPDATE skins SET rarity = %s WHERE skin_id = %s", (rarity, skin_id))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def get_all_skins():
    cursor = WORKING_DB.cursor()

    cursor.execute("SELECT * FROM skins")
    data = cursor.fetchall()

    cursor.close()

    skins = []
    for skin in data:
        skins.append(Skin(skin))

    return skins


def get_skins_by_rarity(rarity: int, db=None):
    if db is None:
        db = WORKING_DB

    cursor = db.cursor()

    cursor.execute("SELECT * FROM skins WHERE rarity = %s", (rarity,))

    data = cursor.fetchall()

    cursor.close()

    skins = []
    for skin in data:
        skins.append(Skin(skin))

    return skins


def get_skin_by_name(name: str):
    cursor = WORKING_DB.cursor()

    cursor.execute("SELECT * FROM skins WHERE skin_name = %s", (name,))

    data = cursor.fetchone()

    cursor.close()

    if data is None:
        return None

    return Skin(data)


def get_skins_by_search_name(search_name: str, weapon_type: int = None) -> list[str]:
    cursor = WORKING_DB.cursor()

    if weapon_type is not None:
        cursor.execute("SELECT skin_name FROM skins WHERE weapon_type = %s", (weapon_type,))
        data = cursor.fetchall()
    else:
        cursor.execute("SELECT skin_name FROM skins")
        data = cursor.fetchall()

    cursor.close()

    skins = []
    for skin in data:
        if skin[0].lower().startswith(search_name):
            skins.append(skin[0])

    return skins


def get_skins_by_crate(internal_id: int):
    cursor = WORKING_DB.cursor()

    cursor.execute("SELECT * FROM skins WHERE crate_id = %s", (internal_id,))
    data = cursor.fetchall()

    cursor.close()

    skins = []
    for skin in data:
        skins.append(Skin(skin))

    return skins


def get_skins_by_crate_and_rarity(crate_id: int, rarity: int, db=None):
    if db is None:
        db = WORKING_DB

    cursor = db.cursor()

    cursor.execute("SELECT * FROM skins WHERE crate_id = %s AND rarity = %s", (crate_id, rarity,))
    data = cursor.fetchall()

    cursor.close()

    skins = []
    for skin in data:
        skins.append(Skin(skin))

    return skins


def get_skin_prices_by_crate_rarity_and_wear(crate_id: int, rarity: int, wear: int):
    cursor = WORKING_DB.cursor()

    cursor.execute("SELECT internal_id FROM skins WHERE crate_id = %s AND rarity = %s",
                   (crate_id, rarity))
    data = cursor.fetchall()

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


def get_skin_by_id(internal_id: int):
    cursor = WORKING_DB.cursor()

    cursor.execute("SELECT * FROM skins WHERE internal_id = %s", (internal_id,))
    data = cursor.fetchone()

    cursor.close()

    if data is None:
        return None

    return Skin(data)


def get_prices(skin_id: int, wear: int, db=None):
    if db is None:
        db = WORKING_DB
    cursor = db.cursor()

    cursor.execute("SELECT price_data FROM prices WHERE skin_id = %s AND wear_rating = %s",
                   (skin_id, wear))
    data = cursor.fetchone()

    cursor.close()

    if data is None:
        return None

    data = json.loads(data[0])

    if data == {} or data == []:
        return None

    return data


def get_buy_orders(skin_id: int, wear: int):
    cursor = WORKING_DB.cursor()

    cursor.execute("SELECT buy_data FROM prices WHERE skin_id = %s AND wear_rating = %s",
                   (skin_id, wear))
    data = cursor.fetchone()

    cursor.close()

    if data is None:
        return None

    data = json.loads(data[0])

    if data == {} or data == []:
        return None

    return data


def get_market_hash(skin_id: float, wear: int):
    cursor = WORKING_DB.cursor()

    cursor.execute("SELECT market_id FROM prices WHERE skin_id = %s AND wear_rating = %s", (skin_id, wear))

    id = cursor.fetchone()

    cursor.close()

    if id is None:
        return None
    else:
        return int(id[0])


def update_price(market_hash: int, sell_orders: str, buy_orders: str, commit: bool=False):
    cursor = WORKING_DB.cursor()

    cursor.execute("UPDATE prices SET price_data=%s, buy_data=%s WHERE market_id = %s",
                   (sell_orders, buy_orders, market_hash))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def add_tradeup(skin_ids: list[int], goal_skin: int, goal_wear: int, goal_rarity: int, goal_weapon: int, skin_1_count,
                chance: float, roi_10: float,
                roi_100: float, profit_10: float,
                profit_100: float, price_warning: bool, skin_1_price: float, skin_2_price: float,
                skin_1_max_wear: float, skin_2_max_wear: float, skin_1_margin: float, skin_2_margin: float,
                input_price: float,
                commit: bool = False, db=None):
    if db is None:
        db = WORKING_DB

    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO tradeups (goal_skin, goal_wear, goal_rarity, goal_weapon, skin_1_count, chance, roi_10, roi_100, profit_10, profit_100, price_warning, skin_1_price, skin_2_price, skin_1_max_wear, skin_2_max_wear, skin_1_margin, skin_2_margin, input_price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING internal_id",
        (
            goal_skin, goal_wear, goal_rarity, goal_weapon, skin_1_count, chance, roi_10, roi_100, profit_10,
            profit_100, price_warning, skin_1_price, skin_2_price, skin_1_max_wear, skin_2_max_wear, skin_1_margin,
            skin_2_margin, input_price))

    tradeup_id = cursor.fetchone()[0]

    for skin in skin_ids:
        cursor.execute("INSERT INTO tradeup_skins (tradeup_id, skin_id) VALUES (%s, %s)", (tradeup_id, skin))

    cursor.close()

    if commit:
        db.commit()


def add_price(skin_id: int, wear: int, market_id: int, sell_data: str, buy_data: str, commit: bool = False):
    cursor = WORKING_DB.cursor()

    cursor.execute(
        "INSERT INTO prices (skin_id, wear_rating, market_id, price_data, buy_data) VALUES (%s, %s, %s, %s, %s)",
        (skin_id, wear, market_id, sell_data, buy_data))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def add_cheapest(crate_id: int, skin_id: int, rarity: int, wear: int, price: float, commit: bool = False):
    cursor = WORKING_DB.cursor()

    cursor.execute("INSERT INTO cheapest (crate_id, skin_id, rarity, wear, price) VALUES (%s, %s, %s, %s, %s)",
                   (crate_id, skin_id, rarity, wear, price))

    cursor.close()

    if commit:
        WORKING_DB.commit()


def get_cheapest_by_crate_rarity_and_wear(crate_id: int, rarity: int, wear: int, db=None):
    if db is None:
        db = WORKING_DB

    cursor = db.cursor()

    cursor.execute("SELECT skin_id, price FROM cheapest WHERE crate_id = %s AND rarity = %s AND wear = %s",
                   (crate_id, rarity, wear))
    data = cursor.fetchone()

    cursor.close()

    return data


async def get_tradeups_by_criteria(rarity: int, wear: int, weapon: int, skin_name: str, min_wear: float,
                                   max_wear: float, lower_bound: float, upper_bound: float, lower_roi: float,
                                   upper_roi: float, max_margin: float, offset: int, sort_by: str):
    criteria = [
        "((%s <= skin_1_max_wear AND %s >= skin_1_max_wear) AND (%s <= skin_2_max_wear AND %s >= skin_2_max_wear))",
        "input_price >= %s AND input_price <= %s", "%s <= roi_10 AND %s >= roi_10",
        "(%s >= skin_1_margin AND %s >= skin_2_margin)"
    ]
    values = [min_wear, max_wear, min_wear, max_wear, lower_bound, upper_bound, lower_roi, upper_roi, max_margin,
              max_margin]

    if rarity is not None:
        criteria.append("goal_rarity = %s")
        values.append(rarity)

    if wear is not None:
        criteria.append("goal_wear = %s")
        values.append(wear)

    if weapon is not None:
        criteria.append("goal_weapon = %s")
        values.append(weapon)

    if skin_name is not None:
        skin_id = get_skin_by_name(skin_name).internal_id
        criteria.append("goal_skin = %s")
        values.append(skin_id)

    if len(criteria) == 0:
        return None

    criteria_str = " AND ".join(criteria)

    values.append(offset * 10)

    values = tuple(values)

    cursor = WORKING_DB.cursor()

    cursor.execute(
        f"SELECT internal_id FROM tradeups WHERE {criteria_str} ORDER BY {sort_by} DESC LIMIT 10 OFFSET %s",
        values)
    data = cursor.fetchall()

    cursor.execute(f"SELECT internal_id FROM tradeups WHERE {criteria_str}",
                   values[0:-1])
    data_len = len(cursor.fetchall())

    cursor.close()

    tradeups = []

    for tradeup in data:
        tradeups.append(get_tradeup_by_id(tradeup[0]))

    return tradeups, data_len


def get_tradeup_by_id(tradeup_id):
    cursor = WORKING_DB.cursor()

    cursor.execute("SELECT * FROM tradeups WHERE internal_id = %s", (tradeup_id,))
    data = cursor.fetchone()

    if data is None:
        cursor.close()
        return None

    data = list(data)

    cursor.execute("SELECT * FROM skins WHERE internal_id = %s", (data[1],))
    goal_skin_data = cursor.fetchone()

    if goal_skin_data is None:
        cursor.close()
        return None

    data[1] = Skin(goal_skin_data)

    cursor.execute("SELECT skin_id FROM tradeup_skins WHERE tradeup_id = %s", (tradeup_id,))
    skin_ids = cursor.fetchall()

    if skin_ids is None:
        cursor.close()
        return None

    skin_data = []
    for skin_id in skin_ids:
        cursor.execute("SELECT * FROM skins WHERE internal_id = %s", (skin_id[0],))
        skin_data.append(cursor.fetchone())

    cursor.close()

    if skin_data is None:
        return None

    skins = []
    for skin in skin_data:
        if skin is not None:
            skins.append(Skin(skin))
        else:
            return None

    return TradeUp(data, skins)
