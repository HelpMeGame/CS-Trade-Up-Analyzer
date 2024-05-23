from models.weapon_classifiers import WearsToInt, WeaponIntToStr, get_valid_wears, wear_int_enum_to_str_enum
from urllib.parse import quote
import requests as req
import db_handler
import datetime
import random
import time
import json
import re


def find_cheapest() -> None:
    # gather all crates
    crates = db_handler.get_all_crates()

    # loop through all crates
    for crate in crates:
        # gather skins based on rarity in crate
        skins_by_rarity = {}
        for skin in db_handler.get_skins_by_crate(crate.internal_id):
            try:
                skins_by_rarity[skin.rarity].append(skin)
            except KeyError:
                skins_by_rarity[skin.rarity] = [skin]

        # loop through each rarity
        for rarity in skins_by_rarity.keys():
            # loop through each wear rating
            for wear in range(WearsToInt.FACTORYNEW.value, WearsToInt.BATTLESCARRED.value + 1):
                cheapest = None
                lowest_price = None

                # loop through all skins in this rarity
                for skin in skins_by_rarity[rarity]:
                    # attempt to get price from the DB
                    prices = db_handler.get_prices(skin.internal_id, wear)

                    # if there is no valid price, skip this
                    if prices is None:
                        continue

                    total = 0
                    current_price = 0

                    for i in prices:
                        price, count, _ = i

                        total += count
                        current_price = price

                        if count >= 10:
                            break

                    # check if this price is lower than the current lowest
                    if lowest_price is None or (current_price is not None and total >= 10 and current_price < lowest_price):
                        cheapest = skin
                        lowest_price = current_price

                # if the cheapest isn't none, we add it to the db
                if cheapest is not None:
                    db_handler.add_cheapest(crate.internal_id, cheapest.internal_id, rarity, wear, lowest_price)

    db_handler.WORKING_DB.commit()


def get_prices(steam_creds: tuple[str, str]) -> None:
    # set Steam request URLs
    market_root = "https://steamcommunity.com/market/listings/730/"
    item_order_root = "https://steamcommunity.com/market/itemordershistogram?country=US&language=english&currency=1&item_nameid="

    # create regex for extracting market ids
    market_id_finder = re.compile(b'Market_LoadOrderSpread\(\s*([0-9]*)\s*\)')

    # set cookies
    cookie_jar = {
        "sessionid": steam_creds[0].strip(),
        "steamLoginSecure": steam_creds[1].strip()
    }

    # get all skins
    skins = db_handler.get_all_skins()

    # create a list of skins to find
    to_retrieve = []

    # loop through skins and valid wears
    for skin in skins:
        for wear in get_valid_wears(skin.min_wear, skin.max_wear, as_int=True):
            if db_handler.get_prices(skin.internal_id, wear.value) is None:
                to_retrieve.append((skin.weapon_type, skin.skin_name, wear, skin.internal_id))

    print(f"Gathering {len(to_retrieve)} market prices...")

    for i in range(len(to_retrieve)):
        weapon, name, wear, skin_id = to_retrieve[i]

        # remaining time estimator
        remaining = (len(to_retrieve) - (i + 1)) * 20
        print(f"\t\t > Handling {i + 1}/{len(to_retrieve)} (~{remaining} seconds -- ETA: "
              f"{(datetime.datetime.now() + datetime.timedelta(seconds=remaining)).strftime('%I:%M %p, %b %e')})")

        # get weapon string
        weapon = WeaponIntToStr[int(weapon)]

        # account for souvenir lab rats skin
        if name == "Lab Rats":
            weapon = "Souvenir " + weapon

        # create market hash name
        hash_name = f"{weapon} | {name.strip()} ({wear_int_enum_to_str_enum[wear].value})"

        try:
            del cookie_jar["Referer"]
        except KeyError:
            pass

        # grab HTML for page
        try:
            html = req.get(url=market_root + quote(hash_name), cookies=cookie_jar).content
        except:
            # sleep in case the request fails, attempts to let rate limits flow over
            time.sleep(1800)
            html = req.get(url=market_root + quote(hash_name), cookies=cookie_jar).content


        try:
            # gather market ID
            market_id = int(market_id_finder.findall(html)[0])

            # set referer URL to avoid rate limits
            cookie_jar["Referer"] = market_root + quote(hash_name)

            # send get request
            try:
                r = req.get(url=item_order_root + str(market_id), cookies=cookie_jar)
            except:
                # sleep in case the request fails, attempts to let rate limits flow over
                time.sleep(1800)
                r = req.get(url=item_order_root + str(market_id), cookies=cookie_jar)

            # parse returned JSON
            price_data = r.json()
            sell_orders = price_data['sell_order_graph']
            buy_orders = price_data['buy_order_graph']
        except IndexError:
            sell_orders = {}
            buy_orders = {}
            market_id = -1

        # add the price to the database
        db_handler.add_price(skin_id, wear.value, market_id, json.dumps(sell_orders), json.dumps(buy_orders), commit=True)

        # check if we are on the last skin or not
        if i + 1 != len(to_retrieve):
            # sleep for 12-20 seconds to avoid rate limit
            time.sleep(random.randrange(13, 15))
