import pyautogui
import google.generativeai as genai
from PIL import Image
import time
import subprocess
import re
import ast
import sys
try:
    from env import GOOGLE_API_KEY
except ImportError:
    print("Error: 'env.py' file not found. Please create it and add your GOOGLE_API_KEY.")
    sys.exit(1)


goal = \
'''
In this google doc, solve the question(s)
'''


'''
How to use:
1. Install dependencies
2. Add your Google/Gemini API key to env.py file
3. Edit the above prompt "goal" variable to any request.
4. Keep the window you want to automate as the second window behind the first one ex. google sheets behind VS code editor.

Description:
1. On run, the script will hide the first window ex. vs code editor.
2. After hiding, the second will be screenshotted and sent with the prompt "goal" to the AI.
3. The AI will generate a list of steps to accomplish the goal.
4. The script cleans & parses the AI response of pyautogui commands.
5. Pyautogui typing is converted to MacOS applescript typing to avoid accidental modifier keys activation.
6. The script executes the steps with an editable delay to allow for proper execution.

Note on Limitaions:
1. The AI will do based on 1 automated screenshot so if the window changes it won't work well.
2. You will not be able to multitask while the script is running since the keyboard will be in use.
'''


# -----------------------------------------------------------------------------------------

# Record the start time
start_time = time.time()

# --- Unified Editable Delay ---
# This single value (in seconds) controls the delay AFTER each command is executed.
# For individual and multi-press commands (e.g., presses=3), this same delay is also applied
STEP_DELAY = 0.1 # Editable: change this value to control the overall script speed. (Recommended: 0.1)
# --- End of delay configuration ---


# --- Automatic Operating System Detection ---
# The script now automatically detects the OS using the sys library.
IS_MACOS = sys.platform == 'darwin'

if IS_MACOS:
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
if IS_MACOS:
    # macOS hotkey to hide the current window (e.g., VS Code) before next steps
    # Using AppleScript for reliability on macOS.
    subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "h" using command down'])


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
model = genai.GenerativeModel('gemini-2.5-flash')

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


# --- (FIXED) AppleScript Key Code Map for Special Keys ---
# Using key codes is more reliable for hotkeys and non-character keys.
# This map is based on the US QWERTY layout.
KEY_CODE_MAP = {
    # Alphanumeric
    'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5, 'h': 4, 'i': 34,
    'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45, 'o': 31, 'p': 35, 'q': 12,
    'r': 15, 's': 1, 't': 17, 'u': 32, 'v': 9, 'w': 13, 'x': 7, 'y': 16, 'z': 6,
    '0': 29, '1': 18, '2': 19, '3': 20, '4': 21, '5': 23, '6': 22, '7': 26,
    '8': 28, '9': 25,
    # Symbols
    '=': 24, '-': 27, '[': 33, ']': 30, '\\': 42, ';': 41, "'": 39, ',': 43,
    '.': 47, '/': 44, '`': 50,
    # Special Keys
    'enter': 36, 'return': 36,
    'tab': 48,
    'space': 49,
    'delete': 51,  # backspace
    'escape': 53, 'esc': 53,
    # Arrow Keys
    'left': 123,
    'right': 124,
    'down': 125,
    'up': 126,
}

