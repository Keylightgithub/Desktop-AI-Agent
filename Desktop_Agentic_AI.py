import pyautogui
import google.generativeai as genai
from PIL import Image
import os
import time
import subprocess
import re
import ast
import sys
from env import GOOGLE_API_KEY # Assuming env.py exists and contains GOOGLE_API_KEY

goal = \
'''
In the selected cell(s) of the sheet, input a 4x4 sample realistic data entry.
'''


'''
How to use:
1. Install dependencies
1. Add your Google/Gemini API key to env.py file
2. Edit the above prompt "goal" variable to any request.
3. Keep the window you want to automate as the second window behind the first one ex. google sheets behind VS code editor.

Description:
1. Once the script is ran, the script will hide the first window ex. vs code editor.
2. Next the second window behind the first will be screenshotted and sent with the prompt to the AI.
3. The AI will generate a list of steps to accomplish the goal.
4. The script cleans & parses the AI response of pyautogui commands.
5. Pyautogui typing is converted to MacOS applescript typing to avoid accidental modifier keys activation.
6. The script executes the steps with a delay to allow for proper execution.

Note on Limitaions:
1. The AI will do based on 1 automated screenshot so if the window changes it won't work well.
2. You will not be able to multitask while the script is running since the keyboard will be in use.
'''


# -----------------------------------------------------------------------------------------

# Record the start time
start_time = time.time()

# --- Automatic Operating System Detection ---
# The script now automatically detects the OS using the sys library.
if sys.platform == 'darwin':
    operating_system = "MacOS"
elif sys.platform == 'win32':
    operating_system = "Windows"
else:
    # A general fallback for Linux and other Unix-like systems.
    operating_system = "Linux"
# --- End of Detection ---


prompt = f"""
goal: {goal}
operating System: {operating_system}

Tasks:
1. Accomplish the goal using only pyautogui keys, hotkeys, and write (no clicks).
2. Plan out navigation steps completely based on image analysis.
3. Give the output in a list format and include the prefix pyautogui for each command.
4. Only give the list results, no extra.
"""

# Check the operating system to perform OS-specific actions
if sys.platform == 'darwin':
    # macOS hotkey to hide the current window (e.g., VS Code) before next steps
    # Using keyDown and keyUp as requested for reliability.
    pyautogui.keyDown('command')
    pyautogui.press('h')
    pyautogui.keyUp('command')


time.sleep(1)  # Wait a little to allow user to prepare the screen


# Configure Gemini API with key from env.py
genai.configure(api_key=GOOGLE_API_KEY)

# ---- Timing the Screenshot ----
screenshot_start_time = time.time()
# Take a screenshot directly into a PIL Image object in memory
screenshot_image = pyautogui.screenshot()
screenshot_end_time = time.time()
screenshot_execution_time = screenshot_end_time - screenshot_start_time
print(f"--- Screenshot taken in {screenshot_execution_time:.4f} seconds ---")
# ---- END Timing the Screenshot ----


# Load the model that supports vision
model = genai.GenerativeModel('gemini-1.5-flash')

# ---- Timing the AI response ----
print(f"--- Requesting AI response for {operating_system}... ---")
ai_request_start_time = time.time()

# Generate content from the image and a prompt
response = model.generate_content([prompt, screenshot_image])

ai_request_end_time = time.time()

print("Raw AI Response:\n" + response.text) # Print raw response for debugging
ai_response_time = ai_request_end_time - ai_request_start_time
print(f"--- AI response received in {ai_response_time:.2f} seconds ---")
# ---- END Timing the AI response ----



# Parse and execute steps from the AI response
def parse_steps(text):
    """
    Extracts pyautogui commands from the AI's text response.
    This function no longer handles timing itself.
    """
    print("\n--- Starting step parsing ---")

    # ---- Timing the Cleaning Text ----
    clean_start_time = time.time()

    text = text.strip()
    # Remove markdown code block fences if they exist
    if text.startswith('```') and text.endswith('```'):
        text = text.strip('`').strip()
        text = re.sub(r'^(python|py|text)\n', '', text, flags=re.IGNORECASE).strip()

    # Print the result of the cleaning
    print(f"Cleaned Text for Parsing:\n{text}")

    clean_end_time = time.time()
    cleaned_text_time = clean_end_time - clean_start_time

    print(f"--- Time to clean text: {cleaned_text_time:.4f} seconds ---")
    # ---- END Timing the Cleaning Text ----

    steps = []

    # Attempt to parse as a Python list literal first (e.g., ['pyautogui.press("a")', ...])
    try:
        potential_list = ast.literal_eval(text)
        if isinstance(potential_list, list):
            print(f"Successfully evaluated list with {len(potential_list)} items.")
            # Ensure each item is a string and starts with 'pyautogui.'
            for s in potential_list:
                if isinstance(s, str) and s.startswith('pyautogui.'):
                    # Standardize typewrite to write if AI uses it
                    s = s.replace('pyautogui.typewrite', 'pyautogui.write')
                    steps.append(s)
                else:
                    print(f"  Skipping non-pyautogui string in list: '{s}'")
            return steps

    except (ValueError, SyntaxError):
        print("Not a Python list literal, falling back to line-by-line parsing.")
        pass # Fallback to line-by-line parsing if ast.literal_eval fails or not a list

    # Fallback: line-by-line parsing assuming each line is a direct command
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Find 'pyautogui.' and slice from there to remove leading characters.
        start_index = line.find('pyautogui.')
        if start_index != -1:
            command = line[start_index:]
            # Standardize typewrite to write if AI uses it
            command = command.replace('pyautogui.typewrite', 'pyautogui.write')
            steps.append(command)
        else:
            print(f"  Line not matched (skipped, does not contain 'pyautogui.'): '{line}'")

    print(f"--- Finished parsing. Total steps found: {len(steps)} ---")
    return steps

