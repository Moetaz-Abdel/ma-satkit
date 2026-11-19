# LEO Link Budget Toolkit (Streamlit)

Python port of `LEO_Toolkit.xlsx`.

## Files
- `app.py` - Streamlit user interface
- `linkbudget.py` - calculation engine (no Streamlit dependency)
- `test_linkbudget.py` - checks the engine against the workbook's values
- `requirements.txt`

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Deploy
Push these files to a GitHub repo, then on https://share.streamlit.io choose the repo and set
the main file to `app.py`.

## Test
    python test_linkbudget.py
