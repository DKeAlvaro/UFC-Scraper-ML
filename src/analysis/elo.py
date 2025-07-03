import csv
import os
from datetime import datetime

# --- ELO Configuration ---
INITIAL_ELO = 1500
K_FACTOR = 32
# --- End Configuration ---

def calculate_expected_score(rating1, rating2):
    """Calculates the expected score for player 1 against player 2."""
    return 1 / (1 + 10 ** ((rating2 - rating1) / 400))

def update_elo(winner_elo, loser_elo):
    """Calculates the new ELO ratings for a win/loss scenario."""
    expected_win = calculate_expected_score(winner_elo, loser_elo)
    change = K_FACTOR * (1 - expected_win)
    return winner_elo + change, loser_elo - change

def update_elo_draw(elo1, elo2):
    """Calculates the new ELO ratings for a draw."""
    expected1 = calculate_expected_score(elo1, elo2)
    change1 = K_FACTOR * (0.5 - expected1)
    
    expected2 = calculate_expected_score(elo2, elo1)
    change2 = K_FACTOR * (0.5 - expected2)

    return elo1 + change1, elo2 + change2

def process_fights_for_elo(fights_csv_path='output/ufc_fights.csv'):
    """
    Processes all fights chronologically to calculate final ELO scores for all fighters.
    """
    if not os.path.exists(fights_csv_path):
        print(f"Error: Fights data file not found at '{fights_csv_path}'.")
        print("Please run the scraping pipeline first using 'src/scrape/main.py'.")
        return None

    with open(fights_csv_path, 'r', encoding='utf-8') as f:
        fights = list(csv.DictReader(f))

    # Sort fights by date to process them in chronological order
    try:
        fights.sort(key=lambda x: datetime.strptime(x['event_date'], '%B %d, %Y'))
    except (ValueError, KeyError) as e:
        print(f"Error sorting fights by date. Make sure 'event_date' exists and is in 'Month Day, Year' format. Error: {e}")
        return None
        
    elos = {}
    
    for fight in fights:
        fighter1 = fight.get('fighter_1')
        fighter2 = fight.get('fighter_2')
        winner = fight.get('winner')

        # Initialize ELO for new fighters
        if fighter1 not in elos: elos[fighter1] = INITIAL_ELO
        if fighter2 not in elos: elos[fighter2] = INITIAL_ELO

        elo1 = elos[fighter1]
        elo2 = elos[fighter2]

        if winner == fighter1:
            elos[fighter1], elos[fighter2] = update_elo(elo1, elo2)
        elif winner == fighter2:
            elos[fighter2], elos[fighter1] = update_elo(elo2, elo1)
        elif winner == "Draw":
            elos[fighter1], elos[fighter2] = update_elo_draw(elo1, elo2)
        # NC (No Contest) fights do not affect ELO

    return elos

def add_elo_to_fighters_csv(elos, fighters_csv_path='output/ufc_fighters.csv'):
    """
    Adds the final ELO scores as a new column to the fighters CSV data.
    """
    if not elos:
        print("No ELO data to process. Aborting.")
        return
        
    if not os.path.exists(fighters_csv_path):
        print(f"Error: Fighters data file not found at '{fighters_csv_path}'. Cannot add ELO column.")
        return

    rows = []
    with open(fighters_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        # Ensure 'elo' column is added if not present
        if 'elo' not in headers:
            headers.append('elo')
        rows = list(reader)

    for row in rows:
        full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
        row['elo'] = round(elos.get(full_name, INITIAL_ELO))

    with open(fighters_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully updated '{fighters_csv_path}' with ELO ratings.")


def main():
    print("--- Starting ELO Calculation ---")
    final_elos = process_fights_for_elo()

    if final_elos:
        add_elo_to_fighters_csv(final_elos)
        
        # Sort fighters by ELO and print the top 10
        sorted_fighters = sorted(final_elos.items(), key=lambda item: item[1], reverse=True)
        
        print("\n--- Top 10 Fighters by ELO Rating ---")
        for i, (fighter, elo) in enumerate(sorted_fighters[:10]):
            print(f"{i+1}. {fighter}: {round(elo)}")
        print("------------------------------------")

if __name__ == '__main__':
    # Create the directory if it doesn't exist to avoid confusion
    if not os.path.exists('src/analysis'):
        os.makedirs('src/analysis')
    main() 