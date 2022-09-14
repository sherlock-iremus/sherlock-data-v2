import curses
from sqlite3 import adapt
import subprocess
import sys
import yaml
from pprint import pprint

file = open(r"data.yaml")
data = yaml.load(file, Loader=yaml.FullLoader)
file.close()

tasks = []
for project_k, project_v in data["projects"].items():
    for task_k, task_v in project_v["tasks"].items():
        task_v["id"] = project_k + ":" + task_k
        task_v["project_name"] = project_v["name"]
        task_v["checked"] = False
        tasks.append(task_v)

stdscr = curses.initscr()
curses.noecho()
stdscr.keypad(True)
curses.start_color()
NOT_FOCUSED_NOT_CHECKED = 1
FOCUSED_NOT_CHECKED = 2
NOT_FOCUSED_CHECKED = 3
FOCUSED_CHECKED = 4
curses.init_pair(NOT_FOCUSED_NOT_CHECKED, curses.COLOR_WHITE, curses.COLOR_BLACK)
curses.init_pair(FOCUSED_NOT_CHECKED, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
curses.init_pair(NOT_FOCUSED_CHECKED, curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(FOCUSED_CHECKED, curses.COLOR_BLACK, curses.COLOR_MAGENTA)


def print_menu(focused):
    i = 0
    for task in tasks:
        if i == focused:
            color = FOCUSED_CHECKED if tasks[i]["checked"] else FOCUSED_NOT_CHECKED
        else:
            color = NOT_FOCUSED_CHECKED if tasks[i]["checked"] else NOT_FOCUSED_NOT_CHECKED
        stdscr.addstr(i, 0, str(i).ljust(4) + task["name"], curses.color_pair(color))
        i += 1

    stdscr.addstr("\n")
    stdscr.refresh()


state = "quit"


def main(stdscr):
    global state

    stdscr.clear()

    focused = 0
    print_menu(focused)

    while True:
        try:
            key = stdscr.getkey()
        except:
            key = None
        if key == "KEY_DOWN":
            if focused < len(tasks)-1:
                focused += 1
        if key == "KEY_UP":
            if focused > 0:
                focused -= 1
        if key == "q":
            break
        if key == "g":
            state = "go"
            break
        if key == " ":
            tasks[focused]["checked"] = not tasks[focused]["checked"]

        print_menu(focused)


curses.wrapper(main)

if state == "go":
    for task in tasks:
        if task["checked"]:
            print("#" * 80)
            print("### " + task["project_name"])
            print("#" * 80)
            for step in task["steps"]:
                if "git" in step:
                    subprocess.run([f"cd {step['git']} ; git pull origin {step['branch']}"], shell=True)
                elif "script" in step:
                    if step["script"][-3:] == ".py":
                        args = []
                        for arg_k, arg_v in step["args"].items():
                            args.append("--"+arg_k)
                            args.append(arg_v)
                        subprocess.run([sys.executable, step["script"], *args])
                    elif step["script"][-3:] == ".sh":
                        cmd = ""
                        cmd += step["script"]
                        subprocess.run(["sh", cmd], env=step["args"])
