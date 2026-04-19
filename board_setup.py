"""
Monopoly Board Setup
Constants and data structures for the Monopoly board.
"""

from collections import defaultdict
import random

# Long-term steady-state probabilities from your Markov chain analysis.
# Index = board position (0-39). Replace with your actual computed values.
STEADY_STATE_PROBS = [
    0.0311, 0.0176, 0.0179, 0.0162, 0.0199,  # 0-4
    0.0283, 0.0162, 0.0141, 0.0162, 0.0196,  # 5-9
    0.0323, 0.0241, 0.0205, 0.0241, 0.0162,  # 10-14
    0.0285, 0.0188, 0.0141, 0.0210, 0.0194,  # 15-19
    0.0228, 0.0181, 0.0222, 0.0281, 0.0180,  # 20-24
    0.0289, 0.0162, 0.0141, 0.0203, 0.0220,  # 25-29
    0.0588, 0.0218, 0.0223, 0.0218, 0.0162,  # 30-34
    0.0289, 0.0162, 0.0141, 0.0203, 0.0209,  # 35-39
]

# House/hotel cost per build, by color group (same cost for houses and hotels)
HOUSE_COSTS = {
    "purple":    50,
    "light_blue":50,
    "pink":     100,
    "orange":   100,
    "red":      150,
    "yellow":   150,
    "green":    200,
    "dark_blue":200,
}

# Property data: (color_group, position, name, price, rents[base,1H,2H,3H,4H,hotel])
PROPERTIES = [
    ("purple",    1,  "Mediterranean Ave",  60,  [2,  10,  30,  90, 160, 250]),
    ("purple",    3,  "Baltic Ave",         60,  [4,  20,  60, 180, 320, 450]),
    ("light_blue",6,  "Oriental Ave",      100,  [6,  30,  90, 270, 400, 550]),
    ("light_blue",8,  "Vermont Ave",       100,  [6,  30,  90, 270, 400, 550]),
    ("light_blue",9,  "Connecticut Ave",   120,  [8,  40, 100, 300, 450, 600]),
    ("pink",     11,  "St. Charles Place", 140,  [10, 50, 150, 450, 625, 750]),
    ("pink",     13,  "States Ave",        140,  [10, 50, 150, 450, 625, 750]),
    ("pink",     14,  "Virginia Ave",      160,  [12, 60, 180, 500, 700, 900]),
    ("orange",   16,  "St. James Place",   180,  [14, 70, 200, 550, 750, 950]),
    ("orange",   18,  "Tennessee Ave",     180,  [14, 70, 200, 550, 750, 950]),
    ("orange",   19,  "New York Ave",      200,  [16, 80, 220, 600, 800,1000]),
    ("red",      21,  "Kentucky Ave",      220,  [18, 90, 250, 700, 875,1050]),
    ("red",      23,  "Indiana Ave",       220,  [18, 90, 250, 700, 875,1050]),
    ("red",      24,  "Illinois Ave",      240,  [20,100, 300, 750, 925,1100]),
    ("yellow",   26,  "Atlantic Ave",      260,  [22,110, 330, 800, 975,1150]),
    ("yellow",   27,  "Ventnor Ave",       260,  [22,110, 330, 800, 975,1150]),
    ("yellow",   29,  "Marvin Gardens",    280,  [24,120, 360, 850,1025,1200]),
    ("green",    31,  "Pacific Ave",       300,  [26,130, 390, 900,1100,1275]),
    ("green",    32,  "North Carolina Ave",300,  [26,130, 390, 900,1100,1275]),
    ("green",    34,  "Pennsylvania Ave",  320,  [28,150, 450,1000,1200,1400]),
    ("dark_blue",37,  "Park Place",        350,  [35,175, 500,1100,1300,1500]),
    ("dark_blue",39,  "Boardwalk",         400,  [50,200, 600,1400,1700,2000]),
]

RAILROADS = [5, 15, 25, 35]  # $200 each; rent: 1=$25, 2=$50, 3=$100, 4=$200
UTILITIES  = [12, 28]         # $150 each; rent: 1 owned=4x dice, 2 owned=10x dice

COLOR_GROUPS = defaultdict(list)
for color, pos, *_ in PROPERTIES:
    COLOR_GROUPS[color].append(pos)

PROP_BY_POS = {pos: (color, name, price, rents)
               for color, pos, name, price, rents in PROPERTIES}

SPECIAL_SQUARES = {
    0:  "GO",
    2:  "COMMUNITY_CHEST",
    4:  "INCOME_TAX",
    7:  "CHANCE",
    10: "JAIL",
    17: "COMMUNITY_CHEST",
    20: "FREE_PARKING",
    22: "CHANCE",
    30: "GO_TO_JAIL",
    33: "COMMUNITY_CHEST",
    36: "CHANCE",
    38: "LUXURY_TAX",
}


# ─────────────────────────────────────────────
# CARD DECKS — US Standard Edition (Sept. 2008 "Atlantic City Edition")
# ─────────────────────────────────────────────

CHANCE_CARDS = [
    "advance_boardwalk",          # 1.  Advance to Boardwalk
    "advance_go",                 # 2.  Advance to Go (collect $200)
    "advance_illinois",           # 3.  Advance to Illinois Ave
    "advance_stcharles",          # 4.  Advance to St. Charles Place
    "advance_nearest_railroad",   # 5.  Advance to nearest Railroad (2x rent) [copy 1]
    "advance_nearest_railroad",   # 6.  Advance to nearest Railroad (2x rent) [copy 2]
    "advance_nearest_utility",    # 7.  Advance to nearest Utility (10x dice if owned)
    "bank_dividend_50",           # 8.  Bank pays dividend of $50
    "get_out_of_jail_free",       # 9.  Get Out of Jail Free
    "go_back_3",                  # 10. Go Back 3 Spaces
    "go_to_jail",                 # 11. Go to Jail
    "chance_repairs",             # 12. General repairs: $25/house, $100/hotel
    "speeding_fine_15",           # 13. Speeding fine $15
    "advance_reading_railroad",   # 14. Take a trip to Reading Railroad
    "chairman_of_board",          # 15. Chairman of the Board — pay each player $50
    "building_loan_150",          # 16. Building loan matures — collect $150
]

COMMUNITY_CHEST_CARDS = [
    "advance_go",                 # 1.  Advance to Go (collect $200)
    "bank_error_200",             # 2.  Bank error in your favor — collect $200
    "doctors_fee_50",             # 3.  Doctor's fee — pay $50
    "stock_sale_50",              # 4.  From sale of stock — collect $50
    "get_out_of_jail_free",       # 5.  Get Out of Jail Free
    "go_to_jail",                 # 6.  Go to Jail
    "holiday_fund_100",           # 7.  Holiday fund matures — collect $100
    "income_tax_refund_20",       # 8.  Income tax refund — collect $20
    "birthday_10",                # 9.  It is your birthday — collect $10 from every player
    "life_insurance_100",         # 10. Life insurance matures — collect $100
    "hospital_fees_100",          # 11. Pay hospital fees — $100
    "school_fees_50",             # 12. Pay school fees — $50
    "consultancy_fee_25",         # 13. Receive $25 consultancy fee
    "community_repairs",          # 14. Street repairs: $40/house, $115/hotel
    "beauty_contest_10",          # 15. Second prize in beauty contest — collect $10
    "inherit_100",                # 16. You inherit $100
]


def shuffle_decks():
    chance = CHANCE_CARDS[:]
    community = COMMUNITY_CHEST_CARDS[:]
    random.shuffle(chance)
    random.shuffle(community)
    return chance, community