import os
import pathlib
import discord
from src import db_handler, tradeup_generator
from discord import Colour
from src.models.skin import Skin
from src.models.simulation_possibility import SimulationPossibility
from src.models.weapon_classifiers import wear_int_to_enum, wear_int_enum_to_str_enum, WeaponIntToStr, WeaponToInt, \
    game_rarity_to_rarity, str_to_wear, rarity_int_to_game_rarity, get_valid_wears

rarity_to_color = {
    0: Colour.light_grey(),
    1: Colour.blue(),
    2: Colour.dark_blue(),
    3: Colour.purple(),
    4: Colour.nitro_pink(),
    5: Colour.red(),
    6: Colour.orange(),
}

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)

WORKING_PATH = pathlib.Path(os.curdir)


@bot.event
async def on_ready():
    print("Bot has connected to discord.")


async def autocomplete_skins(ctx: discord.AutocompleteContext):
    current_str = ctx.options['skin_name']
    current_weapon = ctx.options['weapon']

    if current_weapon is not None:
        skins = db_handler.get_skins_by_search_name(current_str.lower(), WeaponToInt[current_weapon])[:25]
    else:
        skins = db_handler.get_skins_by_search_name(current_str.lower())[:25]

    return skins


@bot.slash_command(description="List off trade offs with the specified criteria. Lists 10 results at a time.")
async def list_trade_ups(ctx: discord.ApplicationContext,
                         rarity: discord.Option(input_type=str,
                                                choices=["Industrial", "Mil-Spec", "Restricted", "Classified",
                                                         "Covert"],
                                                description="The result's skin rarity to sort by",
                                                required=False),
                         wear: discord.Option(input_type=str,
                                              choices=["Factory New", "Minimal Wear", "Field-Tested", "Well-Worn",
                                                       "Battle-Scarred"],
                                              description="The wear rating to sort by",
                                              required=False),
                         weapon: discord.Option(input_type=str,
                                                autocomplete=discord.utils.basic_autocomplete(WeaponIntToStr.values()),
                                                description="The result's weapon type to sort by",
                                                required=False),
                         skin_name: discord.Option(input_type=str,
                                                   autocomplete=discord.utils.basic_autocomplete(autocomplete_skins),
                                                   description="The resulting skin's name to sort by",
                                                   required=False),
                         min_wear: discord.Option(discord.SlashCommandOptionType.number,
                                                  description="The minimum wear rating that you're willing to use in a trade up",
                                                  required=False,
                                                  default=0.001,
                                                  max_value=1,
                                                  min_value=0.001),
                         max_wear: discord.Option(discord.SlashCommandOptionType.number,
                                                  description="The maximum wear rating that you're willing to use in a trade up",
                                                  required=False,
                                                  default=1,
                                                  max_value=1,
                                                  min_value=0.001),
                         lower_price: discord.Option(float, description="Lower price bound", required=False),
                         upper_price: discord.Option(float, description="Lower price bound", required=False),
                         roi_10_min: discord.Option(float, description="Lower ROI bound", required=False),
                         roi_10_max: discord.Option(float, description="Upper ROI bound", required=False),
                         max_margin: discord.Option(discord.SlashCommandOptionType.number,
                                                    description="The maximum distance away from the next lowest level a wear rating can be",
                                                    required=False, min_value=0, max_value=1, default=1),
                         offset: discord.Option(int,
                                                description="How many results to offset by. 1 offset = 10 results.",
                                                required=False, default=0),
                         sort_by=discord.Option(str, description="Category to sort results by", required=False,
                                                default="chance",
                                                choices=["chance", "roi_10", "profit", "input_price"])):
    if min_wear > max_wear:
        await ctx.send_response("Min wear cannot be greater than max wear.")
        return

    if lower_price is None:
        lower_price = 0

    if upper_price is None:
        upper_price = 9999999999

    if roi_10_min is None:
        roi_10_min = 0
    else:
        roi_10_min /= 100

    if roi_10_max is None:
        roi_10_max = 9999999999
    else:
        roi_10_max /= 100

    if rarity is not None:
        rarity = game_rarity_to_rarity[rarity.lower()].value

    if wear is not None:
        wear = str_to_wear[wear].value

    if weapon is not None:
        try:
            weapon = list(WeaponIntToStr.values()).index(weapon) + 1
        except ValueError:
            await ctx.send_response("Invalid weapon.")
            return

    if skin_name is not None:
        skin_name = db_handler.get_skins_by_search_name(skin_name.lower())[0]

    if sort_by == "profit":
        sort_by = "profit_10"

    tradeups, total_count = await db_handler.get_tradeups_by_criteria(rarity, wear, weapon, skin_name, min_wear,
                                                                      max_wear, lower_price, upper_price, roi_10_min,
                                                                      roi_10_max, max_margin, offset, sort_by)

    if tradeups is None:
        await ctx.send_response("Please add a filter.")
        return
    elif len(tradeups) == 0:
        await ctx.send_response("No trade ups matching that criteria were found.")
        return

    await ctx.send_response((await format_tradeups(
        tradeups)) + f"\n\n*Displaying {len(tradeups)} of {total_count} total results. Offset of {offset * 10} results.*")


