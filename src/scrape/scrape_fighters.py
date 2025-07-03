import requests
from bs4 import BeautifulSoup
import json
import time
import string
import concurrent.futures

# --- Configuration ---
# The number of parallel threads to use for scraping fighter details.
# Increase this to scrape faster, but be mindful of rate limits.
MAX_WORKERS = 10
# The delay in seconds between each request to a fighter's detail page.
# This is a politeness measure to avoid overwhelming the server.
REQUEST_DELAY = 0.1
# --- End Configuration ---

BASE_URL = "http://ufcstats.com/statistics/fighters?page=all"

def get_soup(url):
    """Fetches and parses a URL into a BeautifulSoup object."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_fighter_details(fighter_url):
    """Scrapes detailed statistics for a single fighter from their page."""
    print(f"  Scraping fighter details from: {fighter_url}")
    soup = get_soup(fighter_url)
    if not soup:
        return None

    details = {}
    
    # Career stats are usually in a list format on the fighter's page.
    # This finds all list items within the career statistics div and extracts the data.
    career_stats_div = soup.find('div', class_='b-list__info-box_style_small-width')
    if career_stats_div:
        stats_list = career_stats_div.find_all('li', class_='b-list__box-list-item')
        for item in stats_list:
            text = item.text.strip()
            if ":" in text:
                parts = text.split(":", 1)
                key = parts[0].strip().lower().replace(' ', '_').replace('.', '')
                value = parts[1].strip()
                details[key] = value
                
    return details

def process_fighter(fighter_data):
    """
    Worker function for the thread pool. Scrapes details for a single fighter,
    updates the dictionary, and applies a delay.
    """
    fighter_url = fighter_data['url']
    try:
        details = scrape_fighter_details(fighter_url)
        if details:
            fighter_data.update(details)
    except Exception as e:
        print(f"    Could not scrape details for {fighter_url}: {e}")
    
    time.sleep(REQUEST_DELAY)
    return fighter_data

def scrape_all_fighters():
    """Scrapes all fighters from a-z pages using parallel processing."""
    
    # Step 1: Sequentially scrape all fighter list pages. This is fast.
    initial_fighter_list = []
    alphabet = string.ascii_lowercase
    print("--- Step 1: Collecting basic fighter info from all list pages ---")
    for char in alphabet:
        page_url = f"http://ufcstats.com/statistics/fighters?char={char}&page=all"
        print(f"Scanning page: {page_url}")

        soup = get_soup(page_url)
        if not soup:
            continue

        table = soup.find('table', class_='b-statistics__table')
        if not table:
            print(f"Could not find fighters table on page {page_url}")
            continue

        fighter_rows = table.find('tbody').find_all('tr')[1:]
        if not fighter_rows:
            continue
            
        for row in fighter_rows:
            cols = row.find_all('td')
            if len(cols) < 11:
                continue

            fighter_link_tag = cols[0].find('a')
            if not fighter_link_tag or not fighter_link_tag.has_attr('href'):
                continue
            
            initial_fighter_list.append({
                'first_name': cols[0].text.strip(),
                'last_name': cols[1].text.strip(),
                'nickname': cols[2].text.strip(),
                'height': cols[3].text.strip(),
                'weight_lbs': cols[4].text.strip(),
                'reach_in': cols[5].text.strip(),
                'stance': cols[6].text.strip(),
                'wins': cols[7].text.strip(),
                'losses': cols[8].text.strip(),
                'draws': cols[9].text.strip(),
                'belt': False if not cols[10].find('img') else True,
                'url': fighter_link_tag['href']
            })

    print(f"\n--- Step 2: Scraping details for {len(initial_fighter_list)} fighters in parallel (using up to {MAX_WORKERS} workers) ---")
    fighters_with_details = []
    total_fighters = len(initial_fighter_list)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(process_fighter, initial_fighter_list)
        
        for i, fighter_data in enumerate(results):
            fighters_with_details.append(fighter_data)
            print(f"Progress: {i + 1}/{total_fighters} fighters scraped.")

            if (i + 1) > 0 and (i + 1) % 50 == 0:
                print(f"--- Saving progress: {i + 1} fighters saved. ---")
                # Sort before saving to maintain a consistent order in the file
                fighters_with_details.sort(key=lambda x: (x['last_name'], x['first_name']))
                with open('output/fighters_data.json', 'w') as f:
                    json.dump(fighters_with_details, f, indent=4)
                
    # Final sort for the complete dataset
    fighters_with_details.sort(key=lambda x: (x['last_name'], x['first_name']))
    return fighters_with_details

if __name__ == "__main__":
    all_fighters_data = scrape_all_fighters()
    
    # Create output directory if it doesn't exist
    import os
    if not os.path.exists('output'):
        os.makedirs('output')

    with open('output/fighters_data.json', 'w') as f:
        json.dump(all_fighters_data, f, indent=4)
        
    print(f"\nScraping complete. Final data for {len(all_fighters_data)} fighters saved to output/fighters_data.json") 