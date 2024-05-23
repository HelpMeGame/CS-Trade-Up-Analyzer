"""

CS Trade Up Analyzer

src/tradeup_generator.py

Developed by Keagan Bowman
Copyright 2024

Generator algorithms for determining best possible trade ups for a given skin

"""

import random
import threading
import db_handler
from src.models.skin import Skin
from src.models.weapon_classifiers import get_valid_wears
from src.models.simulation_possibility import SimulationPossibility

THREAD_COUNT = 16


def generate_tradeups(db_creds):
    for i in range(1, 6):

        # get skins of this rarity
        skins = db_handler.get_skins_by_rarity(i)

        print(f"\t> Generating combinations for rarity {i} ({len(skins)} items)...")

        # expected wear rating calculations:
        # loop starts inside for wear in get_valid_wears(...):
        #   > forces consideration for cheapest skin.
        #   > see below for more info
        # start at highest wear rating (cheaper) that can reasonably produce a valid skin.
        #   > this loop should be started with the cheapest skin in a crate
        #   > potentially change later to include all valid skins from the crate
        # decrease considered wear rating by 0.01 at every loop
        # write algorithm to determine max value of float for filler skins
        # expected float = ((goal_max_float - goal_min_float) * average_float) + goal_min_float

        # create empty list for skins
        divided_list = [[] for i in range(THREAD_COUNT)]

        # shuffle skins to hopefully achieve a faster runtime
        random.shuffle(skins)

        # split skins into divided skin list
        for i in range(len(skins)):
            divided_list[i % THREAD_COUNT].append(skins[i])

        # create empty thread tracker
        threads = []

        # create & start threads
        for i in range(THREAD_COUNT):
            # create a thread to work on a skin
            threads.append(threading.Thread(target=generate_tradeup, args=[db_creds, divided_list[i]]))

        # start threads
        for thread in threads:
            thread.start()

        # track total completed
        total_complete = 0

        # wait for threads to finish running
        for i in range(len(threads)):
            threads[i].join()
            total_complete += len(divided_list[i])
            print(f"\t\t> Completed {total_complete}/{len(skins)}")


def find_best_fit(origin_case_id: int, remaining_value: float, remaining_count: float, wear: int, rarity: int,
                  db) -> tuple:
    # gather all cases, sort by rarity count for this rarity
    cases = db_handler.get_all_crates(db)

    # sorting by rarity count starts us with less skins in this rarity
    cases.sort(key=lambda x: x.rarity_counts[rarity])

    # set the best values to empty
    best_skin = None
    best_price = None
    best_count = None
    best_case = None
    best_profit = 0

    # loop through all cases
    for case in cases:
        # skip the origin case, that would be redundant
        if case.internal_id == origin_case_id:
            continue

        # set current count to the rarity count for this case
        current_count = case.rarity_counts[rarity]

        # check to see if this case has valid trade ups into our specified rarity
        try:
            if case.rarity_counts[rarity + 1] == 0:
                continue
        except IndexError:
            continue

        # find the cheapest skin from this case in this rarity/wear
        cheapest = db_handler.get_cheapest_by_crate_rarity_and_wear(case.internal_id, rarity, wear, db)

        # if the case has no valid cheapest skin, skip it
        if cheapest is None:
            continue

        # otherwise set the proper values
        cheapest_id, cheapest_price = cheapest

        # calculate profit with current skin
        current_profit = remaining_value - (cheapest_price * remaining_count)

        # assign default best variables (for first run only)
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


