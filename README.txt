How to run script (MUST HAVE INSTALLED PYTHON 3 OR HIGHER):

Steps to setup initially (if you ran the startup_script.ps1 don't do this step):
- Change the proper credentials in config.json

- python -m venv scraping

- If you have Windows:
    - .\scraping\scripts\activate.ps1

- pip install -r requirements.txt


Steps to run the program:

- If you have Windows:
    - .\scraping\scripts\activate.ps1

- streamlit run main.py or python -m streamlit run main.py
