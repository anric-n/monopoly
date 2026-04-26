"""
Monopoly Monte Carlo Simulation Runner
Discrete Math Project - 4 Heuristic Strategy Comparison
"""

import random

import statistics
from collections import defaultdict
import json
from monopoly_game import MonopolyGame


def run_simulation(n_games=1000, max_turns=300, strategies=None):
    if strategies is None:
        strategies = ["Greedy", "Color Hunter", "ROI-Based", "Cash Aware"]

    wins = defaultdict(int)
    final_net_worths = defaultdict(list)
    final_cash = defaultdict(list)
    properties_acquired = defaultdict(list)
    bankruptcies = defaultdict(int)

    # Build stable, unique player labels so duplicate strategy names don't collapse
    from collections import defaultdict as _dd
    _counts = _dd(int)
    player_labels = []
    for s in strategies:
        _counts[s] += 1
        player_labels.append(f"{s} #{_counts[s]}")

    print(f"\n{'='*55}")
    print(f"  MONOPOLY MONTE CARLO SIMULATION")
    print(f"  {n_games} games x {max_turns} max turns")
    print(f"  Players: {', '.join(player_labels)}")
    print(f"{'='*55}\n")

    for game_num in range(n_games):
        random.seed(game_num)  # for reproducibility and fair comparison
        if (game_num + 1) % 100 == 0:
            print(f"  Simulating game {game_num + 1}/{n_games}...")

        game = MonopolyGame(strategies, max_turns=max_turns)
        # Assign stable, unique names to the Player instances based on the
        # requested strategies so identical strategy strings don't collapse
        # together when aggregating statistics.
        name_pool = {k: v.copy() for k, v in _dd(list, {s: []}).items()}
        # Build a fresh name pool in the same order as player_labels
        _tmp_counts = _dd(int)
        for label, s in zip(player_labels, strategies):
            _tmp_counts[s] += 1
            name_pool.setdefault(s, []).append(label)

        for p in game.players:
            # pop labels in the order they were generated
            p.name = name_pool[p.strategy].pop(0)
        winner = game.run()
        wins[winner.name] += 1

        for p in game.players:
            final_net_worths[p.name].append(p.net_worth())
            final_cash[p.name].append(p.cash)
            properties_acquired[p.name].append(
                len(p.properties_owned) + len(p.railroads_owned) + len(p.utilities_owned)
            )
            if p.bankrupt:
                bankruptcies[p.name] += 1

    return {
        "n_games": n_games,
    # 'strategies' contains the per-player labels (unique even for duplicate
    # strategies). Also include a mapping from player label -> strategy.
    "strategies": player_labels,
    "strategy_map": {label: s for label, s in zip(player_labels, strategies)},
    "wins": dict(wins),
    "win_rate": {s: wins[s] / n_games for s in player_labels},
    "avg_net_worth": {s: statistics.mean(final_net_worths[s]) for s in player_labels},
    "median_net_worth": {s: statistics.median(final_net_worths[s]) for s in player_labels},
    "std_net_worth": {s: statistics.stdev(final_net_worths[s]) if len(final_net_worths[s]) > 1 else 0 for s in player_labels},
    "avg_cash": {s: statistics.mean(final_cash[s]) for s in player_labels},
    "avg_properties": {s: statistics.mean(properties_acquired[s]) for s in player_labels},
    "bankruptcy_rate": {s: bankruptcies[s] / n_games for s in player_labels},
    }


def print_results(results):
    strategies = results["strategies"]
    ranked = sorted(strategies, key=lambda s: results["win_rate"][s], reverse=True)

    print(f"\n{'='*55}")
    print(f"  RESULTS AFTER {results['n_games']} GAMES")
    print(f"{'='*55}")
    print(f"\n{'Rank':<6} {'Strategy':<18} {'Win%':>7} {'Avg NW':>12} {'Props':>7} {'Bankrupt%':>10}")
    print("-" * 65)
    for i, s in enumerate(ranked, 1):
        print(
            f"{i:<6} {s:<18} "
            f"{results['win_rate'][s]*100:>6.1f}% "
            f"${results['avg_net_worth'][s]:>10,.0f} "
            f"{results['avg_properties'][s]:>7.1f} "
            f"{results['bankruptcy_rate'][s]*100:>9.1f}%"
        )

    print(f"\n{'Strategy':<18} {'Median NW':>12} {'Std Dev':>10}")
    print("-" * 45)
    for s in ranked:
        print(
            f"{s:<18} "
            f"${results['median_net_worth'][s]:>10,.0f} "
            f"${results['std_net_worth'][s]:>8,.0f}"
        )

    print(f"\n{'='*55}")
    print(f"  WINNER: {ranked[0]} ({results['win_rate'][ranked[0]]*100:.1f}% win rate)")
    print(f"{'='*55}\n")


def run_one_game_describe(strategies, max_turns=1000):
    """Run one game and return per-player descriptions.

    Returns a dict with player labels, strategy_map, winner, and summaries.
    """
    # Build unique labels
    from collections import defaultdict as _dd
    _counts = _dd(int)
    player_labels = []
    for s in strategies:
        _counts[s] += 1
        player_labels.append(f"{s} #{_counts[s]}")

    game = MonopolyGame(strategies, max_turns=max_turns)
    # assign labels to players
    name_pool = _dd(list)
    for label, s in zip(player_labels, strategies):
        name_pool[s].append(label)
    for p in game.players:
        p.name = name_pool[p.strategy].pop(0)

    winner = game.run()

    # build summaries
    from board_setup import PROP_BY_POS as _PROP
    summaries = {}
    for p in game.players:
        props = [(_PROP[pos][1] if pos in _PROP else f"Square {pos}") for pos in p.properties_owned]
        rrs = [str(r) for r in p.railroads_owned]
        utils = [str(u) for u in p.utilities_owned]
        houses = {(_PROP[pos][1] if pos in _PROP else f"Square {pos}"): cnt for pos, cnt in p.houses.items()}
        nw_hist = p.net_worth_history
        summaries[p.name] = {
            "strategy": p.strategy,
            "final_cash": p.cash,
            "final_net_worth": p.net_worth(),
            "bankrupt": p.bankrupt,
            "properties": props,
            "railroads": rrs,
            "utilities": utils,
            "houses": houses,
            "net_worth_history_sample": {
                "first": nw_hist[0] if nw_hist else None,
                "last": nw_hist[-1] if nw_hist else None,
            }
        }

    return {
        "player_labels": player_labels,
        "strategy_map": {label: s for label, s in zip(player_labels, strategies)},
        "winner": winner.name,
        "summaries": summaries,
    }


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":

    results = run_simulation(
        n_games=10000,
        max_turns=300,
        strategies=["Cash Aware", "Cash Aware", "Greedy", "Greedy"]
    )

    print_results(results)

    with open("simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to simulation_results.json")+