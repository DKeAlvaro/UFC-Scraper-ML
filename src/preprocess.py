import csv
import os

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

def preprocess_fighters_csv(file_path='output/ufc_fighters_data.csv'):
    """
    Reads the fighters CSV, converts height to cm, renames the column,
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

        # Check if there's a 'height' column to process
        if 'height' not in headers:
            print("No 'height' column found. Nothing to do.")
            return

        # Process the rows in memory
        for row in rows:
            # Create a new key for the converted height and remove the old one
            row['height_cm'] = convert_height_to_cm(row.pop('height', ''))

        # Update the header name
        headers[headers.index('height')] = 'height_cm'

        # Write the modified data back to the same file, overwriting it
        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Successfully processed file: {file_path}")
        print("Converted 'height' column to centimeters and renamed it to 'height_cm'.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    preprocess_fighters_csv()
