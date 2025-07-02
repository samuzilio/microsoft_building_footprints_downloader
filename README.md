# Microsoft Building Footprints Downloader
## Overview
This repository contains a script to download [Microsoft Building Footprints](https://github.com/microsoft/GlobalMLBuildingFootprints) for a specific municipality/region/country of the European Union. Boundaries are automatically obtained via [GISCO](https://ec.europa.eu/eurostat/web/gisco), through the [LAUs](https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/administrative-units-statistical-units/lau) or [NUTS](https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/administrative-units-statistical-units/nuts) dataset.

<br>

## Instructions
Follow these steps to set up and run the script on your local machine:

**1**. Clone the repository:
```
$ git clone https://github.com/samuzilio/microsoft_building_footprints_downloader.git
```
**2**. Launch your text editor;

**3**. Open the cloned repository;

**4**. Start a new terminal;

**5**. Create and activate a virtual environment:
```
$ python -m venv .venv
```
```
$ .venv\Scripts\activate (for Windows)
$ source .venv/bin/activate (for macOS and Linux)
```
**6**. Install dependencies:
```
$ pip install -r requirements.txt
```
**7**. Run the script (e.g. `downloader_lau.py`:
```
$ python downloader_lau.py
```
