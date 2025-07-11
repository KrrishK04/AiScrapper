Project Plan: Autonomous AI Web Scraping Agent
Objective: To develop an autonomous AI agent that can navigate Indian state and union territory business directory websites, understand their structure, interact with forms, extract company data, and store it in a structured format (JSON/MongoDB).

Core Philosophy: We will build a true autonomous agent based on the OODA (Observe, Orient, Decide, Act) loop described in your inspiration document. The agent will not rely on a pre-baked plan but will instead reason about its next step at every stage, allowing it to learn and self-correct.

Phase 0: Foundation & Environment Setup
This phase is about getting the right tools and setting up the project for success.

Technology Stack:

Language: Python 3.9+

Web Interaction/Automation: Selenium. This is crucial because many government sites are old and rely heavily on JavaScript for form submissions and navigation (__doPostBack). Selenium can execute this JavaScript, which requests alone cannot.

HTML/XML Parsing: BeautifulSoup4. Excellent for parsing the HTML that Selenium retrieves.

LLM Interaction: Google Gemini API Client (google-generativeai). This will be the agent's "brain."

Data Structuring & Validation: Pydantic. This is non-negotiable. We will use it to define the "toolbox" of actions the agent can take and to structure the final extracted data, forcing the LLM to give us clean, predictable output.

Input Data: Pandas to read the list of URLs from your Excel sheet.

Data Storage: Start with the json library. Integrate pymongo later for MongoDB.

Project Structure:

/ai-web-scraper
|-- /src
|   |-- agent.py         # The core autonomous agent logic (OODA loop)
|   |-- toolbox.py       # Pydantic models for all possible actions
|   |-- executor.py      # Code to execute actions (e.g., Selenium clicks)
|   |-- main.py          # Orchestrator: reads URLs, runs agent for each
|-- config.py          # API keys, database URIs
|-- requirements.txt   # Project dependencies
|-- urls.xlsx          # Your input file
|-- /output
|   |-- company_data.json # Where the final data will be saved

Initial Setup:

Create a Python virtual environment.

Install all necessary libraries (pip install selenium beautifulsoup4 google-generativeai pydantic pandas openpyxl).

Set up your Google Gemini API key in a .env file or config.py.

Phase 1: The Core Agent Reasoning Loop (OODA)
This is the heart of the agent. We'll focus on making the agent "think" for a single website.

Observe:

The agent starts by navigating to a URL using Selenium.

The "Observe" step is to get the current state of the page: driver.page_source.

Clean the HTML to remove unnecessary tags (scripts, styles) to reduce the token count for the LLM.

Orient & Decide (The LLM Prompt):

This is the most critical step. We will craft a detailed prompt that gives the LLM all the context it needs to make one single, best next decision.

The Master Prompt Template:

You are an autonomous web scraping agent. Your primary goal is to find and extract information about companies (e.g., name, address, registration number) from this website.

You operate in a step-by-step manner. Based on the current state of the website and your history, you must decide on the single next action to take from the available tools.

**Overall Goal:** Find the page that lists companies and extract their data.
**History of Actions Taken:**
{history_of_actions}