async def format_tradeups(tradeups):
    desc = []

    for tradeup in tradeups:
        goal_skin_price = db_handler.get_prices(tradeup.goal_skin.internal_id, tradeup.goal_wear)

        input_price = (tradeup.skin_1_price * tradeup.skin_1_count) + (
                tradeup.skin_2_price * (10 - tradeup.skin_1_count))

        if goal_skin_price is not None:
            possible_profit = f"`${round((goal_skin_price[0][0] * 0.95) - input_price, 2):,.2f}`"
        else:
            possible_profit = "`N/A`"

        desc.append(
            f"- Trade Up {tradeup.internal_id}: `{wear_int_enum_to_str_enum[wear_int_to_enum[tradeup.goal_wear]]} {tradeup.goal_skin.skin_name}`; input price: `${round(input_price, 2):,.2f}`; chance of success: `{round(tradeup.chance * 100)}%`; potential profit: {possible_profit}; ROI 10: `{round(tradeup.roi_10 * 100, 2):,.2f}%`")

    return "\n".join(desc)


@bot.slash_command(description="Get details about a trade up")
async def get_trade_up(ctx: discord.ApplicationContext, tradeup_id: discord.Option(int)):
    try:
        tradeup = db_handler.get_tradeup_by_id(tradeup_id)
    except ValueError:
        await ctx.send_response("Trade up not found.")
        return

    goal_skin_price = db_handler.get_prices(tradeup.goal_skin.internal_id, tradeup.goal_wear)

    input_price = (tradeup.skin_1_price * tradeup.skin_1_count) + (tradeup.skin_2_price * (10 - tradeup.skin_1_count))

    if goal_skin_price is not None:
        possible_profit = f"`${round(goal_skin_price[0][0] - input_price, 2):,.2f}`"
    else:
        possible_profit = "No price on market"

    desc = f"Success Chance: `{round(tradeup.chance * 100, 2)}%`\nPossible Profit: {possible_profit}"

    embed = discord.Embed(
        title=f"{WeaponIntToStr[tradeup.goal_skin.weapon_type]} \"{tradeup.goal_skin.skin_name}\" ({wear_int_enum_to_str_enum[wear_int_to_enum[tradeup.goal_wear]]})",
        description=desc,
        colour=rarity_to_color[tradeup.goal_rarity]
    )

    embed.set_author(
        name=f"{rarity_int_to_game_rarity[tradeup.goal_rarity - 1]} to {rarity_int_to_game_rarity[tradeup.goal_rarity]}")

    embed.set_footer(text=f"Trade Up ID: {tradeup.internal_id}")

    inputs = f"- {tradeup.skin_1_count}x {WeaponIntToStr[tradeup.skin_1.weapon_type]} \"{tradeup.skin_1.skin_name}\"\n\t - Max Wear: `{tradeup.skin_1_max_wear}` - {get_valid_wears(0, tradeup.skin_1_max_wear)[-1].value}\n - Price: `${tradeup.skin_1_price:,.2f}` each\n - *Internal ID: `{tradeup.skin_1.internal_id}`*"

    if tradeup.skin_2 is not None:
        inputs += f"\n- {10 - tradeup.skin_1_count}x {WeaponIntToStr[tradeup.skin_2.weapon_type]} \"{tradeup.skin_2.skin_name}\"\n\t - Max Wear: `{tradeup.skin_2_max_wear}` - {get_valid_wears(0, tradeup.skin_2_max_wear)[-1].value}\n - Price: `${tradeup.skin_2_price:,.2f}` each\n - *Internal ID: `{tradeup.skin_2.internal_id}`*"

    embed.add_field(name=f"Inputs (`${input_price:,.2f}` total)", value=inputs, inline=False)

    sim_results = f"\n- 10:\n - ROI: `{(tradeup.roi_10 * 100):,.2f}%`\n - Profit: `${tradeup.profit_10:,.2f}`\n- 100:\n - ROI: `{(tradeup.roi_100 * 100):,.2f}%`\n - Profit: `${tradeup.profit_100:,.2f}`"

    embed.add_field(name="Simulation Results", value=sim_results, inline=False)

    await ctx.send_response(embed=embed)


