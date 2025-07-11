"""
This module is the "hands" of the agent. It takes a structured Action
object from the toolbox and executes it using a Selenium WebDriver.
"""

import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Import the action definitions from our toolbox
from src.toolbox import (
    Action,
    Navigate,
    Click,
    FillField,
    SelectDropdown,
    PerformPostback,
    ExtractData,
    Finish
)

class ActionExecutor:
    """
    Executes actions on a web page using Selenium.
    """
    def __init__(self, driver: WebDriver):
        """
        Initializes the executor with a Selenium WebDriver instance.

        Args:
            driver: The Selenium WebDriver to interact with the browser.
        """
        self.driver = driver

    def execute(self, action: Action) -> str:
        """
        Executes a given action and returns a result message.

        This method acts as a dispatcher, calling the appropriate
        private method based on the type of action.

        Args:
            action: The Pydantic action object to execute.

        Returns:
            A string describing the outcome of the action (e.g., "Success" or an error message).
        """
        action_type = action.action_name
        print(f"[EXECUTOR] > Executing: {action.description}")
        
        try:
            if isinstance(action, Navigate):
                self._navigate(action)
            elif isinstance(action, Click):
                self._click(action)
            elif isinstance(action, FillField):
                self._fill_field(action)
            elif isinstance(action, SelectDropdown):
                self._select_dropdown(action)
            elif isinstance(action, PerformPostback):
                self._perform_postback(action)
            # The 'ExtractData' and 'Finish' actions don't manipulate the browser,
            # so they are handled by the agent loop directly. They are included
            # here to show they are valid actions.
            elif isinstance(action, (ExtractData, Finish)):
                return f"Action '{action_type}' acknowledged. No browser interaction needed."
            else:
                raise ValueError(f"Unknown action type: {action_type}")
            
            # Give the page a moment to load/react after an action
            time.sleep(2)
            return "Success"

        except (NoSuchElementException, TimeoutException) as e:
            error_message = f"Error executing {action_type}: Element not found with selector '{getattr(action, 'css_selector', 'N/A')}'. Details: {e.__class__.__name__}"
            print(f"[EXECUTOR] > {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred during {action_type}: {e}"
            print(f"[EXECUTOR] > {error_message}")
            return error_message

    def _navigate(self, action: Navigate):
        self.driver.get(action.url)

    def _click(self, action: Click):
        element = self.driver.find_element(By.CSS_SELECTOR, action.css_selector)
        element.click()

    def _fill_field(self, action: FillField):
        element = self.driver.find_element(By.CSS_SELECTOR, action.css_selector)
        element.clear()
        element.send_keys(action.text)

    def _select_dropdown(self, action: SelectDropdown):
        select_element = Select(self.driver.find_element(By.CSS_SELECTOR, action.css_selector))
        select_element.select_by_value(action.value)

    def _perform_postback(self, action: PerformPostback):
        # This is the key logic for handling ASP.NET PostBacks
        js_script = f"__doPostBack('{action.event_target}', '{action.event_argument}');"
        self.driver.execute_script(js_script)

 
