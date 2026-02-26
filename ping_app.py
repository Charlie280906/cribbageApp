import requests
import sys

# Replace with your actual Streamlit app URL
URL = "http://cribbageapp.streamlit.app/"

try:
    response = requests.get(URL)
    if response.status_code == 200:
        print(f"Successfully pinged {URL}")
    else:
        print(f"Ping failed with status code: {response.status_code}")
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
