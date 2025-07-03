# UFC Scraper

Scrape ALL fight and fighter data from [ufcstats.com](http://ufcstats.com) up to the latest event and save them in `.csv` format

How? Clone the repo, then open a terminal in the root folder and run the following commands:

1. install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

2. Then run the main script:

```bash
python src/scrape/main.py
```
This command will execute the entire scraping process and save the final CSV files in the `output/` directory.
