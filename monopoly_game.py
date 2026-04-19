"""
Monopoly Game Engine
"""

import random
from board_setup import (
    RAILROADS, UTILITIES, PROP_BY_POS, SPECIAL_SQUARES,
    shuffle_decks, COLOR_GROUPS, HOUSE_COSTS
)
from player import Player, STRATEGIES


class MonopolyGame:
    def __init__(self, strategy_names, max_turns=300, verbose=False):
        self.players = [Player(name=s, strategy=s) for s in strategy_names]
        self.max_turns = max_turns
        self.verbose = verbose
        self.chance_deck, self.community_deck = shuffle_decks()
        self.chance_idx = 0
        self.community_idx = 0
        self.ownership = {}   # board_pos -> player index

    # ── Dice ──────────────────────────────────

    def roll_dice(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        return d1, d2

    # ── Cards ─────────────────────────────────

    def draw_chance(self, player):
        card = self.chance_deck[self.chance_idx % len(self.chance_deck)]
        self.chance_idx += 1
        self._apply_chance_card(card, player)

    def draw_community(self, player):
        card = self.community_deck[self.community_idx % len(self.community_deck)]
        self.community_idx += 1
        self._apply_community_card(card, player)

    def _apply_chance_card(self, card, player):
        player_idx = self.players.index(player)

        if card == "advance_go":
            self.move_to(player, 0, collect_go=True)

        elif card == "advance_illinois":
            self.move_to(player, 24, collect_go=True)

        elif card == "advance_stcharles":
            self.move_to(player, 11, collect_go=True)

        elif card == "advance_reading_railroad":
            self.move_to(player, 5, collect_go=True)

        elif card == "advance_boardwalk":
            self.move_to(player, 39, collect_go=True)

        elif card == "advance_nearest_railroad":
            nearest = min(RAILROADS, key=lambda r: (r - player.position) % 40)
            if nearest < player.position:
                player.cash += 200  # passed GO
            player.position = nearest
            if nearest in self.ownership:
                owner_idx = self.ownership[nearest]
                if owner_idx != player_idx:
                    owner = self.players[owner_idx]
                    rr_count = len(owner.railroads_owned)
                    base_rent = [0, 25, 50, 100, 200][rr_count]
                    rent = base_rent * 2
                    self.pay(player, rent)
                    owner.cash += rent
            else:
                # Unowned — player may buy at normal price
                self.handle_purchase_or_rent(player, nearest)

        elif card == "advance_nearest_utility":
            # FIX: if owned, always pay 10x dice roll (not the standard 4x/10x formula)
            nearest = min(UTILITIES, key=lambda u: (u - player.position) % 40)
            if nearest < player.position:
                player.cash += 200  # passed GO
            player.position = nearest
            if nearest in self.ownership:
                owner_idx = self.ownership[nearest]
                if owner_idx != player_idx:
                    owner = self.players[owner_idx]
                    d1, d2 = self.roll_dice()
                    rent = (d1 + d2) * 10   # always 10x when moved by Chance
                    self.pay(player, rent)
                    owner.cash += rent
            else:
                self.handle_purchase_or_rent(player, nearest)

        elif card == "bank_dividend_50":
            player.cash += 50

        elif card == "get_out_of_jail_free":
            player.get_out_of_jail_cards += 1

        elif card == "go_back_3":
            player.position = (player.position - 3) % 40
            self.land_on(player)

        elif card == "go_to_jail":
            self.send_to_jail(player)

        elif card == "speeding_fine_15":
            self.pay(player, 15)

        elif card == "chance_repairs":
            # $25 per house, $100 per hotel
            cost = player.total_houses() * 25 + player.total_hotels() * 100
            self.pay(player, cost)

        elif card == "chairman_of_board":
            # Pay $50 to EACH other player
            for other in self.players:
                if other is not player and not other.bankrupt:
                    self.pay(player, 50)
                    other.cash += 50

        elif card == "building_loan_150":
            player.cash += 150

    def _apply_community_card(self, card, player):
        if card == "advance_go":
            self.move_to(player, 0, collect_go=True)

        elif card == "bank_error_200":
            player.cash += 200

        elif card == "doctors_fee_50":
            self.pay(player, 50)

        elif card == "stock_sale_50":
            player.cash += 50

        elif card == "get_out_of_jail_free":
            player.get_out_of_jail_cards += 1

        elif card == "go_to_jail":
            self.send_to_jail(player)

        elif card == "holiday_fund_100":
            player.cash += 100

        elif card == "income_tax_refund_20":
            player.cash += 20

        elif card == "birthday_10":
            # Collect $10 from EACH other player
            for other in self.players:
                if other is not player and not other.bankrupt:
                    self.pay(other, 10)
                    player.cash += 10

        elif card == "life_insurance_100":
            player.cash += 100

        elif card == "hospital_fees_100":
            self.pay(player, 100)

        elif card == "school_fees_50":
            self.pay(player, 50)

        elif card == "consultancy_fee_25":
            player.cash += 25

        elif card == "community_repairs":
            # $40 per house, $115 per hotel (different from Chance repairs)
            cost = player.total_houses() * 40 + player.total_hotels() * 115
            self.pay(player, cost)

        elif card == "beauty_contest_10":
            player.cash += 10

        elif card == "inherit_100":
            player.cash += 100

    # ── Movement ──────────────────────────────

    def move_to(self, player, target, collect_go=False):
        """Move directly to target; collect $200 if passing or landing on GO."""
        if collect_go and target <= player.position:
            player.cash += 200
        player.position = target
        self.land_on(player)

    def send_to_jail(self, player):
        player.position = 10
        player.in_jail = True
        player.jail_turns = 0
        player.doubles_streak = 0

    def pay(self, player, amount):
        player.cash -= amount
        if player.cash < 0:
            player.bankrupt = True

    # ── Landing ───────────────────────────────

    def land_on(self, player):
        pos = player.position
        square = SPECIAL_SQUARES.get(pos, "property")

        if square == "GO":
            player.cash += 200

        elif square == "INCOME_TAX":
            flat_tax = 200
            pct_tax = int(player.net_worth() * 0.10)
            self.pay(player, min(flat_tax, pct_tax))

        elif square == "LUXURY_TAX":
            self.pay(player, 75)

        elif square == "GO_TO_JAIL":
            self.send_to_jail(player)

        elif square == "CHANCE":
            self.draw_chance(player)

        elif square == "COMMUNITY_CHEST":
            self.draw_community(player)

        elif square in ("JAIL", "FREE_PARKING"):
            pass

        else:
            self.handle_purchase_or_rent(player, pos)

    def handle_purchase_or_rent(self, player, pos):
        player_idx = self.players.index(player)

        if pos in RAILROADS:
            price = 200
            if pos not in self.ownership:
                if STRATEGIES[player.strategy](player, pos, price) and player.cash >= price:
                    player.cash -= price
                    self.ownership[pos] = player_idx
                    player.railroads_owned.append(pos)
            else:
                owner_idx = self.ownership[pos]
                if owner_idx != player_idx:
                    owner = self.players[owner_idx]
                    rr_count = len(owner.railroads_owned)
                    rent = [0, 25, 50, 100, 200][rr_count]
                    self.pay(player, rent)
                    owner.cash += rent

        elif pos in UTILITIES:
            price = 150
            if pos not in self.ownership:
                if STRATEGIES[player.strategy](player, pos, price) and player.cash >= price:
                    player.cash -= price
                    self.ownership[pos] = player_idx
                    player.utilities_owned.append(pos)
            else:
                owner_idx = self.ownership[pos]
                if owner_idx != player_idx:
                    owner = self.players[owner_idx]
                    util_count = len(owner.utilities_owned)
                    d1, d2 = self.roll_dice()
                    multiplier = 10 if util_count == 2 else 4
                    rent = (d1 + d2) * multiplier
                    self.pay(player, rent)
                    owner.cash += rent

        elif pos in PROP_BY_POS:
            color, name, price, rents = PROP_BY_POS[pos]
            if pos not in self.ownership:
                if STRATEGIES[player.strategy](player, pos, price) and player.cash >= price:
                    player.cash -= price
                    self.ownership[pos] = player_idx
                    player.properties_owned.append(pos)
            else:
                owner_idx = self.ownership[pos]
                if owner_idx != player_idx:
                    owner = self.players[owner_idx]
                    house_count = owner.houses.get(pos, 0)
                    if house_count == 0 and owner.owns_color_set(color):
                        rent = rents[0] * 2   # double rent on unimproved monopoly
                    else:
                        rent = rents[min(house_count, 5)]
                    self.pay(player, rent)
                    owner.cash += rent

    # ── Building ──────────────────────────────

    def try_build_houses(self, player):
        """
        Greedily build houses/hotels on all owned monopolies.
        Respects the even-building rule (lowest house count built first).
        Uses correct per-color house costs.
        """
        for color in COLOR_GROUPS:
            if not player.owns_color_set(color):
                continue
            group = COLOR_GROUPS[color]
            house_cost = HOUSE_COSTS[color] 
            for pos in sorted(group, key=lambda p: player.houses.get(p, 0)):
                h = player.houses.get(pos, 0)
                if h >= 5:
                    continue
                if player.cash - house_cost >= 300:
                    player.cash -= house_cost
                    player.houses[pos] = h + 1

    # ── Turn ──────────────────────────────────

    def player_turn(self, player):
        if player.bankrupt:
            return

        d1, d2 = self.roll_dice()
        doubles = (d1 == d2)

        # ── Jail handling ──
        if player.in_jail:
            if player.get_out_of_jail_cards > 0:
                # Use a Get Out of Jail Free card, then move normally
                player.get_out_of_jail_cards -= 1
                player.in_jail = False
                player.jail_turns = 0
                # Fall through to normal movement
            elif doubles:
                player.in_jail = False
                player.jail_turns = 0
                steps = d1 + d2
                new_pos = player.position + steps
                if new_pos >= 40:
                    player.cash += 200
                player.position = new_pos % 40
                self.land_on(player)
                self.try_build_houses(player)
                player.net_worth_history.append(player.net_worth())
                return   # no bonus roll after jail-escape doubles

            else:
                player.jail_turns += 1
                if player.jail_turns >= 3:
                    self.pay(player, 50)
                    player.in_jail = False
                    player.jail_turns = 0
                    # Fall through to normal movement with this roll
                else:
                    player.net_worth_history.append(player.net_worth())
                    return   # still in jail

        # ── Normal movement ──
        if doubles:
            player.doubles_streak += 1
            if player.doubles_streak == 3:
                self.send_to_jail(player)
                player.net_worth_history.append(player.net_worth())
                return
        else:
            player.doubles_streak = 0

        steps = d1 + d2
        new_pos = player.position + steps
        if new_pos >= 40:
            player.cash += 200  # passed GO
        player.position = new_pos % 40

        self.land_on(player)
        self.try_build_houses(player)
        player.net_worth_history.append(player.net_worth())

        # Bonus roll on doubles (only if not sent to jail this turn)
        if doubles and not player.in_jail and not player.bankrupt:
            self.player_turn(player)

    # ── Game loop ─────────────────────────────

    def run(self):
        active = list(range(len(self.players)))
        for _ in range(self.max_turns):
            for i in active[:]:
                self.player_turn(self.players[i])
                if self.players[i].bankrupt:
                    active.remove(i)
            if len(active) <= 1:
                break
        return max(self.players, key=lambda p: p.net_worth())