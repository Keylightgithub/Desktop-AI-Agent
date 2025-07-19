Example use case: automated data entry.

Example prompt 1: In the selected cell(s) of the sheet, input a 4x4 sample realistic data entry.

<img width="551" height="290" alt="image" src="https://github.com/user-attachments/assets/fbea66a6-a59d-4995-89c9-c73233524d65" />


Example prompt 2: In this google doc, solve the question

<img width="676" height="449" alt="image" src="https://github.com/user-attachments/assets/c81f19c1-46f2-4ca6-9f4c-36b41d2c1a4e" />




'''
How to use:
1. Add your Google/Gemini API key to env.py file
2. Only change the prompt Goal and Operating system in the prompt variable below.
3. Keep the window you want to automate as the second window behind the first one ex. google sheets behind VS code editor.

Description:
1. Once the script is ran, the script will hide the first window ex. vs code editor.
2. Next the second window behind the first will be screenshotted and sent with the prompt to the AI.
3. The AI will generate a list of steps to accomplish the goal.
4. The script cleans & parses the AI response of pyautogui commands.
5. Pyautogui typing is converted to MacOS applescript typing to avoid accidental modifier keys activation.
6. The script executes the steps with a delay to allow for proper execution.

Note on Limitaions:
1. The AI will do based on 1 automated screenshot so if the window changes it won't work.
2. You will not be able to multitask while the script is running since the keyboard will be in use.
'''

operating_system = \
"""
MacOS
"""

goal = \
'''
In the selected cell(s) of the sheet, input a 4x4 sample realistic data entry.
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