def simulate(input_costs: float,
             case_1_possibilities: list[SimulationPossibility],
             case_2_possibilities: list[SimulationPossibility],
             total_tickets: int,
             best_count: int,
             average_wear: float,
             db,
             iterations: int = 100):
    # set default ROI lists to empty
    roi_10 = []
    roi_100 = []

    # set default profits to 0
    profit_10 = 0
    profit_100 = 0

    # set the price warning flag to False
    # this will be True when an item with an unknown price was created
    price_warning = False

    # create a "chance range", which works with a random number generator to choose a reward
    chance_range = [best_count]

    # combine all possibilities into a single list
    all_skins = case_1_possibilities.copy()
    all_skins.extend(case_2_possibilities)

    # add chances for case 1 skins
    for i in range(len(case_1_possibilities) - 1):
        chance_range.append(chance_range[-1] + best_count)

    # add chances for case 2 skins
    for i in range(len(case_2_possibilities)):
        chance_range.append(chance_range[-1] + (10 - best_count))

    # simulate 100 random trade ups
    for i in range(iterations):
        # get random value
        r = random.randint(1, total_tickets)

        # use r to find the selected possibility
        if r <= chance_range[0]:
            possibility = all_skins[0]
        else:
            # loop through price ranges to find best match
            for j in range(0, len(chance_range) - 1):
                # check range
                if chance_range[j] < r <= chance_range[j + 1]:
                    possibility = all_skins[j]
                    break
            else:
                possibility = all_skins[-1]

        # get the skin's predicted wear
        estimated_wear = estimate_wear(possibility, average_wear)

        # get the estimated wear as a valid value
        estimated_wear_value = get_valid_wears(0, estimated_wear, True)[-1].value

        # attempt to get price of the generated skin
        try:
            price = db_handler.get_prices(possibility.skin_id, estimated_wear_value, db)[0][0]
        except TypeError:
            # if we can't get the price, grab the cheapest one at it's rarity and crate
            possible_data = db_handler.get_cheapest_by_crate_rarity_and_wear(possibility.case_id, possibility.rarity,
                                                                             estimated_wear_value, db)

            # if that doesn't exist, set it to a price of 0
            if possible_data is None or len(possible_data) < 2:
                price = 0
            else:
                price = possible_data[1]

            # mark the price warning True since the results may be inaccurate.
            price_warning = True

        # get roi for this simulation
        roi = price / input_costs
        profit = (-1 * input_costs) + price

        # add to roi lists
        roi_100.append(roi)
        profit_100 += profit

        # add to roi 10 as well if this was one of the round 10 simulations
        if i < 10:
            roi_10.append(roi)
            profit_10 += profit

    # return average ROI values and profits
    return sum(roi_10) / len(roi_10), sum(roi_100) / len(roi_100), profit_10, profit_100, price_warning


def estimate_wear(skin: Skin | SimulationPossibility, average_wear: float):
    estimate = ((skin.max_wear - skin.min_wear) * average_wear) + skin.min_wear

    # ensure the estimated wear is not larger than the max
    if estimate > skin.max_wear:
        estimate = skin.max_wear

    return estimate


