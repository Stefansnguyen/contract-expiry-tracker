# Contract Expiry Tracker

A lightweight procurement tool that flags vendor contracts approaching expiry and generates
ready-to-send reminder emails, built to reduce missed renewal/renegotiation deadlines,
a common gap in manual contract management.

> **Note:** This is a portfolio project built against mock data for demonstration purposes.
> It is not connected to any live vendor or contract system.

## Why this exists

Missed contract renewal windows are a recurring, avoidable problem in procurement:
contracts auto-renew on unfavorable terms, or lapse entirely, simply because no one
was tracking the expiry date. This tool gives a quick, visual answer to
"what needs my attention this month?" and removes the manual step of drafting a
reminder email from scratch.

## What it does

- **Dashboard view**: counts of contracts expiring within 30 / 60 / 90 days, and already-expired contracts
- **Filterable table**: filter by vendor, contract type, or urgency level, color-coded by how soon action is needed
- **CSV in/out**: upload your own contract data, or generate example data to explore the tool; export the filtered view
- **Email draft generator**: select a contract and get a pre-filled reminder email (subject + body), editable and downloadable

## Tech stack

- Python
- Streamlit
- Pandas

## Data format

Upload a CSV with these columns:

| Column | Example |
|---|---|
| Vendor | Nordic Packaging AB |
| Contract Type | Serviceavtal |
| Start Date | 2023-01-15 |
| End Date | 2026-09-30 |
| Contract Value (SEK) | 250000 |
| Owner | Anna Berg |

Or just click **Generera exempeldata** in the app to explore it with realistic mock data.

## Run locally

```bash
pip install -r requirements.txt
streamlit run contract_tracker.py
```

## Possible next steps

- Connect to a live source (e.g. SharePoint list or ERP contract module) instead of manual CSV upload
- Trigger actual email sends via Power Automate instead of manual copy/download
- Add renewal-history tracking to flag vendors with a pattern of late renegotiation
