# Monopoly Simulation

Simplified Monte-Carlo simulator of Monopoly games.

## Rules removed / changed 
- Auctions, trading between players, selling / mortgaging assets have been removed. 
- When a player goes bankrupt all of their assets return to The Bank. 
- Card decks are not reshuffled when exhausted. 

## Assumptions about all players:
- Greedy house / hotel building after every term. After every turn, players will try to build houses if they can afford them and they are available. 
- If a player goes to jail and has a get out of jail free card, then they will always use their card. If they don’t have a card, then they will try to roll for a double. If they do not get a double after 3 turns, they will pay the $50 to get out. 


## Files Structure

- **`board_setup.py`**: Contains all board-related constants, property data, card decks, and setup functions
  - Board positions and probabilities
  - Property definitions and costs
  - Card deck definitions and shuffling

- **`player.py`**: Contains the Player class and strategy functions
  - Player dataclass with all attributes and methods
  - Four different buying strategies (Greedy, Color Hunter, ROI-Based, Position-Based)

- **`monopoly_game.py`**: Contains the main game engine
  - MonopolyGame class with all game logic
  - Turn handling, movement, property purchases, rent collection
  - Card effects and special square handling

- **`monte_carlo_runner.py`**: Contains the simulation runner and results analysis
  - Monte Carlo simulation function
  - Results printing and JSON export
  - Main execution block

## Dependencies

The modules import from each other as follows:
- `player.py` imports from `board_setup.py`
- `monopoly_game.py` imports from `board_setup.py` and `player.py`
- `monte_carlo_runner.py` imports from `monopoly_game.py`

## Running the Simulation

To run the full simulation:
```bash
python3 monte_carlo_runner.py
```

For a quick test with fewer games:
```python
from monte_carlo_runner import run_simulation, print_results
results = run_simulation(n_games=100, max_turns=100)
print_results(results)
```