def execute_applescript_write(text_to_write):
    """
    Executes an AppleScript command to type the given text.
    """
    # Escape double quotes and backslashes for AppleScript
    escaped_text = text_to_write.replace("\\", "\\\\").replace('"', '\\"')
    applescript_command = f'tell application "System Events" to keystroke "{escaped_text}"'

    try:
        subprocess.run(["osascript", "-e", applescript_command], check=True)
        print(f"AppleScript Writing: {text_to_write}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing AppleScript: {e}")

def execute_step(step):
    """
    Execute a single step string, e.g. pyautogui.hotkey('command', 'l')
    This version now consistently uses pyautogui.write with an increased interval.
    On macOS, it uses AppleScript for writing.
    It also adds a delay if a URL is written.
    """
    step = step.strip() # Ensure no leading/trailing whitespace

    try:
        # Check if the step is a 'pyautogui.write()' command
        write_match = re.match(r"pyautogui\.write\((.*)\)", step)
        if write_match:
            # Release any held-down modifier keys before writing
            for key in ['command', 'shift', 'option', 'ctrl', 'alt', 'fn']:
                pyautogui.keyUp(key)

            arg_str_raw = write_match.group(1)
            try:
                # Safely evaluate the argument to get the actual string value
                arg_val = ast.literal_eval(arg_str_raw)

                if isinstance(arg_val, str):
                    text_to_write = arg_val

                    # Use the appropriate writing method based on OS
                    if sys.platform == 'darwin':
                        execute_applescript_write(text_to_write)
                    else:
                        pyautogui.write(text_to_write, interval=0.05)

                    # After writing, check if the text was a URL/domain. If so, wait.
                    common_tlds = (r'(com|net|org|gov|edu|io|co|uk|de|jp|ca|au|us|info|biz|dev'
                                   r'|app|ai|tech|online|store|blog|xyz|me|tv|solutions|expert)')
                    url_pattern = re.compile(
                        r'^(https?://|www\.)\S+|'  # Matches http://, https://, www.
                        r'(?:[^@\s]+\.)+' + common_tlds,  # Matches domain.com, sub.domain.co.uk, etc.
                        re.IGNORECASE
                    )

                    if url_pattern.search(text_to_write):
                        print("URL/Domain detected, added delay for page to load.")
                        time.sleep(5)

                else:
                    print(f"  Warning: Expected string for pyautogui.write, got {type(arg_val)}: {arg_val}")
            except (ValueError, SyntaxError) as err:
                print(f"Error parsing write arguments '{arg_str_raw}': {err}")
            return # End execution for this step after handling write

        # For all other commands (e.g., hotkey, press), execute directly
        print(f"Executing: {step}")
        eval(step)

    except Exception as e:
        print(f"Error executing step '{step}': {e}")


# --- Main execution flow ---

# ---- Timing the Parsing ----
parsing_start_time = time.time()

steps = parse_steps(response.text)

parsing_end_time = time.time()
parsing_time = parsing_end_time - parsing_start_time
# ---- END Timing the Parsing ----


# --- Print the parsed steps and then the time it took ---
print("\n--- Parsed pyautogui steps: ---")
if steps:
    for s in steps:
        print(f"  {s}")
else:
    print("No steps were parsed. Please check the AI response format and parsing logic.")
print("--- End of parsed steps ---")

# Now print the time it took to parse the steps, as requested.
print(f"--- Time to parse steps: {parsing_time:.4f} seconds ---")


print("\n--- Executing steps ---")
for step in steps:
    time.sleep(0.3) # Delay between each command
    execute_step(step)
print("--- Finished execution ---")

# Calculate and print the total execution time
end_time = time.time()
execution_time = end_time - start_time
print(f"\nTotal execution time: {execution_time:.2f} seconds")
