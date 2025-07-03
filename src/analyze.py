import pandas as pd

ufc_fights = pd.read_csv('output/ufc_fights.csv')
ufc_fighters = pd.read_csv('output/ufc_fighters.csv')

print(f"Number of fighters registered in UFC: {len(ufc_fighters)}")
unique_fighters=set()
for fight in ufc_fights['fighter_1']:
    unique_fighters.add(fight)
for fight in ufc_fights['fighter_2']:
    unique_fighters.add(fight)
print(f"Number of fighters who have at least one fight: {len(unique_fighters)}")

highest_elo_fighters=ufc_fighters.sort_values(by='elo', ascending=False).head(20)
print(highest_elo_fighters)