@bot.slash_command(description="Simulate a trade up with a specified number of iterations")
async def simulate(ctx: discord.ApplicationContext, tradeup_id: discord.Option(int),
                   simulation_iterations: discord.Option(discord.SlashCommandOptionType.integer, min_value=1,
                                                         max_value=10000)):
    try:
        tradeup = db_handler.get_tradeup_by_id(tradeup_id)
    except ValueError:
        await ctx.send_response("Trade up not found.")
        return

    # gather case 1 skins
    case_1_skins = db_handler.get_skins_by_crate_and_rarity(tradeup.skin_1.crate_id, tradeup.skin_1.rarity)

    # loop through case_1_skins and turn them into case_1_possibility objects
    case_1_possibilities = [SimulationPossibility(skin) for skin in case_1_skins]

    case_2_possibilities = []

    if tradeup.skin_2 is not None:
        # gather case 2 skins
        case_2_skins = db_handler.get_skins_by_crate_and_rarity(tradeup.skin_2.crate_id, tradeup.skin_2.rarity)

        # turn skins into possibility objects
        case_2_possibilities = [SimulationPossibility(skin) for skin in case_2_skins]

    # generate the total number of "tickets" for this trade up
    total_tickets = (len(case_1_possibilities) * tradeup.skin_1_count) + (
            len(case_2_possibilities) * (10 - tradeup.skin_1_count))

    # calculate average wear
    average = ((tradeup.skin_1_max_wear * tradeup.skin_1_count) + (
            (10 - tradeup.skin_1_count) * tradeup.skin_2_max_wear)) / 10

    message = await ctx.send_response("Simulating...")

    data = tradeup_generator.simulate(
        input_costs=tradeup.input_price,
        case_1_possibilities=case_1_possibilities,
        case_2_possibilities=case_2_possibilities,
        total_tickets=total_tickets,
        best_count=tradeup.skin_1_count,
        average_wear=average,
        db=db_handler.WORKING_DB,
        iterations=simulation_iterations
    )

    desc = f"Trade Up ID: `{tradeup_id}`\nInput Price: `${tradeup.input_price:,.2f}`\n\nNumber of Iterations: `{simulation_iterations:,}`\n\nROI: `{round((data[1] * 100), 2):,.2f}%`\nProfit: `${round(data[3], 2):,.2f}`"

    embed = discord.Embed(
        title="Simulation Results",
        description=desc
    )

    if data[-1]:
        embed.set_footer(text="Warning: a skin with an unknown price was used in this simulation.")

    await message.edit(embed=embed, content="")


