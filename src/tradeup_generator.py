"""

CS Trade Up Analyzer

src/tradeup_generator.py

Developed by Keagan Bowman
Copyright 2024

Generator algorithms for determining best possible trade ups for a given skin

"""

import db_handler
from src.models.weapon_classifiers import get_valid_wears


def generate_tradeups():
    for i in range(1, 6):

        # get skins of this rarity
        skins = db_handler.get_skins_by_rarity(i)

        print(f"\t > Generating combinations for rarity {i} ({len(skins)} items)...")

        for skin in skins:
            for wear in get_valid_wears(skin.min_wear, skin.max_wear, True):
                # get the lowest value for this crate
                data = db_handler.get_cheapest_by_crate_rarity_and_wear(skin.crate_id, i - 1,
                                                                        wear.value)

                if data is None:
                    continue
                else:
                    lowest_skin_id, lowest_value = data

                skin_value = db_handler.get_prices(skin.internal_id, wear.value)

                if skin_value is not None:
                    skin_value = skin_value[0][0] * 0.95  # account for market tax
                else:
                    continue

                best_count = 1

                # find highest possible combination that could make money
                while best_count <= 10 and best_count * skin_value < skin_value:
                    best_count += 1

                # get the remaining amount
                remaining = skin_value - (best_count * lowest_value)

                # skip where the remaining is less than zero with a best count of 1
                if remaining <= 0 and best_count == 1:
                    continue

                # check to ensure we can at least put 3 cent skins in
                while (10 - best_count) * 0.03 >= remaining and best_count > 0:
                    best_count -= 1

                # skip where best count can't be decreased
                if best_count <= 0:
                    continue

                # double-check the remaining value
                remaining = skin_value - (best_count * lowest_value)

                # get the best filler skin
                filler_skin = find_best_fit(remaining, 10 - best_count, wear.value, i - 1)

                # no filler skin available, skip
                if filler_skin is None:
                    continue

                # add tradeup to DB
                db_handler.add_tradeup([skin.internal_id, filler_skin])

    # commit trade ups to the DB
    db_handler.WORKING_DB.commit()


def find_best_fit(remaining_value, remaining_count, wear, rarity) -> int:
    # gather all cases, sort by rarity count for this rarity
    cases = db_handler.get_all_crates()
    cases.sort(key=lambda x: x.rarity_counts[rarity])

    # set the best values to empty
    best_skin = None
    best_price = None
    best_count = None
    best_profit = 0

    # loop through all cases
    for case in cases:
        # set current count to the rarity count for this case
        current_count = case.rarity_counts[rarity]

        # find the cheapest skin from this case in this rarity/wear
        cheapest = db_handler.get_cheapest_by_crate_rarity_and_wear(case.internal_id, rarity, wear)

        # no cheapest, skip this one
        if cheapest is None:
            continue

        # set some variables
        cheapest_id, cheapest_price = cheapest

        # assign default best variables
        if best_skin is None:
            best_skin = cheapest_id
            best_price = cheapest_price
            best_count = current_count
            best_profit = remaining_value - (best_price * remaining_count)
            continue

        # calculate profit with current skin
        current_profit = remaining_value - (cheapest_price * remaining_count)

        # no profit, skip this filler skin
        if current_profit <= 0:
            continue

        new_best = False

        # if this skin is better in every way, replace the best
        if cheapest_price < best_price and current_count < best_count and current_profit > best_profit:
            new_best = True
        # otherwise, if this skin has better chances and a higher profit, replace the old best
        elif current_count < best_count and current_profit > best_profit:
            new_best = True

        # update best variables
        if new_best:
            best_skin = cheapest_id
            best_price = cheapest_price
            best_count = current_count
            best_profit = remaining_value - (best_price * remaining_count)

    # return the best filler skin
    if (remaining_count * best_price) >= remaining_value:
        return None
    else:
        return best_skin
