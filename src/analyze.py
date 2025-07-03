import json
import pandas as pd

ufc_events = json.load(open('output/ufc_fights.json'))
ufc_events_csv = pd.read_csv('output/ufc_fights.csv')
ufc_fighters_csv = pd.read_csv('output/ufc_fighters.csv')


unique_fighters = set()

for event in ufc_events:
    for fight in event['fights']:
        unique_fighters.add(fight['fighter_1'])
        unique_fighters.add(fight['fighter_2'])

unique_fighters_csv=set()
for fight in ufc_events_csv['fighter_1']:
    unique_fighters_csv.add(fight)
for fight in ufc_events_csv['fighter_2']:
    unique_fighters_csv.add(fight)

print(len(unique_fighters))
print(len(unique_fighters_csv))


