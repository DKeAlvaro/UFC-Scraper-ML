---
title: UFC Fight Predictor
emoji: 🥊
colorFrom: red
colorTo: blue
sdk: gradio
sdk_version: "4.28.3"
app_file: app.py
pinned: false
---
# UFC Scraper & ML

Scrape ALL fight and fighter data from [ufcstats.com](http://ufcstats.com) up to the latest event and save them in `.csv` format

How? Clone the repo, then open a terminal in the root folder and run the following commands:

1. Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

2. Then run the main script to scrape all data:

```bash
python -m src.scrape.main
```
This command will execute the entire scraping and processing pipeline, saving the final CSV files in the `output/` directory.

3. (Optional) Calculate fighter ELO ratings:

```bash
python -m src.analysis.elo
```
This updates `ufc_fighters.csv` with ELO scores and prints the top 10 fighters.

4. (Optional) Run the prediction pipeline:

```bash
python -m src.predict.main
```
This runs a baseline model to predict outcomes for the most recent fights and saves a detailed report in the `output/` directory.