def pyautogui_to_applescript(command):
    """
    (FIXED) Converts a PyAutoGUI command string to its AppleScript equivalent.
    Handles key presses, hotkeys (prioritizing key codes), and text writing.
    """
    # Hotkeys with modifiers: pyautogui.hotkey('mod1', 'mod2', 'key')
    hotkey_match = re.match(r"pyautogui\.hotkey\((.*)\)", command)
    if hotkey_match:
        keys = [k.strip().strip("'\"") for k in hotkey_match.group(1).split(',')]
        if not keys: return None
        
        key_press = keys[-1]
        modifiers = keys[:-1]
        
        modifier_map = {'command': 'command', 'cmd': 'command', 'ctrl': 'control', 'alt': 'option', 'shift': 'shift'}
        active_modifiers = [modifier_map[mod] for mod in modifiers if mod in modifier_map]
        mod_string = " using {" + ", ".join(f'{mod} down' for mod in active_modifiers) + "}" if active_modifiers else ""
        
        key_lower = key_press.lower()
        # For hotkeys, always prefer key code if available for reliability
        if key_lower in KEY_CODE_MAP:
            key_action = f"key code {KEY_CODE_MAP[key_lower]}"
        else:
            # Fallback to keystroke for unmapped keys
            escaped_key = key_press.replace("\\", "\\\\").replace('"', '\\"')
            key_action = f'keystroke "{escaped_key}"'
            
        return f'tell application "System Events" to {key_action}{mod_string}'

    # Key presses (including multiple presses)
    press_match = re.match(r"pyautogui\.press\((.*)\)", command)
    if press_match:
        arg_str = press_match.group(1).strip()
        
        try:
            args = [arg.strip() for arg in arg_str.split(',')]
            if not args or not args[0]: return None
            key = args[0].strip("'\"")
            presses = 1
            if len(args) > 1:
                presses_arg = args[1]
                if 'presses=' in presses_arg:
                    presses = int(presses_arg.split('=')[1].strip())
                else:
                    presses = int(presses_arg)
        except (ValueError, IndexError):
            key = arg_str.strip("'\"")
            presses = 1

        key_lower = key.lower()
        if key_lower in KEY_CODE_MAP:
            key_action = f"key code {KEY_CODE_MAP[key_lower]}"
        else:
            escaped_key = key.replace("\\", "\\\\").replace('"', '\\"')
            key_action = f'keystroke "{escaped_key}"'
        
        if presses > 1:
            repeat_block = (f'repeat {presses - 1} times\n'
                            f'\t{key_action}\n'
                            f'\tdelay {STEP_DELAY}\n'
                            f'end repeat\n'
                            f'{key_action}')
            return f'tell application "System Events"\n{repeat_block}\nend tell'
        else:
            return f'tell application "System Events" to {key_action}'

    # Text writing
    write_match = re.match(r"pyautogui\.write\((.*)\)", command)
    if write_match:
        arg_str_raw = write_match.group(1)
        try:
            text_to_write = ast.literal_eval(arg_str_raw)
            if isinstance(text_to_write, str):
                escaped_text = text_to_write.replace("\\", "\\\\").replace('"', '\\"')
                return f'tell application "System Events" to keystroke "{escaped_text}"'
        except (ValueError, SyntaxError):
            return None

    return None


# Parse and execute steps from the AI response
def parse_steps(text):
    """
    Cleans and parses the AI's text response into a structured list of commands.
    Performs pre-formatting for AppleScript and URL detection during parsing to
    optimize the execution loop.
    """
    print("\n--- Starting step parsing and pre-processing ---")
    clean_start_time = time.time()

    text = text.strip()
    if text.startswith('```') and text.endswith('```'):
        text = text.strip('`').strip()
        text = re.sub(r'^(python|py|text)\n', '', text, flags=re.IGNORECASE).strip()

    print(f"Cleaned Text for Parsing:\n{text}")
    clean_end_time = time.time()
    print(f"--- Time to clean text: {clean_end_time - clean_start_time:.4f} seconds ---")

    common_tlds = (r'(com|net|org|gov|edu|io|co|uk|de|jp|ca|au|us|info|biz|dev'
                   r'|app|ai|tech|online|store|blog|xyz|me|tv|solutions|expert)')
    url_pattern = re.compile(
        r'^(https?://|www\.)\S+|'
        r'(?:[^@\s]+\.)+' + common_tlds,
        re.IGNORECASE
    )

    raw_commands = []
    try:
        potential_list = ast.literal_eval(text)
        if isinstance(potential_list, list):
            print(f"Successfully evaluated list with {len(potential_list)} items.")
            for s in potential_list:
                if isinstance(s, str) and s.startswith('pyautogui.'):
                    raw_commands.append(s.replace('pyautogui.typewrite', 'pyautogui.write'))
                else:
                    print(f"  Skipping non-pyautogui string in list: '{s}'")
        else:
            raise ValueError("Parsed literal is not a list.")
    except (ValueError, SyntaxError):
        print("Not a valid Python list literal, falling back to line-by-line parsing.")
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if not line: continue
            start_index = line.find('pyautogui.')
            if start_index != -1:
                command = line[start_index:]
                raw_commands.append(command.replace('pyautogui.typewrite', 'pyautogui.write'))
            else:
                print(f"  Line not matched (skipped, does not contain 'pyautogui.'): '{line}'")

    structured_steps = []
    for command in raw_commands:
        step_details = {'original_command': command, 'type': 'other', 'is_url': False}
        
        if IS_MACOS:
            applescript_cmd = pyautogui_to_applescript(command)
            if applescript_cmd:
                step_details['applescript_command'] = applescript_cmd
                step_details['type'] = 'applescript'

        write_match = re.match(r"pyautogui\.write\((.*)\)", command)
        if write_match:
            arg_str_raw = write_match.group(1)
            try:
                text_to_write = ast.literal_eval(arg_str_raw)
                if isinstance(text_to_write, str) and url_pattern.search(text_to_write):
                    step_details['is_url'] = True
            except (ValueError, SyntaxError):
                pass

        structured_steps.append(step_details)

    print(f"--- Finished parsing and pre-processing. Total steps: {len(structured_steps)} ---\n")
    return structured_steps


