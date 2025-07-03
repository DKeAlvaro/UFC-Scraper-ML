import json
import csv
import config

def json_to_csv(json_file_path, csv_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        print(f"Error: The file {json_file_path} was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}.")
        return

    # Define the headers for the CSV file
    headers = [
        'event_name', 'event_date', 'event_location', 'fighter_1', 'fighter_2', 'winner',
        'weight_class', 'method', 'round', 'time',
        'f1_kd', 'f1_sig_str', 'f1_sig_str_percent', 'f1_total_str', 'f1_td', 
        'f1_td_percent', 'f1_sub_att', 'f1_rev', 'f1_ctrl',
        'f1_sig_str_head', 'f1_sig_str_body', 'f1_sig_str_leg', 'f1_sig_str_distance',
        'f1_sig_str_clinch', 'f1_sig_str_ground',
        'f2_kd', 'f2_sig_str', 'f2_sig_str_percent', 'f2_total_str', 'f2_td',
        'f2_td_percent', 'f2_sub_att', 'f2_rev', 'f2_ctrl',
        'f2_sig_str_head', 'f2_sig_str_body', 'f2_sig_str_leg', 'f2_sig_str_distance',
        'f2_sig_str_clinch', 'f2_sig_str_ground'
    ]

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

        for event in data:
            for fight in event.get('fights', []):
                details = fight.get('details')
                
                # Create a dictionary for easier and safer access to stats
                f1_stats = details.get('fighter_1_stats', {}) if details else {}
                f2_stats = details.get('fighter_2_stats', {}) if details else {}

                row = [
                    event.get('name', ''),
                    event.get('date', ''),
                    event.get('location', ''),
                    fight.get('fighter_1', ''),
                    fight.get('fighter_2', ''),
                    fight.get('winner', ''),
                    fight.get('weight_class', ''),
                    fight.get('method', ''),
                    fight.get('round', ''),
                    fight.get('time', ''),
                    f1_stats.get('kd', ''),
                    f1_stats.get('sig_str', ''),
                    f1_stats.get('sig_str_percent', ''),
                    f1_stats.get('total_str', ''),
                    f1_stats.get('td', ''),
                    f1_stats.get('td_percent', ''),
                    f1_stats.get('sub_att', ''),
                    f1_stats.get('rev', ''),
                    f1_stats.get('ctrl', ''),
                    f1_stats.get('sig_str_head', ''),
                    f1_stats.get('sig_str_body', ''),
                    f1_stats.get('sig_str_leg', ''),
                    f1_stats.get('sig_str_distance', ''),
                    f1_stats.get('sig_str_clinch', ''),
                    f1_stats.get('sig_str_ground', ''),
                    f2_stats.get('kd', ''),
                    f2_stats.get('sig_str', ''),
                    f2_stats.get('sig_str_percent', ''),
                    f2_stats.get('total_str', ''),
                    f2_stats.get('td', ''),
                    f2_stats.get('td_percent', ''),
                    f2_stats.get('sub_att', ''),
                    f2_stats.get('rev', ''),
                    f2_stats.get('ctrl', ''),
                    f2_stats.get('sig_str_head', ''),
                    f2_stats.get('sig_str_body', ''),
                    f2_stats.get('sig_str_leg', ''),
                    f2_stats.get('sig_str_distance', ''),
                    f2_stats.get('sig_str_clinch', ''),
                    f2_stats.get('sig_str_ground', '')
                ]
                writer.writerow(row)

    print(f"Successfully converted {json_file_path} to {csv_file_path}")

def fighters_json_to_csv(json_file_path, csv_file_path):
    """
    Converts a JSON file containing a list of fighter data to a CSV file.
    It cleans the data by removing unwanted characters and standardizing formats.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        print(f"Error: The file {json_file_path} was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}.")
        return

    if not data:
        print(f"Warning: The file {json_file_path} is empty. No CSV will be created.")
        return
        
    # Dynamically determine headers by collecting all keys from all records
    all_keys = set()
    for item in data:
        all_keys.update(item.keys())
    
    # Define a preferred order for the most important columns
    preferred_headers = [
        'first_name', 'last_name', 'nickname', 'wins', 'losses', 'draws', 'belt',
        'height', 'weight_lbs', 'reach_in', 'stance', 'dob', 'slpm', 
        'str_acc', 'sapm', 'str_def', 'td_avg', 'td_acc', 'td_def', 'sub_avg', 'url'
    ]
    
    # Create the final list of headers, with preferred ones first
    headers = [h for h in preferred_headers if h in all_keys]
    headers.extend(sorted([k for k in all_keys if k not in preferred_headers]))

    def clean_value(value):
        if isinstance(value, str):
            # Clean data by removing unwanted characters and standardizing units
            # As requested, this removes '"' and '--'. It also cleans up units.
            cleaned_value = value.replace('--', '').replace('"', '').replace("'", " ft").replace(' lbs.', '')
            return cleaned_value.strip()
        return value

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()

        for fighter_data in data:
            # Get a cleaned version of the row, using get() for safety
            cleaned_row = {key: clean_value(fighter_data.get(key, '')) for key in headers}
            writer.writerow(cleaned_row)

    print(f"Successfully converted {json_file_path} to {csv_file_path}")

if __name__ == '__main__':
    json_to_csv(config.EVENTS_JSON_PATH, config.FIGHTS_CSV_PATH) 
    fighters_json_to_csv(config.FIGHTERS_JSON_PATH, config.FIGHTERS_CSV_PATH) 