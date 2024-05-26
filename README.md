# Counter Strike Trade Up Analyzer

An algorithm that uses the Steam Community Market to gather price data and then analyze them to find the most profitable possible combinations for trade ups.

---

## Requirements
- postgreqSQL server
- Python 3.11
- pip
- Local installation of *Counter-Strike 2*

---

## Discord Bot Integration
Discord bot integration allows for seamless connectivity into your servers. Through the in-depth and extensive controls, users can easily find profitable trade ups. The following is a list of some of the more notable commands, and their uses:

 - Trade up listing
    - Lists out trade ups using over 10 customizable criteria fields
 - Profit Breakdowns
   - Get an in-depth look into the potential outcomes of a trade up
 - Simulation
   - Simulate a trade up for a customizable period of openings, and get an idea of how the return on investment and potential profit is affected.


---

### How Trade Ups Work
Before getting into the meat of this algorithm, it's important to know a few things about *Counter-Strike 2* trade ups: specifically what they are and how they work.  A "trade up" uses 10 skins of the same rarity to randomly create a skin of the next rarity. There are a couple of key components of a trade up that give it a predictable nature, which is exploited in this algorithm.

The first feature is that of success chance. The more skins you add from different crate or collection, the more possible outcomes. In order to deal with this, `Counter-Strike 2` uses a weight system in trade ups. This can be expressed as the following equation:

$$\text{Total Tickets} = (\text{Skin 1 Count * Skin 1 Case Possibilities}) + (\text{Skin 2 Count * Skin 2 Case Possibilities})$$

In order to get a better understanding of this formula, consider the following scenario, in which two skins are being used in a trade up. Skin 1 is being used 3 times in the trade up, and can result in 2 skins. Skin 2 is being used 7 times in the trade up, and can result in 4 skins. The formula would look like the following:

$$\text{Total Tickets} = (3 * 2) + (7 * 4)$$

In this instance, `Total Tickets` would be equal to `34`. Now say we wanted to calculate the chance of getting a specific skin out of the trade up. In order to do so, we'd divide the total tickets by the number of that skin we put in. Referencing the earlier example, say we want to figure out the chance of getting Skin A from Skin 1's case. The formula would appear as the following:

$$\text{Chance} = 3 / 34$$

Our chance to get Skin A from this trade up would then be `0.0882`, or about `9%`. With this concept in mind, we can move on to the next and equally important feature of trade up prediction.

When dealing with predicting the resulting skin's wear rating, we need to take into account the wear rating of all input skins, and some information from the resulting skin as well. This means that there will *not* be a set wear rating outcome for all skins involved in a trade up process, and two skins from the same crate may end up with differing results.

Luckily, the algorithm for this is pretty straight forward and the data is easily gather-able. The formula is as follows:

$$\text{Estimated Wear} = ((\text{Goal Max Wear - Goal Min Wear}) * \text{Average Input Wears}) + \text{Goal Min Wear}$$

It's important to note that `Average Input Wears` is the average of all the inputted skin's wear values, and the "goal" wears are the maximum and minimum wears for the target skin in a trade up. This formula is both good and bad, meaning that skins with outlying high wear values may negatively impact the resulting skin's wear rating, but also that a static and predictable skin rating can serve as an upper bound for prediction.

With these concepts of `Counter-Strike 2` skin trade ups in mind, the algorithm described below should hopefully make decent sense.

---

## How The Algorithm Works
There are numerous steps to the trade up generation process. They can be broken down into a few notable groupings: *Game Item Collection*, *Market Price Collection*, and *Trade Up Generation*. Each of these steps is detailed further below.

### Game Item Collection
In order to analyze the large number of skins (over 1,150) present in Counter Strike 2 in a dynamic and efficient way, they're first gathered from game files. This method uses an extracted version of the `items_game.txt` and `csgo_english.txt` files present in the game's compiled form. 

These files are then crawled using a custom-built crawler, transforming their data into a readable JSON format. This format is quick and easy to read in Python, and allows for better debugging as well.

After the files have been converted to JSON, another parser looks through the `items_game.txt`file to identify crates. Each of these have items that players can use in a trade up, and are therefore important to the generational aspect of this algorithm.

Once crates and collections have been gathered, the skin data for each available skin in the game is added to the database. This is all information used later during trade up generation.

### Market Price Collection
By utilizing the open-ended Steam URLs available to the average user, Steam can be systematically scraped for data relating to skins. Though a bit of a time-consuming and tedious process, this is a critical part in trade up generation. Price information allows the algorithm to identify the cheapest item from a set, cutting generation time to fractional amounts.

To gather information on a skin, there are three steps:
 - First, a "hash" name is generated for a skin. This typically includes simple information, such as what weapon the skin belongs to, the name of the skin, and it's wear rating. For example, a SSG-08 Dragonfire Factory New would be formatted as `SSG-08 Dragonfire | Factory New`
 - Second, the hash name is used in conjunction with [this](https://steamcommunity.com/market/listings/730/) base URL, allowing the script to fetch the market ID of the skins.
 - Third and finally, the market ID is used with [this](https://steamcommunity.com/market/itemordershistogram?country=US&language=english&currency=1&item_nameid=) URL to gather the list of current buy and sell orders for a skin.

Once gathered, the information is then systematically parsed by crate. The cheapest skin in any tier of rarity for a crate is identified and recorded, allowing for future use in the trade up generation step.

## Trade Up Generation
The final and second-most complex step is the generation of valid trade ups. Due to the nature of the algorithm, a large chunk of this process is trial-and-error brute forcing. To understand how this section works though, a deeper understanding of trade ups is required.

In any given instance, a trade up consists of 10 skins of the same rarity. In the worst case scenario, that means 372 skins (from the Mil-Spec rarity) to potentially combine. Now by addressing each individual trade up, this process would take 372<sup>10</sup> comparisons. That's a lot of time.

However, by using a few clever tricks, the process can be sped up significantly. In particular, only ever using 2 skins in a trade up, increasing the chance of success. In addition, only the cheapest skin of a crate's rarity tier needs to be analyzed, as all skins above that price will have no further effect other than an increased base price. This significantly reduces the total number of comparisons to a much more manageable 372<sup> 2</sip> 

In order to put these ideas into effect, the trade up generator starts at the highest possible wear for a target skin, slowly decreasing until it reaches a point where the resulting skin (using the expected wear formula) is profitable. It then attempts to combine the trade up with filler skins, prioritizing the cheapest price and highest chance of success.

Due to the basic nature of this process still being brute force, it can take a considerable amount of time. One employed method to reduce this time is by using threading, and by default the work load of the program is split over 64 threads, significantly reducing the processing time.