@bot.slash_command(description="Get a breakdown of the profits & losses that could result from a trade up")
async def profit_breakdown(ctx: discord.ApplicationContext, tradeup_id: discord.Option(int)):
    try:
        tradeup = db_handler.get_tradeup_by_id(tradeup_id)
    except ValueError:
        await ctx.send_response("Trade up not found.")
        return

    case_1 = db_handler.get_skins_by_crate_and_rarity(tradeup.skin_1.crate_id, tradeup.goal_rarity)

    case_2 = []
    if tradeup.skin_2 is not None:
        case_2 = db_handler.get_skins_by_crate_and_rarity(tradeup.skin_2.crate_id, tradeup.goal_rarity)

    # get total tickets
    total_tickets = (len(case_1) * tradeup.skin_1_count) + (len(case_2) * (10 - tradeup.skin_1_count))

    # get average wear
    average = ((tradeup.skin_1_max_wear * tradeup.skin_1_count) + (
            (10 - tradeup.skin_1_count) * tradeup.skin_2_max_wear)) / 10

    case_1_obj = db_handler.get_crate_from_internal(tradeup.skin_1.crate_id)

    desc = f"Goal: {WeaponIntToStr[tradeup.goal_skin.weapon_type]} \"{tradeup.goal_skin.skin_name}\" ({wear_int_enum_to_str_enum[wear_int_to_enum[tradeup.goal_wear]]})\n\n{case_1_obj.crate_name} (`{case_1_obj.internal_id}`):"

    case_1_chance = (tradeup.skin_1_count / total_tickets) * 100

    profit = 0

    for skin in case_1:
        skin_desc, has_profit = await format_skin_profit(skin, average, tradeup.input_price, case_1_chance)

        desc += skin_desc

        if has_profit:
            profit += case_1_chance

    if tradeup.skin_2 is not None:
        case_2_obj = db_handler.get_crate_from_internal(tradeup.skin_2.crate_id)

        desc += f"\n\n{case_2_obj.crate_name} (`{case_2_obj.internal_id}`):"

        case_2_chance = ((10 - tradeup.skin_1_count) / total_tickets) * 100

        for skin in case_2:
            skin_desc, has_profit = await format_skin_profit(skin, average, tradeup.input_price, case_2_chance)

            desc += skin_desc

            if has_profit:
                profit += case_2_chance

    desc += f"\n\nChance for profit: `{profit:,.2f}%`\nChance for loss: `{(100 - profit):,.2f}%`"

    # create embed
    embed = discord.Embed(
        title=f"Profit Breakdown For Trade Up {tradeup_id}",
        description=desc,
        colour=rarity_to_color[tradeup.goal_rarity]
    )

    # send embed
    await ctx.send_response(embed=embed)


async def format_skin_profit(skin: Skin, average: float, input_price: float, chance: float):
    # get estimated wear for this skin
    estimate = tradeup_generator.estimate_wear(skin, average)

    # get skin wear as a string
    skin_wear = get_valid_wears(skin.min_wear, estimate)[-1]

    # add skin to description
    desc = f"\n- {WeaponIntToStr[skin.weapon_type]} \"{skin.skin_name}\" ({skin_wear})"

    # get skin prices
    prices = db_handler.get_prices(skin.internal_id, str_to_wear[skin_wear].value)

    # set price data
    if prices is not None:
        price = float(prices[0][0]) * 0.95
        profit = price - input_price
        desc += f"\n - Skin price: `${price:,.2f}`"
        desc += f"\n - Profit: `${profit:,.2f}`"
    else:
        profit = 0
        desc += f"\n - Skin price: N/A"
        desc += f"\n - Profit: N/A"

    # set skin chance
    desc += f"\n - Chance: `{chance:,.2f}%`"
    desc += f"\n - *Internal ID: `{skin.internal_id}`*"

    # if we have profit, return the chance
    if profit > 0:
        has_profit = True
    else:
        has_profit = False

    # return skin description
    return desc, has_profit


