import random
import discord
import db_handler
from discord import Colour
from models.weapon_classifiers import wear_int_to_enum, wear_int_enum_to_str_enum, WeaponIntToStr, WeaponToInt, \
    game_rarity_to_rarity, str_to_wear, rarity_int_to_game_rarity

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


@bot.slash_command(description="List off trade offs with the specified criteria. Lists 20 results at a time.")
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
                         offset: discord.Option(int, description="How many results to offset by.", required=False, default=0)):

    if min_wear > max_wear:
        await ctx.send_response("Min wear cannot be greater than max wear.")
        return

    if lower_price is None:
        lower_price = 0

    if upper_price is None:
        upper_price = 9999999999

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

    tradeups, total_count = await db_handler.get_tradeups_by_criteria(rarity, wear, weapon, skin_name, min_wear, max_wear, lower_price, upper_price, offset)

    if tradeups is None:
        await ctx.send_response("Please add a filter.")
        return
    elif len(tradeups) == 0:
        await ctx.send_response("No trade ups matching that criteria were found.")
        return

    await ctx.send_response((await format_tradeups(tradeups)) + f"\n\n*Displaying {len(tradeups)} of {total_count} total results*")


async def format_tradeups(tradeups):
    desc = []

    for tradeup in tradeups:
        goal_skin_price = db_handler.get_prices(tradeup.goal_skin.internal_id, tradeup.goal_wear)

        input_price = (tradeup.skin_1_price * tradeup.skin_1_count) + (
                tradeup.skin_2_price * (10 - tradeup.skin_1_count))

        if goal_skin_price is not None:
            possible_profit = f"`${round(goal_skin_price[0][0] - input_price, 2):,.2f}`"
        else:
            possible_profit = "`N/A`"

        desc.append(
            f"Trade Up {tradeup.internal_id}: `{wear_int_enum_to_str_enum[wear_int_to_enum[tradeup.goal_wear]]} {tradeup.goal_skin.skin_name}`; input price: `${round(input_price, 2):,.2f}`; chance of success: `{round(tradeup.chance * 100)}%`; potential profit: {possible_profit}; roi 10: `{round(tradeup.roi_10 * 100, 2):,.2f}`")

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

    inputs = f"- {tradeup.skin_1_count}x {WeaponIntToStr[tradeup.skin_1.weapon_type]} \"{tradeup.skin_1.skin_name}\"\n\t - Max Wear: `{tradeup.skin_1_max_wear}`\n - Price: `${round(tradeup.skin_1_price, 2):,.2f}` each"

    if tradeup.skin_2 is not None:
        inputs += f"\n- {10 - tradeup.skin_1_count}x {WeaponIntToStr[tradeup.skin_2.weapon_type]} \"{tradeup.skin_2.skin_name}\"\n\t - Max Wear: `{tradeup.skin_2_max_wear}`\n - Price: `${round(tradeup.skin_2_price, 2):,.2f}` each"

    embed.add_field(name=f"Inputs (${round(input_price, 2):,.2f} total)", value=inputs, inline=False)

    sim_results = f"\n10:\n- ROI: `{round(tradeup.roi_10 * 100, 2):,.2f}%`\n- Profit: `${round(tradeup.profit_10, 2):,.2f}`\n100:\n- ROI: `{round(tradeup.roi_100 * 100, 2):,.2f}%`\n- Profit: `${round(tradeup.profit_100, 2):,.2f}`"

    embed.add_field(name="Simulation Results", value=sim_results, inline=False)

    await ctx.send_response(embed=embed)


@bot.slash_command(description="Simulate a trade up with a specified number of iterations")
async def simulate(ctx: discord.ApplicationContext, tradeup_id: int, simulation_iterations: int):
    await ctx.send_response("Simulation command is being rewritten.")
    return

    try:
        tradeup = db_handler.get_tradeup_by_id(tradeup_id)
    except ValueError:
        await ctx.send_response("Trade up not found.")
        return

    if simulation_iterations > 10000:
        await ctx.send_response("The max iterations is 10,000.")
        return

    roi = []
    profit = 0

    case_1_items, case_1_prices = db_handler.get_skin_prices_by_crate_rarity_and_wear(tradeup.skin_1.crate_id,
                                                                                      tradeup.goal_skin.rarity,
                                                                                      tradeup.goal_wear)

    if tradeup.skin_2 is not None:
        case_2_items, case_2_prices = db_handler.get_skin_prices_by_crate_rarity_and_wear(tradeup.skin_2.crate_id,
                                                                                          tradeup.goal_skin.rarity,
                                                                                          tradeup.goal_wear)
    else:
        case_2_items, case_2_prices = [], []

    # copy all values into a new array
    all_prices = case_1_prices.copy()
    all_prices.extend(case_2_prices)

    chance_range = [tradeup.skin_1_count]

    # add chance for case 1 items
    for i in range(len(case_1_prices) - 1):
        chance_range.append(chance_range[-1] + tradeup.skin_1_count)

    # add chance for case 2 items
    for i in range(len(case_2_prices)):
        chance_range.append(chance_range[-1] + (10 - tradeup.skin_1_count))

    total_tickets = (len(case_1_items) * tradeup.skin_1_count) + (len(case_2_items) * (10 - tradeup.skin_1_count))
    input_costs = tradeup.skin_1_price + tradeup.skin_2_price

    # simulate 100 random trade ups
    for i in range(simulation_iterations):
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
        r = price / input_costs
        p = (-1 * input_costs) + price

        # add to roi lists
        roi.append(r)
        profit += p

    roi_average = sum(roi) / len(roi)

    desc = f"Trade Up ID: `{tradeup_id}`\n\nNumber of Iterations: `{simulation_iterations}`\n\nROI: `{round(roi_average, 2):,.2f}%`\nProfit: `${round(profit, 2):,.2f}`"

    embed = discord.Embed(
        title="Simulation Results",
        description=desc
    )

    await ctx.send_response(embed=embed)


def start_bot(token: str):
    bot.run(token)
