"""
Monopoly Player Class and Strategy Functions
"""
from random import choice
from dataclasses import dataclass, field
from board_setup import STEADY_STATE_PROBS, PROP_BY_POS, COLOR_GROUPS, HOUSE_COSTS, AVG_PROB, RAILROADS, UTILITIES


@dataclass(eq=False)
class Player:
    name: str
    strategy: str
    cash: int = 1500
    position: int = 0
    in_jail: bool = False
    jail_turns: int = 0           # counts failed (non-doubles) rolls while in jail
    doubles_streak: int = 0
    properties_owned: list = field(default_factory=list)
    railroads_owned: list = field(default_factory=list)
    utilities_owned: list = field(default_factory=list)
    houses: dict = field(default_factory=dict)  # pos -> house count (5 = hotel)
    get_out_of_jail_cards: int = 0
    bankrupt: bool = False
    net_worth_history: list = field(default_factory=list)

    def net_worth(self):
        worth = self.cash
        for pos in self.properties_owned:
            color, _, price, _ = PROP_BY_POS[pos]
            worth += price // 2
            h = self.houses.get(pos, 0)
            worth += h * (HOUSE_COSTS[color] // 2)
        worth += len(self.railroads_owned) * 100
        worth += len(self.utilities_owned) * 75
        return worth

    def owns_color_set(self, color):
        return all(p in self.properties_owned for p in COLOR_GROUPS[color])

    def total_houses(self):
        """Count of houses (not hotels) across all properties."""
        return sum(min(h, 4) for h in self.houses.values())

    def total_hotels(self):
        """Count of hotels (house_count == 5) across all properties."""
        return sum(1 for h in self.houses.values() if h >= 5)


# ─────────────────────────────────────────────
# STRATEGY FUNCTIONS
# ─────────────────────────────────────────────

def strategy_greedy(player: Player, pos: int, price: int, game=None) -> bool:
    """Buy everything you can afford (keep $100 buffer)."""
    return player.cash - price >= 100


def strategy_color_hunter(player: Player, pos: int, price: int, game=None) -> bool:
    """Buy if already own part of the color group, otherwise defer to greedy strategy."""
    if pos in PROP_BY_POS:
        color = PROP_BY_POS[pos][0]
        owned_in_group = sum(1 for p in COLOR_GROUPS[color] if p in player.properties_owned)
        if owned_in_group > 0 and player.cash  >= price:
            return True
    return player.cash - price >= 100

def strategy_roi(player: Player, pos: int, price: int, game=None) -> bool:
    """Buy if the markov-weighted ROI looks favorable compared to a board-average benchmark, with some heuristics for cash buffer."""
    if player.cash > 600:
        return player.cash - price >= 100
    if player.cash - price < 200:
        return False
    if pos in PROP_BY_POS:
        _, _, _, rents = PROP_BY_POS[pos]
        # markov-weighted ROI: pi * hotel_rent / (price + 5 houses)
        score = STEADY_STATE_PROBS[pos] * rents[5] / (price + 5 * HOUSE_COSTS[PROP_BY_POS[pos][0]])
        # rough board-average benchmark
        bench = AVG_PROB * 1000 / (260 + 5 * HOUSE_COSTS[PROP_BY_POS[pos][0]])
        return score > bench
    elif pos in RAILROADS or pos in UTILITIES:
        return STEADY_STATE_PROBS[pos] > AVG_PROB
    return False

def strategy_cash_aware(player: Player, pos: int, price: int, game=None) -> bool:
    """Cash-aware strategy that inspects the live game state (ownership/houses).
    - Compute the actual worst-case rent over the next 12 squares from the
      current `game.ownership` and owners' `houses`, `railroads_owned`,
      `utilities_owned` and require remaining cash >= that rent.
    """
    max_rent = 0
    for step in range(1, 13):
        p = (player.position + step) % 40
        # railroads
        if p in RAILROADS:
            if p in game.ownership:
                owner_idx = game.ownership[p]
                owner = game.players[owner_idx]
                rr_count = len(owner.railroads_owned)
                rent = [0, 25, 50, 100, 200][rr_count]
                max_rent = max(max_rent, rent)
            continue
        # utilities
        if p in UTILITIES:
            if p in game.ownership:
                owner_idx = game.ownership[p]
                owner = game.players[owner_idx]
                util_count = len(owner.utilities_owned)
                multiplier = 10 if util_count == 2 else 4
                rent = 12 * multiplier
                max_rent = max(max_rent, rent)
            continue
        # properties
        if p in PROP_BY_POS and p in game.ownership:
            rents = PROP_BY_POS[p][3]
            owner_idx = game.ownership[p]
            owner = game.players[owner_idx]
            hcount = owner.houses.get(p, 0)
            if hcount == 0 and owner.owns_color_set(PROP_BY_POS[p][0]):
                rent = rents[0] * 2
            else:
                rent = rents[min(hcount, 5)]
            max_rent = max(max_rent, rent)

    return (player.cash - price) >= max_rent


def strategy_random(player: Player, pos: int, price: int, game=None) -> bool:
    """Buy randomly if you can afford with a $100 buffer."""
    return player.cash - price >= 100 and choice([True, False])

STRATEGIES = {
    "Greedy":         strategy_greedy,
    "Color Hunter":   strategy_color_hunter,
    "ROI-Based":      strategy_roi,
    "Cash Aware":     strategy_cash_aware,
    "Random":         strategy_random,
}