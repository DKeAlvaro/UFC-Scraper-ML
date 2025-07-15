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
Always retrains all models from scratch with latest data.

### 3. Complete Pipeline

#### 2.1 Complete Pipeline
```bash
python -m src.main --pipeline all --scrape-mode update
```
Runs scraping (update mode), analysis, and prediction in sequence.

### 4. Model Updates Only

```bash
python -m src.main --pipeline update
```
Checks for new data and retrains models only if needed (perfect for automation).

## Model Performance

The system tests on the latest UFC event for realistic accuracy scores (typically 50-70% for fight prediction).

## Output

- **Data:** `output/ufc_fights.csv`, `output/ufc_fighters.csv`
- **Models:** `output/models/*.joblib`
- **Results:** `output/model_results.json`

## License

This project is licensed under the GNU Affero General Public License v3 (AGPL-3.0) - see the [LICENSE](LICENSE) file for details.

**What this means:**
- Free for personal, research, and educational use
- Can be modified and redistributed (with source code)
- **Network Copyleft**: If you run this as a web service or API, you must make your source code publicly available
- **Strong Copyleft**: Any modifications or derivative works must also be AGPL-3.0 licensed
- Commercial use is allowed but requires compliance with copyleft terms

This license specifically prevents companies from using this code in proprietary betting platforms or closed-source prediction services without contributing back to the open source community.
