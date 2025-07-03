import csv
import os
from .. import config

def convert_height_to_cm(height_str):
    """
    Converts a height string in the format 'X ft Y' to centimeters.
    Returns the original string if the format is unexpected or empty.
    """
    if not height_str or 'ft' not in height_str:
        return height_str
    
    try:
        parts = height_str.split(' ft')
        feet = int(parts[0].strip())
        inches_str = parts[1].strip()
        # Handle cases where inches might be missing (e.g., '6 ft')
        inches = int(inches_str) if inches_str else 0
        
        total_inches = (feet * 12) + inches
        cm = total_inches * 2.54
        return round(cm)
    except (ValueError, IndexError):
        # Return original value if parsing fails
        return height_str

def preprocess_fighters_csv(file_path=config.FIGHTERS_CSV_PATH):
    """
    Reads the fighters CSV, cleans names, converts height to cm, 
    and saves the changes back to the same file.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    try:
        rows = []
        headers = []
        # Read all data from the CSV into memory first
        with open(file_path, 'r', newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            # Return if there's no header or the file is empty
            if not reader.fieldnames:
                print(f"Warning: {file_path} is empty or has no headers.")
                return
            headers = reader.fieldnames
            rows = list(reader)

        # --- Data Cleaning and Processing ---
        
        name_cleaned_count = 0
        # Process the rows in memory
        for row in rows:
            # Clean fighter names (e.g., "O ftMalley" -> "O'Malley")
            for col in ['first_name', 'last_name']:
                if col in row and ' ft' in row[col]:
                    row[col] = row[col].replace(' ft', "'")
                    name_cleaned_count += 1

            # Convert height to cm and remove the old column
            if 'height' in row:
                row['height_cm'] = convert_height_to_cm(row.pop('height'))

        # Update the header name if 'height' was present
        if 'height' in headers:
            headers[headers.index('height')] = 'height_cm'

        # Write the modified data back to the same file, overwriting it
        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Successfully processed file: {file_path}")
        if name_cleaned_count > 0:
            print(f"Cleaned {name_cleaned_count} instances of ' ft' in fighter names.")
        if 'height_cm' in headers:
            print("Converted 'height' column to centimeters and renamed it to 'height_cm'.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    preprocess_fighters_csv() 