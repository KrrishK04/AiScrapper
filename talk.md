Step 1: Create the Project Directory Structure
Open your terminal and run these commands one by one.

Bash

# Create the main project folder
mkdir ai-web-scraper

# Navigate into the new folder
cd ai-web-scraper

# Create the 'src' and 'output' subdirectories
mkdir src
mkdir output
Step 2: Create the Initial Python and Config Files
Now, let's create all the empty files we'll need.

Bash

# Create the Python files inside the 'src' directory
touch src/agent.py
touch src/toolbox.py
touch src/executor.py
touch src/main.py

# Create the configuration file in the main directory
touch config.py
Step 3: Create the Requirements File
This command will create a requirements.txt file and populate it with the libraries we need.

Bash

# Create and write to the requirements.txt file
echo -e "selenium\nbeautifulsoup4\ngoogle-generativeai\npydantic\npandas\nopenpyxl" > requirements.txt
Step 4: Set Up the Python Virtual Environment
It's best practice to isolate our project's dependencies.

Bash

# Create a virtual environment named 'venv'
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows (Command Prompt/PowerShell):
# venv\Scripts\activate
You should see (venv) at the beginning of your terminal prompt, indicating the environment is active.

Step 5: Install the Dependencies
Now, let's install all the libraries we listed in requirements.txt.

Bash

# Install the libraries using pip
pip install -r requirements.txt
Congratulations! You have successfully completed Phase 0. Your project structure is now identical to the plan, and you have a clean, isolated environment with all the necessary tools installed.

Your ai-web-scraper directory should now look like this:

/ai-web-scraper
|-- /src
|   |-- agent.py
|   |-- toolbox.py
|   |-- executor.py
|   |-- main.py
|-- /output
|-- config.py
|-- requirements.txt
|-- /venv
Our next step will be to populate config.py with your Gemini API key and start building the "Toolbox" in src/toolbox.py as outlined in Phase 2. Ready for the next step?