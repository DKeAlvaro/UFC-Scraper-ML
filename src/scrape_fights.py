import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "http://ufcstats.com/statistics/events/completed?page=all"

def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes
    return BeautifulSoup(response.text, 'html.parser')

def scrape_fight_details(fight_url):
    print(f"  Scraping fight: {fight_url}")
    soup = get_soup(fight_url)
    
    # On upcoming fight pages, there's a specific div. If it exists, skip.
    if soup.find('div', class_='b-fight-details__content-abbreviated'):
        print(f"    Upcoming fight, no details available: {fight_url}")
        return None

    tables = soup.find_all('table', class_='b-fight-details__table')

    if not tables:
        print(f"    No stats tables found on {fight_url}")
        return None

    fight_details = {"fighter_1_stats": {}, "fighter_2_stats": {}}

    # Helper to extract stats. The stats for both fighters are in <p> tags within a single <td>
    def extract_stats_from_cell(cell, col_name):
        ps = cell.find_all('p')
        if len(ps) == 2:
            fight_details["fighter_1_stats"][col_name] = ps[0].text.strip()
            fight_details["fighter_2_stats"][col_name] = ps[1].text.strip()

    # --- Totals Table ---
    # The first table contains overall stats
    totals_table = tables[0]
    totals_tbody = totals_table.find('tbody')
    if totals_tbody:
        totals_row = totals_tbody.find('tr')
        if totals_row:
            totals_cols = totals_row.find_all('td')
            stat_cols = {
                1: 'kd', 2: 'sig_str', 3: 'sig_str_percent', 4: 'total_str',
                5: 'td', 6: 'td_percent', 7: 'sub_att', 8: 'rev', 9: 'ctrl'
            }
            for index, name in stat_cols.items():
                if index < len(totals_cols):
                    extract_stats_from_cell(totals_cols[index], name)

    # --- Significant Strikes Table ---
    # The second table contains significant strike details
    if len(tables) > 1:
        sig_strikes_table = tables[1]
        sig_strikes_tbody = sig_strikes_table.find('tbody')
        if sig_strikes_tbody:
            sig_strikes_row = sig_strikes_tbody.find('tr')
            if sig_strikes_row:
                sig_strikes_cols = sig_strikes_row.find_all('td')
                stat_cols = {
                    2: 'sig_str_head', 3: 'sig_str_body', 4: 'sig_str_leg',
                    5: 'sig_str_distance', 6: 'sig_str_clinch', 7: 'sig_str_ground'
                }
                for index, name in stat_cols.items():
                     if index < len(sig_strikes_cols):
                        extract_stats_from_cell(sig_strikes_cols[index], name)

    return fight_details

def scrape_event_details(event_url):
    print(f"Scraping event: {event_url}")
    soup = get_soup(event_url)
    event_details = {}
    
    # Extract event name
    event_details['name'] = soup.find('h2', class_='b-content__title').text.strip()

    # Extract event date and location
    info_list = soup.find('ul', class_='b-list__box-list')
    list_items = info_list.find_all('li', class_='b-list__box-list-item')
    event_details['date'] = list_items[0].text.split(':')[1].strip()
    event_details['location'] = list_items[1].text.split(':')[1].strip()

    # Extract fights
    fights = []
    fight_table = soup.find('table', class_='b-fight-details__table')
    if fight_table:
        rows = fight_table.find('tbody').find_all('tr', class_='b-fight-details__table-row')
        for row in rows:
            cols = row.find_all('td', class_='b-fight-details__table-col')
            
            fight_url = row['data-link']
            
            fight = {
                'fighter_1': cols[1].find_all('p')[0].text.strip(),
                'fighter_2': cols[1].find_all('p')[1].text.strip(),
                'weight_class': cols[6].text.strip(),
                'method': ' '.join(cols[7].stripped_strings),
                'round': cols[8].text.strip(),
                'time': cols[9].text.strip(),
            }

            try:
                details = scrape_fight_details(fight_url)
                if details:
                    fight['details'] = details
                else:
                    fight['details'] = None
                time.sleep(0.1) # a small delay to be polite to the server
            except Exception as e:
                print(f"    Could not scrape fight details for {fight_url}: {e}")

            fights.append(fight)
    
    event_details['fights'] = fights
    return event_details

def scrape_all_events():
    soup = get_soup(BASE_URL)
    events = []

    table = soup.find('table', class_='b-statistics__table-events')
    if not table:
        print("Could not find events table on the page.")
        return []

    event_rows = [row for row in table.find_all('tr', class_='b-statistics__table-row') if row.find('td')]
    total_events = len(event_rows)
    print(f"Found {total_events} events to scrape.")

    for i, row in enumerate(event_rows):
        event_link_tag = row.find('a', class_='b-link b-link_style_black')
        if not event_link_tag or not event_link_tag.has_attr('href'):
            continue
        
        event_url = event_link_tag['href']
        
        try:
            event_data = scrape_event_details(event_url)
            if event_data:
                events.append(event_data)
            
            print(f"Progress: {i}/{total_events} events scraped.")

            if (i + 1) % 10 == 0:
                print(f"--- Saving progress: {i + 1} of {total_events} events saved. ---")
                with open('ufc_events_detailed.json', 'w') as f:
                    json.dump(events, f, indent=4)
        except Exception as e:
            print(f"Could not process event {event_url}. Error: {e}")

    return events

if __name__ == "__main__":
    all_events_data = scrape_all_events()
    with open('ufc_events_detailed.json', 'w') as f:
        json.dump(all_events_data, f, indent=4)
    print("\nScraping complete. Final data saved to ufc_events_detailed.json")