@bot.slash_command(description="Get information about a skin")
async def get_skin(ctx: discord.ApplicationContext, skin_id: discord.Option(int)):
    skin = db_handler.get_skin_by_id(skin_id)

    if skin is None:
        await ctx.send_response("Skin could not be found.")
        return

    desc = f"Skin Name: `{skin.skin_name}`\nRarity: `{rarity_int_to_game_rarity[skin.rarity]}`\n\nSkin ID: `{skin.skin_id}`\nSkin Tag: `{skin.skin_tag}`\n\nMin Wear: `{skin.min_wear}`\nMax Wear: `{skin.max_wear}`\nPossible Wear Ratings:"

    for rating in get_valid_wears(skin.min_wear, skin.max_wear):
        prices = db_handler.get_prices(skin.internal_id, str_to_wear[rating].value)

        if prices is None:
            price = "N/A"
        else:
            price = f"${prices[0][0]:,.2f}"

        desc += f"\n- {rating} (`{price}`)"

    case = db_handler.get_crate_from_internal(skin.crate_id)
    desc += f"\n\nCase: `{case.crate_name}` (`{case.internal_id}`)"

    embed = discord.Embed(
        title=f"{WeaponIntToStr[skin.weapon_type]} \"{skin.skin_name}\"",
        description=desc,
        colour=rarity_to_color[skin.rarity]
    )

    embed.set_footer(text=f"Internal ID: {skin.internal_id}")

    await ctx.send_response(embed=embed)


@bot.slash_command(description="Get information about a case")
async def get_case(ctx: discord.ApplicationContext, case_id: discord.Option(int)):
    case = db_handler.get_crate_from_internal(case_id)

    if case is None:
        await ctx.send_response("Case could not be found.")
        return

    desc = f"Case ID: `{case.crate_id}`\nSet ID: `{case.set_id}`\nLoot List ID: `{case.loot_table_id}`\n\nSkins:"

    for rarity in range(0, 6):
        if case.rarity_counts[rarity] > 0:
            desc += f"\n- {rarity_int_to_game_rarity[rarity]} ({case.rarity_counts[rarity]} skin"

            if case.rarity_counts[rarity] > 1:
                desc += "s"

            desc += ")"

            for skin in db_handler.get_skins_by_crate_and_rarity(case.internal_id, rarity):
                desc += f"\n - {WeaponIntToStr[skin.weapon_type]} \"{skin.skin_name}\" (`{skin.internal_id}`)"

    embed = discord.Embed(
        title=case.crate_name,
        description=desc
    )

    embed.set_footer(text=f"Internal ID: {case.internal_id}")

    await ctx.send_response(embed=embed)


def main():
    # get database creds
    if os.path.exists(os.path.join(WORKING_PATH.absolute(), "data/.db-creds")):
        with open(os.path.join(WORKING_PATH.absolute(), "data/.db-creds"), "r") as f:
            db_creds = tuple(f.readlines())
            f.close()
    else:
        db_creds = ("", "", "", "", "")

    # establish connection to database
    print("Establishing connection to database...")
    db_handler.establish_db(db_creds)

    # start the bot
    if os.path.exists(os.path.join(WORKING_PATH.absolute(), "data/.bot-creds")):
        print("Starting bot...")
        with open(os.path.join(WORKING_PATH.absolute(), "data/.bot-creds"), "r") as f:
            token = f.read()
            f.close()

    # run the bot
    bot.run(token)


if __name__ == "__main__":
    main()