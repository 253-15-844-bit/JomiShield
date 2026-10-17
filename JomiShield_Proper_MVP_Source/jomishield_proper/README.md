# JomiShield MVP

JomiShield is a demonstration prototype for preliminary land-record comparison, map-based approximate area measurement, and discrepancy alerts.

## Features
- Overview dashboard
- Synthetic reference land records
- Add a synthetic parcel record
- Compare new values against a reference record
- Explainable discrepancy alerts and review history
- Interactive map polygon drawing and approximate area conversion
- SHA-256 file fingerprint utility

## Requirements
- Python 3.10 or newer recommended
- Internet access may be needed to install packages and load map tiles

## Run on Windows
1. Extract the ZIP.
2. Open the extracted `jomishield_proper` folder.
3. Click the folder address bar in File Explorer, type `cmd`, and press Enter.
4. Run:

```bash
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If `py` is not recognized, try `python` instead of `py`.

## Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local address, usually `http://localhost:8501`. Open it in your browser.

## Demo walkthrough
1. Open **Compare & Verify**.
2. Select `DHAKA-MOCK-001`.
3. Change area from `10` to `7` decimal and click **Compare records**.
4. Open **Alerts & History** to see the new discrepancy alert.
5. Open **Map & Area**, use the polygon drawing tool to click 3 or more points, and finish the polygon to see approximate area.
6. Open **Land Records** to add another synthetic parcel.

## Data and limitations
- Included data is synthetic demonstration data only.
- No live government record integration is included.
- A discrepancy is not proof of fraud or legal ownership.
- User-drawn map boundaries produce approximate measurements, not official cadastral surveys.
- Use only authorized data sources and do not upload real people's sensitive identifiers or private land records.
