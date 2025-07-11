"""
This is the main entry point for the AI Web Scraper application.

This script initializes all the necessary components, including the Selenium
WebDriver, the configuration, and the Agent itself. It then starts the
agent on a specified target URL.
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# It's good practice to manage API keys via environment variables or a config file.
# For simplicity, we'll define it here for now.
# In a real application, use a library like 'python-dotenv' to load from a .env file.
# Create a 'config.py' file and add: GEMINI_API_KEY = "YOUR_API_KEY"
try:
    from config import GEMINI_API_KEY
except ImportError:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please set it in config.py or as an environment variable.")

from src.agent import Agent

def main():
    """
    The main function to set up and run the agent.
    """
    # --- Configuration ---
    # The URL of the website the agent should start on.
    # TODO: REPLACE WITH A REAL TARGET URL from your urls.xlsx file.
    target_url = "https://www.sme.in/Home/Index.htm" 

    # The high-level goal for the agent.
    goal = "Find the business or company directory on this website, navigate through it, and extract details of all companies listed, including their name, address, and any other available information."

    # --- WebDriver Setup ---
    print("[MAIN] > Setting up Selenium WebDriver...")
    try:
        # Using webdriver-manager to automatically handle the driver installation
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") # Run in headless mode (no GUI) for servers
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        print("[MAIN] > WebDriver setup complete.")
    except Exception as e:
        print(f"[MAIN] > Error setting up WebDriver: {e}")
        return

    # --- Agent Initialization and Execution ---
    try:
        # Initialize the agent, now passing the target_url
        agent = Agent(
            driver=driver, 
            gemini_api_key=GEMINI_API_KEY, 
            goal=goal,
            target_url=target_url # <-- FIX: Pass the URL to the agent
        )
        
        # Start the agent's run loop
        agent.run()

    except Exception as e:
        print(f"[MAIN] > An error occurred during the agent's run: {e}")
    finally:
        # --- Cleanup ---
        print("[MAIN] > Agent run finished. Closing WebDriver.")
        driver.quit()

if __name__ == "__main__":
    main()