def generate_tradeup(*args):
    db = db_handler.connect_to_db(args[0])

    skins = args[1]

    # loop through skins
    for i in range(len(skins)):
        # get current skin from i
        goal_skin = skins[i]

        # loop through all valid wear ratings for current skin
        for goal_wear in get_valid_wears(goal_skin.min_wear, goal_skin.max_wear, True):
            # get a list of all the skins that can be used to trade up into the goal skin
            valid_skins = db_handler.get_skins_by_crate_and_rarity(goal_skin.crate_id, goal_skin.rarity - 1, db)

            # loop through valid skin trade ups to identify all possible combinations
            for skin_1 in valid_skins:
                max_profitable_wear = skin_1.max_wear

                # should the max_profitable_wear value be decremented?
                decrement_wear = False
                while max_profitable_wear > 0:
                    # ensure the max_profitable_wear isn't changed in the first run, but is in all subsequent runs
                    if decrement_wear:
                        max_profitable_wear = round(max_profitable_wear - 0.01, 2)
                    else:
                        decrement_wear = True

                    # get list of valid wears
                    max_wear = get_valid_wears(0, max_profitable_wear, True)

                    # determine absolute highest wear value so we can use it to search
                    if len(max_wear) > 0:
                        max_wear = max_wear[-1].value
                    else:
                        # no valid wear rating found, skip this check
                        break

                    # get the current skin_1's price
                    data = db_handler.get_prices(skin_1.internal_id, max_wear, db)

                    # data does not exist, we'll decrement and try again
                    if data is None:
                        continue

                    # set cheapest skin id/price variables from data
                    price = data[0][0]

                    # gather price data for the current goal skin
                    goal_price = db_handler.get_prices(goal_skin.internal_id, goal_wear.value, db)

                    # if price data doesn't exist for this goal, we can skip it
                    if goal_price is None:
                        continue

                    # account for the market tax on the resale value of this item
                    goal_price = goal_price[0][0] * 0.95

                    # assume that 10 of the cheapest skins is the best fit (gives a higher success chance)
                    skin_1_best = 10

                    # calculate highest possible price of cheapest_price first
                    # this will allow us to decrease later on to save money or lower wear ratings.
                    while skin_1_best > 0 and price * skin_1_best > goal_price:
                        skin_1_best -= 1

                    # we need to ensure that the filler skins later on can at least be 3 cents, so check that here
                    if (skin_1_best * price) + ((10 - skin_1_best) * 0.03) > goal_price:
                        skin_1_best -= 1

                    # check that skin_1_best is a valid combination
                    if skin_1_best <= 0:
                        continue

                    # now consider the max wear value of the filler skins
                    valid_wears = False

                    # set the defaults for the goal variables
                    goal_alternative = None
                    goal_average = 0

                    while skin_1_best > 0:
                        max_alternative_wear = 1

                        while max_alternative_wear > 0:

                            # get a rough average wear rating prediction
                            average = ((
                                               max_profitable_wear * skin_1_best)  # generate average for cheapest skin with max_profitable
                                       + ((10 - skin_1_best) * max_alternative_wear)
                                       # generate average for filler skins with max_alternative
                                       ) / 10

                            # get wear rating estimate
                            estimate = estimate_wear(goal_skin, average)

                            # check if this wear rating is too high
                            goal_alternative = get_valid_wears(0, estimate, True)[-1].value
                            if goal_alternative > goal_wear.value:
                                max_alternative_wear = round(max_alternative_wear - 0.01, 2)
                                continue
                            else:
                                # valid wear rating combination, break from this loop
                                valid_wears = True
                                goal_average = average
                                break

                        # found valid wears, we'll break from this loop too.
                        if valid_wears:
                            break

                        # if no valid wear was found, we'll decrement skin_1_best until one is
                        skin_1_best -= 1

                    # check to ensure skin_1_best is still valid
                    if skin_1_best <= 0:
                        continue

                    # since we now have the max possible wear rating that works with this trade up, we can move on to the
                    # next step: finding the best filler skin. we only need to do this if skin_1_best is < 10

                    if skin_1_best < 10:
                        # calculate the value remaining after our original skins
                        remaining_value = goal_price - (price * skin_1_best)

                        # calculate how many more skins we can use
                        remaining_count = 10 - skin_1_best

                        # call the filler skin algorithm to get our data
                        filler_skin_data = find_best_fit(goal_skin.crate_id, remaining_value, remaining_count,
                                                         get_valid_wears(0, max_alternative_wear, True)[-1].value, goal_skin.rarity - 1, db)

                        # no valid skin found! skip this combinations.
                        if filler_skin_data[0] is None:
                            continue

                        # set our filler skin id, crate, and price
                        filler_skin, filler_crate, filler_price = filler_skin_data
                    else:
                        # mark filler skin as empty so we can check it later
                        filler_skin = None
                        filler_price = 0

                    # the next step after filler skins is to run a basic simulation using the data we've collected.
                    # first though, we need the valid skins from the two crates.

                    # gather up all possible results from the goal skin's case
                    case_1_skins = db_handler.get_skins_by_crate_and_rarity(goal_skin.crate_id, goal_skin.rarity, db)

                    # loop through case_1_skins and turn them into case_1_possibility objects
                    case_1_possibilities = [SimulationPossibility(skin) for skin in case_1_skins]

                    # check if we are using a filler skin, and fill out case_2_possibilities
                    case_2_possibilities = []
                    if filler_skin is not None:
                        # gather case 2 skins
                        case_2_skins = db_handler.get_skins_by_crate_and_rarity(filler_crate, goal_skin.rarity, db)

                        # turn skins into possibility objects
                        case_2_possibilities = [SimulationPossibility(skin) for skin in case_2_skins]

                    # set input costs (how much each trade up will cost)
                    input_costs = price * skin_1_best

                    # if we're using a filler skin, add that to the input cost
                    if filler_skin is not None:
                        input_costs += filler_price * (10 - skin_1_best)

                    # generate the total number of "tickets" for this trade up
                    total_tickets = (len(case_1_possibilities) * skin_1_best) + (
                            len(case_2_possibilities) * (10 - skin_1_best))

                    # run simulation
                    sim_data = simulate(
                        input_costs,
                        case_1_possibilities,
                        case_2_possibilities,
                        total_tickets,
                        skin_1_best,
                        goal_average,
                        db
                    )

                    # extract data from the simulation for 10 and 100 simulations, as well as the price warning flag
                    roi_10, roi_100, profit_10, profit_100, price_warning = sim_data

                    # finally, add all this data into the DB

                    # get a list of the skin IDs used in this trade up
                    skin_ids = [skin_1.internal_id]

                    # add the filler skin if it was used
                    if filler_skin is not None:
                        skin_ids.append(filler_skin)

                    # calculate the chance of getting the goal skin (for use in trade up displays)
                    chance = skin_1_best / total_tickets

                    # actually add to DB
                    db_handler.add_tradeup(
                        skin_ids,
                        goal_skin.internal_id,
                        goal_wear.value,
                        goal_skin.rarity,
                        goal_skin.weapon_type,
                        skin_1_best,
                        chance,
                        roi_10,
                        roi_100,
                        profit_10,
                        profit_100,
                        price_warning,
                        price,
                        filler_price,
                        max_profitable_wear,
                        max_alternative_wear,
                        input_costs,
                        db=db
                    )

                    # exit this loop since we've found a working wear rating
                    break

        # commit trade ups to the DB
        db.commit()

    # close db connection
    db.close()
