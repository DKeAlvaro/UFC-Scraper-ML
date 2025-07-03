import json

ufc_events = json.load(open('ufc_events_detailed.json'))

unique_fighters = set()

for event in ufc_events:
    for fight in event['fights']:
        unique_fighters.add(fight['fighter_1'])
        unique_fighters.add(fight['fighter_2'])

print(len(unique_fighters))



