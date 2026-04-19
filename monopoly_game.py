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
        self.available_houses = 32
        self.available_hotels = 12
        self._determine_start_order()

    # ── Setup player order ─────────────────────────────────
    def _determine_start_order(self):
        rolls = [random.randint(1, 6) for _ in self.players]
        while len(set(rolls)) < len(rolls):
            duplicated = {}
            for i, value in enumerate(rolls):
                duplicated.setdefault(value, []).append(i)
            for tied in duplicated.values():
                if len(tied) > 1:
                    for i in tied:
                        rolls[i] = random.randint(1, 6)
        ordered_indices = sorted(range(len(self.players)), key=lambda i: rolls[i], reverse=True)
        self.players = [self.players[i] for i in ordered_indices]

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

        match card:
            case "advance_go":
                self.move_to(player, 0, collect_go=True)

            case "advance_illinois":
                self.move_to(player, 24, collect_go=True)

            case "advance_stcharles":
                self.move_to(player, 11, collect_go=True)

            case "advance_reading_railroad":
                self.move_to(player, 5, collect_go=True)

            case "advance_boardwalk":
                self.move_to(player, 39, collect_go=True)

            case "advance_nearest_railroad":
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

            case "advance_nearest_utility":
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

            case "bank_dividend_50":
                player.cash += 50

            case "get_out_of_jail_free":
                player.get_out_of_jail_cards += 1

            case "go_back_3":
                player.position = (player.position - 3) % 40
                self.land_on(player)

            case "go_to_jail":
                self.send_to_jail(player)

            case "speeding_fine_15":
                self.pay(player, 15)

            case "chance_repairs":
                # $25 per house, $100 per hotel
                cost = player.total_houses() * 25 + player.total_hotels() * 100
                self.pay(player, cost)

            case "chairman_of_board":
                # Pay $50 to EACH other player
                for other in self.players:
                    if other is not player and not other.bankrupt:
                        self.pay(player, 50)
                        other.cash += 50

            case "building_loan_150":
                player.cash += 150

            case _:
                pass

    def _apply_community_card(self, card, player):
        match card:
            case "advance_go":
                self.move_to(player, 0, collect_go=True)

            case "bank_error_200":
                player.cash += 200

            case "doctors_fee_50":
                self.pay(player, 50)

            case "stock_sale_50":
                player.cash += 50

            case "get_out_of_jail_free":
                player.get_out_of_jail_cards += 1

            case "go_to_jail":
                self.send_to_jail(player)

            case "holiday_fund_100":
                player.cash += 100

            case "income_tax_refund_20":
                player.cash += 20

            case "birthday_10":
                # Collect $10 from EACH other player
                for other in self.players:
                    if other is not player and not other.bankrupt:
                        self.pay(other, 10)
                        player.cash += 10

            case "life_insurance_100":
                player.cash += 100

            case "hospital_fees_100":
                self.pay(player, 100)

            case "school_fees_50":
                self.pay(player, 50)

            case "consultancy_fee_25":
                player.cash += 25

            case "community_repairs":
                # $40 per house, $115 per hotel (different from Chance repairs)
                cost = player.total_houses() * 40 + player.total_hotels() * 115
                self.pay(player, cost)

            case "beauty_contest_10":
                player.cash += 10

            case "inherit_100":
                player.cash += 100

            case _:
                pass

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
        if player.cash < 0 and not player.bankrupt:
            player.bankrupt = True
            self._release_assets_to_bank(player)

    # ── Landing ───────────────────────────────

    def land_on(self, player):
        pos = player.position
        square = SPECIAL_SQUARES.get(pos, "property")

        match square:
            case "GO":
                player.cash += 200

            case "INCOME_TAX":
                flat_tax = 200
                pct_tax = int(player.net_worth() * 0.10)
                self.pay(player, min(flat_tax, pct_tax))

            case "LUXURY_TAX":
                self.pay(player, 75)

            case "GO_TO_JAIL":
                self.send_to_jail(player)

            case "CHANCE":
                self.draw_chance(player)

            case "COMMUNITY_CHEST":
                self.draw_community(player)

            case "JAIL" | "FREE_PARKING":
                pass

            case _:
                self.handle_purchase_or_rent(player, pos)

    def handle_purchase_or_rent(self, player, pos):
        player_idx = self.players.index(player)

        match pos:
            case _ if pos in RAILROADS:
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

            case _ if pos in UTILITIES:
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

            case _ if pos in PROP_BY_POS:
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

            case _:
                pass

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
                if player.cash - house_cost < 300:
                    continue
                if h == 4:
                    if self.available_hotels <= 0:
                        continue
                    self.available_hotels -= 1
                    self.available_houses += 4
                else:
                    if self.available_houses <= 0:
                        continue
                    self.available_houses -= 1
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
    
    # ── Bankruptcy ─────────────────────────────
    def _release_assets_to_bank(self, player):
        player_idx = self.players.index(player)

        for pos, house_count in player.houses.items():
            if house_count >= 5:
                self.available_hotels += 1
                self.available_houses += 4
            else:
                self.available_houses += house_count
        player.houses.clear()

        self.ownership = {
            pos: owner_idx
            for pos, owner_idx in self.ownership.items()
            if owner_idx != player_idx
        }

        player.properties_owned.clear()
        player.railroads_owned.clear()
        player.utilities_owned.clear()
        player.get_out_of_jail_cards = 0
        
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