'''
How to use:
1. Add your Google API key to env.py file
2. Only change the prompt Goal and Operating system in the prompt variable below.

Description:
1. Once the script is ran, the script will hide the first window,
2. Next the second window will be the one that the screenshot will take and the AI will analyze.
3. The AI will generate a list of steps to accomplish the goal.
4. The script will parse the AI response and execute the steps using pyautogui.
5. The script will filter out some letters from the results if conflicting with MacOS modifier keys.
6. The script will execute the steps with a delay to allow for proper execution.

Note on Limitaions:
1. The AI will do based on 1 automated screenshot so if the window changes it won't work.
2. You will not be able to multitask while the script is running since the keyboard will in use.
3. Some keys are filtered out since MacOS may mistake them for modifier keys.
 - For example, 'm' and 'M' are filtered out from pyautogui commands
'''

prompt = """
Goal: access the web address bar and search for a random realistic search query
Operating System: MacOS

Tasks:
1. plan out a list of steps to accomplish the goal using only pyautogui keys, hotkeys, and write.
2. Plan out navigation steps completely based on image analysis.
3. give the output in a list format and include the prefix pyautogui for each command.
4. only give the list results, no extra. no comments.
"""
