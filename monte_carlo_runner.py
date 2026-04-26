"""
Monopoly Monte Carlo Simulation Runner
Discrete Math Project - 4 Heuristic Strategy Comparison
"""

import random
random.seed(100)

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

    print(f"\n{'='*55}")
    print(f"  MONOPOLY MONTE CARLO SIMULATION")
    print(f"  {n_games} games x {max_turns} max turns")
    print(f"  Strategies: {', '.join(strategies)}")
    print(f"{'='*55}\n")

    for game_num in range(n_games):
        if (game_num + 1) % 100 == 0:
            print(f"  Simulating game {game_num + 1}/{n_games}...")

        game = MonopolyGame(strategies, max_turns=max_turns)
        winner = game.run()
        wins[winner.strategy] += 1

        for p in game.players:
            final_net_worths[p.strategy].append(p.net_worth())
            final_cash[p.strategy].append(p.cash)
            properties_acquired[p.strategy].append(
                len(p.properties_owned) + len(p.railroads_owned) + len(p.utilities_owned)
            )
            if p.bankrupt:
                bankruptcies[p.strategy] += 1

    return {
        "n_games": n_games,
        "strategies": strategies,
        "wins": dict(wins),
        "win_rate": {s: wins[s] / n_games for s in strategies},
        "avg_net_worth": {s: statistics.mean(final_net_worths[s]) for s in strategies},
        "median_net_worth": {s: statistics.median(final_net_worths[s]) for s in strategies},
        "std_net_worth": {s: statistics.stdev(final_net_worths[s]) if len(final_net_worths[s]) > 1 else 0 for s in strategies},
        "avg_cash": {s: statistics.mean(final_cash[s]) for s in strategies},
        "avg_properties": {s: statistics.mean(properties_acquired[s]) for s in strategies},
        "bankruptcy_rate": {s: bankruptcies[s] / n_games for s in strategies},
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


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":

    results = run_simulation(
        n_games=100000,
        max_turns=300,
        strategies=["Greedy", "Color Hunter", "ROI-Based", "Cash Aware"],
    )

    print_results(results)

    with open("simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to simulation_results.json")