"""
This module defines the 'toolbox' for the AI agent.

Each class represents a single, executable action the agent can decide to take.
Pydantic is used to enforce a strict schema for each action, ensuring that
the LLM's output is predictable and can be reliably parsed and executed.
"""

from pydantic import BaseModel, Field
from typing import Literal, Union

# --- Action Definitions ---

class Navigate(BaseModel):
    """Navigates the browser to a specific URL."""
    action_name: Literal["navigate"] = "navigate"
    url: str = Field(..., description="The full URL to navigate to.")

class Click(BaseModel):
    """Performs a click on a web element."""
    action_name: Literal["click"] = "click"
    css_selector: str = Field(..., description="The CSS selector to identify the clickable element (e.g., 'a#login-button').")
    description: str = Field(..., description="A brief, human-readable description of the element being clicked, for logging purposes (e.g., 'Click on the main login button').")

class FillField(BaseModel):
    """Fills an input field with specified text."""
    action_name: Literal["fill_field"] = "fill_field"
    css_selector: str = Field(..., description="The CSS selector for the input field (e.g., 'input[name=\"username\"]').")
    text: str = Field(..., description="The text to fill into the field.")
    description: str = Field(..., description="A brief description of the field being filled (e.g., 'Entering the username').")

class SelectDropdown(BaseModel):
    """Selects an option from a dropdown menu."""
    action_name: Literal["select_dropdown"] = "select_dropdown"
    css_selector: str = Field(..., description="The CSS selector for the <select> element.")
    value: str = Field(..., description="The 'value' attribute of the <option> to select.")
    description: str = Field(..., description="A brief description of the selection being made (e.g., 'Selecting Gujarat from the state dropdown').")

class PerformPostback(BaseModel):
    """
    Executes a JavaScript __doPostBack, common in older ASP.NET sites.
    This is a critical tool for handling non-standard navigation.
    """
    action_name: Literal["perform_postback"] = "perform_postback"
    event_target: str = Field(..., description="The value for the __EVENTTARGET hidden field, indicating which control triggered the postback.")
    event_argument: str = Field(..., description="The value for the __EVENTARGUMENT hidden field, providing additional data for the event.")
    description: str = Field(..., description="A brief description of the postback action (e.g., 'Triggering postback for the search button').")

class ExtractData(BaseModel):
    """
    A special action indicating the agent believes the current page contains
    the target company data and that extraction should now be attempted.
    """
    action_name: Literal["extract_data"] = "extract_data"
    description: str = Field(..., description="A confirmation that the current page contains the target company data and is ready for extraction.")

class Finish(BaseModel):
    """
    The final action, used when the agent concludes its work on a site,
    either successfully or because it's stuck.
    """
    action_name: Literal["finish"] = "finish"
    reason: str = Field(..., description="The reason for finishing (e.g., 'Successfully extracted all data and navigated all pages' or 'Reached a dead end with no further actions possible').")


# --- Union Type for Dispatching ---

# This Union type allows Pydantic to automatically determine which action
# the LLM has chosen based on the 'action_name' field.
Action = Union[
    Navigate,
    Click,
    FillField,
    SelectDropdown,
    PerformPostback,
    ExtractData,
    Finish
]
 
