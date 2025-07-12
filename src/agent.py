"""
This module contains the core Agent class, which orchestrates the web
scraping process by implementing the OODA (Observe, Orient, Decide, Act) loop.
"""
import json
from typing import List, Dict, Any
from selenium.webdriver.remote.webdriver import WebDriver
from bs4 import BeautifulSoup
from pydantic_ai import Agent as PydanticAIAgent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from src.toolbox import Action, Finish, ExtractData, Navigate
from src.executor import ActionExecutor

# --- Pydantic models for data extraction ---
from pydantic import BaseModel, Field
from typing import List
import os
import asyncio
from datetime import datetime

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
        self.target_url = target_url
        self.max_steps = max_steps
        self.history: List[Dict[str, Any]] = []
        self.action_executor = ActionExecutor(driver)

        # Configure the PydanticAI client for decision making
        llm = GeminiModel(
            'gemini-1.5-flash',
            provider=GoogleGLAProvider(api_key=gemini_api_key)
        )
        self.decision_client = PydanticAIAgent(llm, result_type=Action)
        self.extraction_client = PydanticAIAgent(llm, result_type=CompanyList)


    def _clean_html(self, page_source: str) -> str:
        """Removes unnecessary tags to simplify HTML and reduce token count."""
        soup = BeautifulSoup(page_source, 'html.parser')
        for tag in soup(['script', 'style', 'svg', 'nav', 'footer', 'header']):
            tag.decompose()
        return str(soup.prettify())[:8000]

    def _construct_decision_prompt(self, simplified_html: str) -> str:
        """Constructs the prompt for the LLM to decide the next action."""
        return f"""
You are an autonomous web scraping agent. Your primary goal is: "{self.goal}".
You operate in a step-by-step manner. Based on the current state of the website and your history, you must decide on the single best action to take RIGHT NOW to move closer to the goal.

**History of Actions Taken & Results:**
{json.dumps(self.history, indent=2)}

**Current Page HTML (simplified):**
```html
{simplified_html}
```
"""

    def _construct_extraction_prompt(self, simplified_html: str) -> str:
        """Constructs the prompt for extracting structured data from a page."""
        return f"""
You are a data extraction specialist. From the following HTML, extract all companies.
Here is the HTML:
```html
{simplified_html}
```
"""
    def _get_action_description(self, action: Action) -> str:
        """Generates a human-readable description of an action for logging."""
        if hasattr(action, 'description'):
            return action.description
        elif isinstance(action, Navigate):
            return f"Navigate to {action.url}"
        elif isinstance(action, Finish):
            return action.reason
        return "No description available."

    async def run(self):
        """Starts the main OODA loop of the agent."""
        print(f"[AGENT] > Starting run. Navigating to initial URL: {self.target_url}")
        self.driver.get(self.target_url)

        os.makedirs('logs/sent', exist_ok=True)
        os.makedirs('logs/received', exist_ok=True)

        for step in range(self.max_steps):
            print(f"--- Step {step + 1}/{self.max_steps} ---")

            # 1. OBSERVE
            print(f"[AGENT] > Observing page: {self.driver.current_url}")
            page_source = self.driver.page_source
            simplified_html = self._clean_html(page_source)

            # 2. ORIENT & DECIDE
            print("[AGENT] > Sending context to LLM for decision...")
            decision_prompt = self._construct_decision_prompt(simplified_html)

            # Log sent message
            sent_filename = f"logs/sent/{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_step{step+1}.txt"
            with open(sent_filename, 'w', encoding='utf-8') as f:
                f.write(decision_prompt)

            try:
                result = await self.decision_client.run(decision_prompt)
                action = result.output
                # Log received message
                received_filename = f"logs/received/{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_step{step+1}.txt"
                with open(received_filename, 'w', encoding='utf-8') as f:
                    f.write(str(result))
                action_description = self._get_action_description(action)
                print(f"[LLM]   > Decided action: {action.action_name} - {action_description}")

            except Exception as e:
                print(f"[AGENT] > Error processing LLM response: {e}. Attempting to recover.")
                self.history.append({"action": "LLM_Error", "result": str(e)})
                continue

            # 3. ACT
            if isinstance(action, Finish):
                print(f"[AGENT] > Finishing run. Reason: {action.reason}")
                break

            if isinstance(action, ExtractData):
                print("[AGENT] > Extraction action triggered. Querying LLM for data...")
                extraction_prompt = self._construct_extraction_prompt(simplified_html)
                # Log sent extraction prompt
                sent_filename = f"logs/sent/{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_extract_step{step+1}.txt"
                with open(sent_filename, 'w', encoding='utf-8') as f:
                    f.write(extraction_prompt)
                try:
                    extracted_data_result = await self.extraction_client.run(extraction_prompt)
                    extracted_data = extracted_data_result.output
                    # Log received extraction data
                    received_filename = f"logs/received/{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_extract_step{step+1}.txt"
                    with open(received_filename, 'w', encoding='utf-8') as f:
                        f.write(str(extracted_data_result))
                    print(f"[LLM]   > Extracted {len(extracted_data.companies)} companies.")
                    result = f"Successfully extracted {len(extracted_data.companies)} companies."
                except Exception as e:
                    print(f"[AGENT] > Data extraction failed: {e}")
                    result = f"Data extraction failed: {e}"
            else:
                result = self.action_executor.execute(action)

            # 4. LOOP (Update history)
            self.history.append({"action": action.model_dump(), "result": result})

        else:
            print("[AGENT] > Reached max steps. Ending run.")