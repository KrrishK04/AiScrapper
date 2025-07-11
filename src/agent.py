"""
This module contains the core Agent class, which orchestrates the web
scraping process by implementing the OODA (Observe, Orient, Decide, Act) loop.
"""

import json
from typing import List, Dict, Any
from selenium.webdriver.remote.webdriver import WebDriver
from bs4 import BeautifulSoup
import google.generativeai as genai
from pydantic import ValidationError

from src.toolbox import Action, Finish, ExtractData, PerformPostback, Click, FillField, SelectDropdown, Navigate
from src.executor import ActionExecutor

# --- Pydantic models for data extraction ---
from pydantic import BaseModel, Field
from typing import List

class Company(BaseModel):
    """Pydantic model to structure the extracted company data."""
    company_name: str = Field(..., description="The full, official name of the company.")
    address: str = Field(..., description="The registered address of the company.")
    registration_number: str = Field(None, description="The official registration number, if available.")
    other_details: Dict[str, Any] = Field({}, description="A dictionary for any other relevant details found.")

class CompanyList(BaseModel):
    """A list of companies, used for validating the LLM's extraction output."""
    companies: List[Company]

class Agent:
    """
    The autonomous agent that navigates and scrapes websites.
    """
    def __init__(self, driver: WebDriver, gemini_api_key: str, goal: str, target_url: str, max_steps: int = 20):
        """
        Initializes the Agent.

        Args:
            driver: The Selenium WebDriver instance.
            gemini_api_key: Your Google Gemini API key.
            goal: The high-level objective for the agent.
            target_url: The starting URL for the agent.
            max_steps: The maximum number of steps the agent can take to prevent infinite loops.
        """
        self.driver = driver
        self.goal = goal
        self.target_url = target_url # <-- FIX: Store the target URL
        self.max_steps = max_steps
        self.history: List[Dict[str, Any]] = []
        self.action_executor = ActionExecutor(driver)
        
        # Configure the Gemini client
        genai.configure(api_key=gemini_api_key)
        # --- FIX: Using a known stable model name ---
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # Generate the JSON schema for the toolbox to be used in the prompt
        self.toolbox_schema = self._generate_toolbox_schema()

    def _generate_toolbox_schema(self) -> str:
        """Generates a JSON schema from the Action Union type for the LLM."""
        schemas = [m.model_json_schema() for m in Action.__args__]
        return json.dumps(schemas, indent=2)

    def _clean_html(self, page_source: str) -> str:
        """Removes unnecessary tags to simplify HTML and reduce token count."""
        soup = BeautifulSoup(page_source, 'html.parser')
        for tag in soup(['script', 'style', 'svg', 'nav', 'footer', 'header']):
            tag.decompose()
        return str(soup.prettify())[:8000]

    def _get_decision_prompt(self, simplified_html: str) -> str:
        """Constructs the main prompt for the LLM to decide the next action."""
        return f"""
You are an autonomous web scraping agent. Your primary goal is: "{self.goal}".
You operate in a step-by-step manner. Based on the current state of the website and your history, you must decide on the single next action to take from the available tools.

**History of Actions Taken & Results:**
{json.dumps(self.history, indent=2)}

**Current Page HTML (simplified):**
```html
{simplified_html}
```

**Available Tools (Actions) JSON Schema:**
{self.toolbox_schema}

Based on everything you see, what is the single best action to take RIGHT NOW to move closer to the goal?
Your response MUST be a single JSON object that validates against one of the schemas in the 'Available Tools'.
Do not add any commentary or markdown formatting. Just the JSON object.
"""

    def _get_extraction_prompt(self, simplified_html: str) -> str:
        """Constructs the prompt for extracting structured data from a page."""
        company_schema = CompanyList.model_json_schema()
        return f"""
You are a data extraction specialist. From the following HTML, extract all companies.
Your output must be a single JSON object that conforms to this schema:
{json.dumps(company_schema, indent=2)}

Here is the HTML:
```html
{simplified_html}
```
Respond with only the JSON object containing the list of companies.
"""

    def run(self):
        """Starts the main OODA loop of the agent."""
        # --- FIX: Perform initial navigation BEFORE the loop starts ---
        print(f"[AGENT] > Starting run. Navigating to initial URL: {self.target_url}")
        self.driver.get(self.target_url)
        
        for step in range(self.max_steps):
            print(f"\n--- Step {step + 1}/{self.max_steps} ---")
            
            # 1. OBSERVE
            print(f"[AGENT] > Observing page: {self.driver.current_url}")
            page_source = self.driver.page_source
            simplified_html = self._clean_html(page_source)

            # 2. ORIENT & DECIDE
            print("[AGENT] > Sending context to LLM for decision...")
            decision_prompt = self._get_decision_prompt(simplified_html)
            
            try:
                response = self.model.generate_content(decision_prompt)
                action_json_str = response.text.strip().replace('```json', '').replace('```', '')
                action_data = json.loads(action_json_str)
                action = Action.model_validate(action_data)
                print(f"[LLM]   > Decided action: {action.action_name} - {action.description}")

            except (json.JSONDecodeError, ValidationError, Exception) as e:
                print(f"[AGENT] > Error processing LLM response: {e}. Attempting to recover.")
                self.history.append({"action": "LLM_Error", "result": str(e)})
                continue

            # 3. ACT
            if isinstance(action, Finish):
                print(f"[AGENT] > Finishing run. Reason: {action.reason}")
                break

            if isinstance(action, ExtractData):
                print("[AGENT] > Extraction action triggered. Querying LLM for data...")
                extraction_prompt = self._get_extraction_prompt(simplified_html)
                try:
                    extraction_response = self.model.generate_content(extraction_prompt)
                    extraction_json_str = extraction_response.text.strip().replace('```json', '').replace('```', '')
                    extracted_data = CompanyList.model_validate_json(extraction_json_str)
                    print(f"[LLM]   > Extracted {len(extracted_data.companies)} companies.")
                    result = f"Successfully extracted {len(extracted_data.companies)} companies."
                except (json.JSONDecodeError, ValidationError, Exception) as e:
                    print(f"[AGENT] > Data extraction failed: {e}")
                    result = f"Data extraction failed: {e}"
            else:
                result = self.action_executor.execute(action)

            # 4. LOOP (Update history)
            self.history.append({"action": action.model_dump(), "result": result})

        else:
            print("[AGENT] > Reached max steps. Ending run.")
