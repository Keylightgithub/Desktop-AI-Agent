import pyautogui
import google.generativeai as genai
from PIL import Image
import os
import time
from env import GOOGLE_API_KEY

'''
Note: some keys are filtered out since MacOS may mistake them for modifier keys.
For example, 'm' and 'M' are filtered out from pyautogui commands
'''

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
# No need to open a file, we pass the in-memory image object directly
prompt = """
goal: access the web address bar and search for a random realistic search query
Operating System: MacOS

Tasks:
1. plan out a list of steps to accomplish the goal using only pyautogui keys, hotkeys, and write.
2. Plan out navigation steps completely based on image analysis.
3. give the output in a list format and include the prefix pyautogui for each command.
4. only give the list results, no extra. no comments.
"""

response = model.generate_content([prompt, screenshot_image])

print(response.text)

# Parse and execute steps from the AI response
import re
import ast

def parse_steps(text):
    """
    Try to extract a Python list of pyautogui commands from the response.
    If not found, fallback to parsing numbered steps as strings.
    """
    # Remove code block formatting if present
    text = text.strip()
    if text.startswith('```') and text.endswith('```'):
        text = text.strip('`').strip()
        # Remove language identifier if present
        text = re.sub(r'^(python|py|text)\n', '', text, flags=re.IGNORECASE)

    # Try to find a Python list in the response
    list_match = re.search(r'\[.*?\]', text, re.DOTALL)
    steps = []
    def convert_typewrite_to_write(cmd):
        # Replace typewrite with write in pyautogui commands
        return re.sub(r'pyautogui\\.typewrite', 'pyautogui.write', cmd)

    if list_match:
        try:
            items = ast.literal_eval(list_match.group(0))
            if isinstance(items, list):
                for s in items:
                    if isinstance(s, str):
                        s = s.strip()
                        # Only keep pyautogui commands
                        if s.startswith('pyautogui.'):
                            s = convert_typewrite_to_write(s)
                            steps.append(s)
        except Exception:
            pass
    if not steps:
        # Fallback: parse lines for pyautogui commands or bare hotkey/write/press/typewrite
        lines = text.splitlines()
        for line in lines:
            # Match bullet points or numbered steps with pyautogui commands
            m = re.match(r'[-*]\s*`?(pyautogui\.[^`]+)`?', line)
            if m:
                cmd = convert_typewrite_to_write(m.group(1).strip())
                steps.append(cmd)
                continue
            # Also check for direct pyautogui commands in numbered steps
            m2 = re.match(r'\d+\.\s*`?(pyautogui\.[^`]+)`?', line)
            if m2:
                cmd = convert_typewrite_to_write(m2.group(1).strip())
                steps.append(cmd)
                continue
            # Now match for bare hotkey/write/press/typewrite (with or without backticks)
            m3 = re.match(r'.*`?(hotkey|write|press|typewrite)\(([^`]*)\)`?', line)
            if m3:
                func = m3.group(1)
                args = m3.group(2)
                # Convert typewrite to write
                if func == 'typewrite':
                    func = 'write'
                steps.append(f"pyautogui.{func}({args})")
        
    return steps

def execute_step(step):
    """
    Execute a single step string, e.g. pyautogui.hotkey('command', 'l')
    This version now consistently uses pyautogui.write with an increased interval.
    """
    # Filter out 'm' and 'M' from the step string before execution since Macos may mistake them for modifier keys
    filtered_step = "".join([char for char in step if char not in ('m', 'M')])
    
    # Remove any surrounding backticks or whitespace
    filtered_step = filtered_step.strip('`').strip()
    # Try to match pyautogui.hotkey, pyautogui.write, pyautogui.press
    hotkey_match = re.match(r"pyautogui\.hotkey\((.*)\)", filtered_step)
    write_match = re.match(r"pyautogui\.write\((.*)\)", filtered_step)
    press_match = re.match(r"pyautogui\.press\((.*)\)", filtered_step)

    if hotkey_match:
        args = ast.literal_eval(f'[{hotkey_match.group(1)}]')
        print(f"Executing hotkey (keydown for each, then keyup in reverse): {args}")
        # Press down all keys
        for key in args:
            pyautogui.keyDown(key)
        # Release all keys in reverse order
        for key in reversed(args):
            pyautogui.keyUp(key)
    elif write_match:
        # Check if the argument is a string before filtering
        arg_str = write_match.group(1)
        if arg_str.startswith("'") and arg_str.endswith("'"):
            # If it's a string literal, extract the content and filter
            original_content = arg_str.strip("'")
            filtered_content = "".join([char for char in original_content if char not in ('m', 'M')])
            arg = f"'{filtered_content}'" # Re-wrap in quotes
        else:
            # For non-string arguments, use as is (e.g., numbers, variables)
            arg = arg_str
            
        arg_eval = ast.literal_eval(f'[{arg}]')[0] # Evaluate to get the actual value
        print(f"Writing: {arg_eval}")
        # Use pyautogui.write with a consistent interval for all strings
        pyautogui.write(arg_eval, interval=0.05)
    elif press_match:
        # Extract arguments for pyautogui.press
        args_str = press_match.group(1)
        key = None
        presses = 1 # Default to 1 press

        # Use regex to find key and optional presses argument
        key_match = re.match(r"^\s*['\"]([^'\"]+)['\"]\s*(,\s*presses=(\d+))?$", args_str)
        if key_match:
            key = key_match.group(1)
            # Filter 'm' and 'M' from the key itself
            key = "".join([char for char in key if char not in ('m', 'M')])
            if key_match.group(3): # If presses argument exists
                presses = int(key_match.group(3))
        
        if key:
            print(f"Pressing: '{key}' {presses} time(s)")
            pyautogui.press(key, presses=presses)
        else:
            print(f"Could not parse pyautogui.press arguments: {filtered_step}")
    else:
        print(f"Unrecognized step: {filtered_step}")

steps = parse_steps(response.text)
print("\nParsed pyautogui steps:")
for s in steps:
    print(f"  {s}")
print()
for step in steps:
    time.sleep(0.8)
    execute_step(step)