def execute_applescript_command(applescript_command, original_command):
    """
    Executes a pre-formatted AppleScript command.
    """
    try:
        if "repeat" in applescript_command:
            match = re.search(r"presses=(\d+)\)", original_command)
            if match:
                presses = match.group(1)
                key_match = re.search(r"press\((['\"])(.*?)\1", original_command)
                key = key_match.group(2) if key_match else "key"
                print(f"Executing (AppleScript): Pressing '{key}' {presses} times with a {STEP_DELAY}s delay between each press.")
            else:
                 print(f"Executing (AppleScript): {original_command}")
        else:
            print(f"Executing (AppleScript): {original_command}")
        
        subprocess.run(["osascript", "-e", applescript_command], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing AppleScript for command '{original_command}': {e}")


def execute_step(step):
    """
    Executes a single pre-processed step, handling delays for multi-press commands
    on any operating system.
    """
    original_command = step['original_command']

    if IS_MACOS and step['type'] == 'applescript':
        execute_applescript_command(step['applescript_command'], original_command)
    else:
        # For non-macOS, or if AppleScript conversion failed, handle execution here.
        is_multi_press = False
        press_match = re.match(r"pyautogui\.press\((.*)\)", original_command)
        
        if press_match:
            try:
                arg_str = press_match.group(1).strip()
                args = [arg.strip() for arg in arg_str.split(',')]
                presses = 1
                if len(args) > 1:
                    presses_arg = args[1]
                    if 'presses=' in presses_arg:
                        presses = int(presses_arg.split('=')[1].strip())
                    else:
                        presses = int(presses_arg)
                
                if presses > 1:
                    is_multi_press = True
                    key = ast.literal_eval(args[0])

                    print(f"Executing (Looped): Pressing '{key}' {presses} times with a {STEP_DELAY}s delay between each press.")
                    # Loop for (presses - 1) to insert delays between them
                    for _ in range(presses - 1):
                        pyautogui.press(key)
                        time.sleep(STEP_DELAY)
                    pyautogui.press(key) # The final press
            except (ValueError, IndexError, SyntaxError):
                is_multi_press = False # Fallback on parsing error

        if not is_multi_press:
            # If it's not a multi-press command, execute it directly
            try:
                print(f"Executing: {original_command}")
                eval(original_command, {"pyautogui": pyautogui})
            except Exception as e:
                print(f"Error executing step '{original_command}': {e}")

    if step.get('is_url'):
        print("URL/Domain detected, adding extra delay for page to load.")
        time.sleep(5)


# --- Main execution flow ---

parsing_start_time = time.time()
steps = parse_steps(response.text)
parsing_end_time = time.time()
parsing_time = parsing_end_time - parsing_start_time

print("--- Parsed pyautogui steps: ---")
if steps:
    for s in steps:
        if IS_MACOS and s['type'] == 'applescript':
            print(f"  (AppleScript) {s['original_command']}")
        else:
            print(f"  {s['original_command']}")
else:
    print("No steps were parsed. Please check the AI response format and parsing logic.")
print("--- End of parsed steps ---")
print(f"--- Time to parse steps: {parsing_time:.4f} seconds ---")


print("\n--- Executing steps ---")
executing_steps_start_time = time.time()
for step in steps:
    # Execute the command first. The function handles intra-command delays.
    execute_step(step)
    
    # Apply the unified delay AFTER the entire command has finished.
    time.sleep(STEP_DELAY) 

executing_steps_end_time = time.time()
print(f"--- Finished execution in {executing_steps_end_time - executing_steps_start_time:.2f} seconds ---")


end_time = time.time()
execution_time = end_time - start_time
print(f"\nTotal execution time: {execution_time:.2f} seconds")
