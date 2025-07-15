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
# UFC Scraper & ML [![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/AlvaroMros/ufc-predictor)

## Setup

1. Clone the repo (or download it), then open a terminal in the root folder

2. Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

## Usage

### 1. Data Scraping

**Initial Setup (First Time):**
```bash
python -m src.main --pipeline scrape --scrape-mode full
```
Scrapes all historical fight data from ufcstats.com.

**Update Data (Regular Use):**
```bash
python -m src.main --pipeline scrape --scrape-mode update
```
Adds only the latest events to existing data.

### 2. Fight Prediction

**Use Existing Models (Fast):**
```bash
python -m src.main --pipeline predict
```
Loads saved models if available and retrains if new data available.

**Force Retrain Models:**
```bash
python -m src.main --pipeline predict --force-retrain
```
Always retrains all models from scratch with latest data. This is useful for when the way training models changes

#### 2.1 Complete Pipeline
```bash
python -m src.main --pipeline all --scrape-mode update
```
Runs scraping (update mode), analysis, and prediction in sequence.

#### 2.2 Update Models
```bash
python -m src.main --pipeline update
```

## Model Performance

The system tests on the latest UFC event for realistic accuracy scores (typically 50-70% for fight prediction).

## Output

- **Data:** `output/ufc_fights.csv`, `output/ufc_fighters.csv`
- **Models:** `output/models/*.joblib`
- **Results:** `output/model_results.json`
