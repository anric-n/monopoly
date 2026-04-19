"""
Monopoly Player Class and Strategy Functions
"""

from dataclasses import dataclass, field
from board_setup import STEADY_STATE_PROBS, PROP_BY_POS, COLOR_GROUPS, HOUSE_COSTS


@dataclass
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

def strategy_greedy(player: Player, pos: int, price: int) -> bool:
    """Buy everything you can afford (keep $100 buffer)."""
    return player.cash - price >= 100


def strategy_color_hunter(player: Player, pos: int, price: int) -> bool:
    """Buy if already own part of the color group, or have >$600 to speculate."""
    if player.cash - price < 150:
        return False
    if pos in PROP_BY_POS:
        color = PROP_BY_POS[pos][0]
        owned_in_group = sum(1 for p in COLOR_GROUPS[color] if p in player.properties_owned)
        if owned_in_group > 0:
            return True
        if player.cash > 600:
            return True
    return False


def strategy_roi(player: Player, pos: int, price: int) -> bool:
    """Buy only if base_rent/price > 3% ROI threshold. Railroads/utilities always pass."""
    ROI_THRESHOLD = 0.03
    if player.cash - price < 200:
        return False
    if pos in PROP_BY_POS:
        _, _, p, rents = PROP_BY_POS[pos]
        return (rents[0] / p) >= ROI_THRESHOLD
    return False


def strategy_position_based(player: Player, pos: int, price: int) -> bool:
    """Buy if the Markov steady-state visit probability is >=5% above the board average."""
    if player.cash - price < 150:
        return False
    avg_prob = sum(STEADY_STATE_PROBS) / len(STEADY_STATE_PROBS)
    return STEADY_STATE_PROBS[pos] >= avg_prob * 1.05


STRATEGIES = {
    "Greedy":         strategy_greedy,
    "Color Hunter":   strategy_color_hunter,
    "ROI-Based":      strategy_roi,
    "Position-Based": strategy_position_based,
}