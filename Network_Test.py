import os
from dotenv import load_dotenv
from urllib.request import urlopen
import socket

# --- SCRIPT SETUP ---
print("--- Attempting to load .env file from the correct directory... ---")
# This specifically loads the .env file from the Backend folder
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
print(f"--- Loaded AUTH0_DOMAIN value is: '{AUTH0_DOMAIN}' ---")

# --- THE TEST ---
if not AUTH0_DOMAIN:
    print("\n--- TEST RESULT ---")
    print("❌ Failure! The AUTH0_DOMAIN environment variable was not found.")
    print("   Please check that your .env file is in the 'Backend' folder and the variable name is correct.")
    print("--- END OF TEST ---")
else:
    url_to_test = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    print(f"\n--- Attempting to connect to: {url_to_test} ---")
    try:
        response = urlopen(url_to_test, timeout=10)
        if response.getcode() == 200:
            print("\n--- TEST RESULT ---")
            print("✅ Success! The connection to the Auth0 server was successful.")
            print("   This means your .env file is correct and your internet connection is working for this script.")
            print("--- END OF TEST ---")
        else:
            print(f"\n--- TEST RESULT ---\n❌ Failure! Received an unexpected status code: {response.getcode()}")
    except (socket.gaierror, Exception) as e:
        print("\n--- TEST RESULT ---")
        print(f"❌ Failure! The connection failed with an error: {e}")
        print("   This confirms a network issue. It could be a firewall blocking Python, a DNS problem, or an incorrect AUTH0_DOMAIN value.")
        print("--- END OF TEST ---")
