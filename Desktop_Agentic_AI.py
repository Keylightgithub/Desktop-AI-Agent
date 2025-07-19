import pyautogui
import google.generativeai as genai
from PIL import Image
import os
import time
import subprocess
import re
import ast
from env import GOOGLE_API_KEY # Assuming env.py exists and contains GOOGLE_API_KEY

# Record the start time
start_time = time.time()

'''
How to use:
1. Add your Google/Gemini API key to env.py file
2. Only change the prompt Goal and Operating system in the prompt variable below.
3. Keep the window you want to automate as the second window behind the first one ex. google sheets behind VS code editor.

Description:
1. Once the script is ran, the script will hide the first window ex. vs code editor.
2. Next the second window behind the first will be screenshotted and sent with the prompt to the AI.
3. The AI will generate a list of steps to accomplish the goal.
4. The script parses the AI response and execute the steps using pyautogui.
5. The script filters out some letters from the results if conflicting with MacOS modifier keys.
6. The script executes the steps with a delay to allow for proper execution.

Note on Limitaions:
1. The AI will do based on 1 automated screenshot so if the window changes it won't work.
2. You will not be able to multitask while the script is running since the keyboard will in use.
3. Some keys are filtered out since MacOS may mistake them for modifier keys.
 - For example, 'm' and 'M' are filtered out from pyautogui commands
'''

operating_system = \
"""
MacOS
"""

goal = \
'''
In the selected cell(s) of the sheet, input a 3x3 sample realistic data entry.
'''

prompt = f"""
goal: {goal}
operating System: {operating_system}

Tasks:
1. Accomplish the goal using only pyautogui keys, hotkeys, and write (no clicks).
2. Plan out navigation steps completely based on image analysis.
3. Give the output in a list format and include the prefix pyautogui for each command.
4. Only give the list results, no extra.
"""

# macOS hotkey to hide VS Code window before next steps
pyautogui.keyDown('command')
pyautogui.press('h')
pyautogui.keyUp('command')

time.sleep(1)  # Wait a little to allow user to prepare the screen


# Configure Gemini API with key from env.py
genai.configure(api_key=GOOGLE_API_KEY)

# Take a screenshot directly into a PIL Image object in memory
screenshot_image = pyautogui.screenshot()

# Load the model that supports vision
model = genai.GenerativeModel('gemini-2.5-flash')

# Generate content from the image and a prompt
response = model.generate_content([prompt, screenshot_image])

print("Raw AI Response:\n" + response.text) # Print raw response for debugging

# Parse and execute steps from the AI response
def parse_steps(text):
    """
    Extracts pyautogui commands from the response.
    """
    print("\n--- Starting parse_steps function ---")
    text = text.strip()
    # Remove markdown code block fences if they exist
    if text.startswith('```') and text.endswith('```'):
        text = text.strip('`').strip()
        text = re.sub(r'^(python|py|text)\n', '', text, flags=re.IGNORECASE).strip()

    print(f"Cleaned Text for Parsing:\n{text}")

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
            print(f"--- Finished parse_steps. Total steps found: {len(steps)} ---")
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
        
        # MODIFIED LOGIC: Find 'pyautogui.' and slice from there.
        # This removes any leading characters like "- ".
        start_index = line.find('pyautogui.')
        if start_index != -1:
            command = line[start_index:]
            # Standardize typewrite to write if AI uses it
            command = command.replace('pyautogui.typewrite', 'pyautogui.write')
            print(f"Parsed Command: {command}")
            steps.append(command)
        else:
            print(f"  Line not matched (skipped, does not contain 'pyautogui.'): '{line}'")

    print(f"--- Finished parse_steps. Total steps found: {len(steps)} ---")
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
    """
    step = step.strip() # Ensure no leading/trailing whitespace

    # Attempt to parse the step string as a Python expression and execute it.
    # This directly calls pyautogui functions.
    try:
        # For pyautogui.write commands, we need to handle the argument specifically
        # because we want to apply the lowercasing and potentially use AppleScript.
        write_match = re.match(r"pyautogui\.write\((.*)\)", step)
        if write_match:
            # Release modifier keys before writing to prevent unintended shortcuts.
            for key in ['command', 'shift', 'option', 'ctrl', 'alt', 'fn']:
                pyautogui.keyUp(key)

            arg_str_raw = write_match.group(1)
            try:
                # Safely evaluate the argument string to get the actual Python string value
                arg_val = ast.literal_eval(arg_str_raw)
                
                if isinstance(arg_val, str):
                    # MODIFICATION: Removed .lower() to preserve original casing
                    text_to_write = arg_val 
                    print(f"  Text for writing: '{text_to_write}'")

                    if 'macos' in operating_system.lower():
                        execute_applescript_write(text_to_write)
                    else:
                        pyautogui.write(text_to_write, interval=0.05)
                else:
                    print(f"  Warning: Expected string for pyautogui.write, got {type(arg_val)}: {arg_val}")
            except (ValueError, SyntaxError) as err:
                print(f"Error parsing write arguments '{arg_str_raw}' during execution: {err}")
            return # Exit after handling pyautogui.write

        # For all other pyautogui commands (hotkey, press), directly execute them
        print(f"Executing: {step}")
        eval(step) # This is where pyautogui.press('enter'), pyautogui.hotkey('option', 'i') etc. will be executed.

    except Exception as e:
        print(f"Error executing step '{step}': {e}")
        # If eval fails for some reason, the previous regex-based parsing
        # and execution for hotkey/press might be a fallback, but ideally
        # direct eval should work if the string is a valid Python call.


# --- Main execution flow ---
steps = parse_steps(response.text)
print("\n--- Parsed pyautogui steps: ---")
if steps:
    for s in steps:
        print(f"  {s}")
else:
    print("No steps were parsed. Please check the AI response format and parsing logic.")
print("--- End of parsed steps ---")

print("\n--- Executing steps ---")
for step in steps:
    time.sleep(0.8)
    execute_step(step)
print("--- Finished execution ---")

# Calculate and print the total execution time
end_time = time.time()
execution_time = end_time - start_time
print(f"\nTotal execution time: {execution_time:.2f} seconds")

