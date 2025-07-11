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

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/AlvaroMros/ufc-predictor)

## Setup

1. Clone the repo (or download it), then open a terminal in the root folder

2. Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```
## Scraping:
Scrape ALL fight and fighter data from [ufcstats.com](http://ufcstats.com) up to the latest event and save them in `.csv` format 

2. Then run the main script to scrape all data:

```bash
python -m src.scrape.main
```
This command will execute the entire scraping and processing pipeline, saving the final CSV files in the `output/` directory.

## Train and save ML models:

This trains a different set of ML models and saves them in `output/models`.

```bash
python -m src.predict.main
```