**Current Page HTML (simplified):**
```html
{current_html}

Available Tools (Actions):
{json_schema_of_tools}

Based on everything you see, what is the single best action to take RIGHT NOW to move closer to the goal? Respond with only a single JSON object representing your chosen action.



Act:

The LLM will respond with a JSON object, e.g., {"action_name": "click_element", "parameters": {"css_selector": "a#nextPage"}}.

The executor.py module will parse this JSON. It will use a simple if/elif block or a dictionary to map the action_name to a Python function that performs the Selenium action.

Crucially, log everything to the terminal so you can see the agent's "thought process":

[AGENT] > Observing page: https://example.gov.in/search
[AGENT] > Sending context to LLM for decision...
[LLM]   > Decided action: {"action_name": "select_dropdown_option", "parameters": {"css_selector": "select#ddlDistrict", "value": "Ahmedabad"}}
[AGENT] > Executing action: Selecting "Ahmedabad" from dropdown "select#ddlDistrict".

Loop:

After the action is executed, the loop repeats. The agent gets the new page_source (Observe), appends the last action and its result to the history, and sends it all back to the LLM (Orient/Decide).

Phase 2: Defining the Agent's "Toolbox"
We'll use Pydantic to define all the actions the agent can possibly take. This gives the LLM clear, structured options.

In toolbox.py:

from pydantic import BaseModel, Field
from typing import Literal

class Navigate(BaseModel):
    action_name: Literal["navigate"] = "navigate"
    url: str = Field(description="The full URL to navigate to.")

class Click(BaseModel):
    action_name: Literal["click"] = "click"
    css_selector: str = Field(description="The CSS selector of the element to click.")

class FillField(BaseModel):
    action_name: Literal["fill_field"] = "fill_field"
    css_selector: str = Field(description="The CSS selector of the input field.")
    text: str = Field(description="The text to fill into the field.")

# This is the key lesson from the inspiration document!
class PerformPostback(BaseModel):
    action_name: Literal["perform_postback"] = "perform_postback"
    event_target: str = Field(description="The value for the __EVENTTARGET hidden field.")
    event_argument: str = Field(description="The value for the __EVENTARGUMENT hidden field.")

class ExtractData(BaseModel):
    action_name: Literal["extract_data"] = "extract_data"
    description: str = Field(description="A confirmation that the current page contains the target company data.")

class Finish(BaseModel):
    action_name: Literal["finish"] = "finish"
    reason: str = Field(description="Reason for finishing (e.g., 'Successfully extracted all data' or 'Reached a dead end').")

# We will generate a JSON schema from these models to include in the prompt.

Phase 3: Data Extraction & Self-Correction
This phase focuses on getting the final data and handling failures.

Triggering Extraction: The agent's loop continues until the LLM decides the current page contains the target data and returns the ExtractData action.

The Extraction Prompt: When the ExtractData action is chosen, the agent makes a different kind of LLM call.

Prompt: "You are a data extraction specialist. From the following HTML, extract all companies. Your output must be a JSON list, where each object conforms to this Pydantic schema: {company_schema}. Here is the HTML: {html_with_data}"

We will define a Company Pydantic model (name: str, address: str, etc.) to get structured output.

Saving Data: The agent receives the JSON list of companies, validates it with Pydantic, and appends it to output/company_data.json.

Self-Correction (The "Aha!" Moment):

The executor must have try...except blocks.

If an action fails (e.g., a click fails because the selector is wrong), we capture the error.

The result of the action is then added to the history: Action: Click(css_selector="#bad-id") -> Result: Failure (NoSuchElementException).

This failure context is sent to the LLM in the next loop. The prompt now implicitly asks, "I tried to do X, and it failed with Y. What should I do instead?"

This is how the agent learns that a simple link click might not work and that it needs to use PerformPostback instead.

Phase 4: Orchestration & Scaling
Now we make the agent work through the entire Excel sheet.

The Orchestrator (main.py):

Reads urls.xlsx into a Pandas DataFrame.

Loops through each URL.

For each URL, it initializes a new Agent instance (with a fresh history).

It runs the agent's main loop until the agent returns the Finish action.

Includes error handling for entire site failures and sets a maximum number of steps per site to prevent infinite loops and control costs.

Phase 5: Integration & Finalization
MongoDB Integration:

Modify the data-saving step in Phase 3.

Instead of writing to a JSON file, establish a connection to your MongoDB instance using pymongo.

Use insert_many() to save the list of company dictionaries directly into a collection.

Refinement and Monitoring:

Review the terminal logs to see where the agent is inefficient.

Refine the master prompt to give it better guidance or constraints.

Add cost-estimation logic by tracking token usage for each LLM call.

This plan provides a structured, phased approach to building a highly capable and intelligent scraping agent, directly incorporating the critical lessons learned from the GIDC case study.