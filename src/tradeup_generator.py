"""

CS Trade Up Analyzer

src/tradeup_generator.py

Developed by Keagan Bowman
Copyright 2024

Generator algorithms for determining best possible trade ups for a given skin

"""

import math
import random
import db_handler
from src.models.weapon_classifiers import get_valid_wears


def generate_tradeups():
    for i in range(1, 6):

        # get skins of this rarity
        skins = db_handler.get_skins_by_rarity(i)

        print(f"\t > Generating combinations for rarity {i} ({len(skins)} items)...")

        # loop through skins
        for skin in skins:
            # loop through all valid wear ratings
            for wear in get_valid_wears(skin.min_wear, skin.max_wear, True):
                # get the lowest trade up value for this crate (one rarity below)
                data = db_handler.get_cheapest_by_crate_rarity_and_wear(skin.crate_id, i - 1,
                                                                        wear.value)

                if data is None:
                    continue
                else:
                    lowest_skin_id, lowest_value = data

                skin_ids = [lowest_skin_id]

                # get this skin's value
                skin_value = db_handler.get_prices(skin.internal_id, wear.value)

                # check to make sure skin has valid value
                if skin_value is not None:
                    skin_value = skin_value[0][0] * 0.95  # account for market tax
                else:
                    continue

                # set min count to 10
                best_count = 10

                # find highest possible combination that could make money (increases chances)
                while best_count > 0 and lowest_value * best_count > skin_value:
                    best_count -= 1

                # skip where best count can't be decreased
                if best_count <= 0:
                    continue

                # double-check the remaining value
                remaining = skin_value - (best_count * lowest_value)

                if best_count != 10:
                    # get the best filler skin
                    filler_skin, filler_case, filler_skin_cost = find_best_fit(skin.crate_id, remaining, 10 - best_count, wear.value,
                                                                               i - 1)

                    # no filler skin available, skip
                    if filler_skin is None:
                        continue
                    else:
                        skin_ids.append(filler_skin)

                    input_cost = (lowest_value * best_count) + ((10 - best_count) * filler_skin_cost)

                    case_2_items, case_2_prices = db_handler.get_skin_prices_by_crate_rarity_and_wear(filler_case, i,
                                                                                                      wear.value)
                else:
                    # in the instance where we can make money with 10 of the same skin
                    case_2_items = []
                    case_2_prices = []
                    input_cost = lowest_value * 10

                # get case information
                case = db_handler.get_crate_from_internal(db_handler.get_skin_by_id(lowest_skin_id).crate_id)

                case_1_items, case_1_prices = db_handler.get_skin_prices_by_crate_rarity_and_wear(case.internal_id, i,
                                                                                                  wear.value)

                # calculate success chance
                total_tickets = (len(case_1_items) * best_count) + (len(case_2_items) * (10 - best_count))

                chance = best_count / total_tickets

                roi_10, roi_100, profit_10, profit_100 = simulate(input_cost, case_1_prices, case_2_prices,
                                                                  total_tickets, best_count)

                # add tradeup to DB
                db_handler.add_tradeup(skin_ids, skin.internal_id, wear.value, i, skin.weapon_type, best_count, chance, roi_10, profit_10,
                                       roi_100, profit_100, lowest_value, filler_skin_cost)

    # commit trade ups to the DB
    db_handler.WORKING_DB.commit()


def find_best_fit(origin_case_id, remaining_value, remaining_count, wear, rarity) -> int:
    # gather all cases, sort by rarity count for this rarity
    cases = db_handler.get_all_crates()
    cases.sort(key=lambda x: x.rarity_counts[rarity])

    # set the best values to empty
    best_skin = None
    best_price = None
    best_count = None
    best_case = None
    best_profit = 0

    # loop through all cases
    for case in cases:
        if case.internal_id == origin_case_id:
            continue

        # set current count to the rarity count for this case
        current_count = case.rarity_counts[rarity]

        try:
            if case.rarity_counts[rarity + 1] == 0:
                continue
        except IndexError:
            continue

        # find the cheapest skin from this case in this rarity/wear
        cheapest = db_handler.get_cheapest_by_crate_rarity_and_wear(case.internal_id, rarity, wear)

        # no cheapest, skip this one
        if cheapest is None:
            continue

        # set some variables
        cheapest_id, cheapest_price = cheapest

        # calculate profit with current skin
        current_profit = remaining_value - (cheapest_price * remaining_count)

        # assign default best variables
        if best_skin is None and current_profit > 0:
            best_skin = cheapest_id
            best_price = cheapest_price
            best_count = current_count
            best_profit = current_profit
            best_case = case.internal_id
            continue

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
            best_case = case.internal_id

    # return the best filler skin
    if best_price is None or remaining_count * best_price >= remaining_value:
        return None, None, None
    else:
        return best_skin, best_case, best_price


def simulate(input_costs: float, case_1_prices: list[float], case_2_prices: list[float],
             total_tickets: int,
             best_count: int):
    # set default ROI lists to empty
    roi_10 = []
    roi_100 = []

    # set default profits to 0
    profit_10 = 0
    profit_100 = 0

    # copy all values into a new array
    all_prices = case_1_prices.copy()
    all_prices.extend(case_2_prices)

    chance_range = [best_count]

    # add chance for case 1 items
    for i in range(len(case_1_prices) - 1):
        chance_range.append(chance_range[-1] + best_count)

    # add chance for case 2 items
    for i in range(len(case_2_prices)):
        chance_range.append(chance_range[-1] + (10 - best_count))

    # simulate 100 random trade ups
    for i in range(100):
        # get random value
        r = random.randint(1, total_tickets)

        # get price from r
        if r <= chance_range[0]:
            price = all_prices[0]
        else:
            # loop through price ranges to find best match
            for j in range(0, len(chance_range) - 1):
                # check range
                if chance_range[j] < r <= chance_range[j + 1]:
                    price = all_prices[j]
                    break
            else:
                price = all_prices[-1]

        # get roi for this simulation
        roi = price / input_costs
        profit = (-1 * input_costs) + price

        # add to roi lists
        roi_100.append(roi)
        profit_100 += profit
        if i < 10:
            roi_10.append(roi)
            profit_10 += profit

    # return average ROI values and profits
    return sum(roi_10) / len(roi_10), sum(roi_100) / len(roi_100), profit_10, profit_100
