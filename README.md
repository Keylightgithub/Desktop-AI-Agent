Example use case: automated data entry.

Example Prompt 1: In the selected cell(s) of the sheet, input a 3x3 sample realistic data entry.

<img width="448" height="346" alt="Screenshot 2025-07-17 at 3 06 25 AM" src="https://github.com/user-attachments/assets/c055405b-8b17-43c1-82a3-c43437cb6ff4" />


'''
How to use:
1. Add your Google API key to env.py file
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

prompt = """
Goal: In the selected cell(s) of the sheet, input a 3x3 sample realistic data entry.
Operating System: MacOS

Tasks:
1. Accomplish the goal using only pyautogui keys, hotkeys, and write (no clicks).
2. Plan out navigation steps completely based on image analysis.
3. Give the output in a list format and include the prefix pyautogui for each command.
4. Only give the list results, no extra. no comments.
"""
