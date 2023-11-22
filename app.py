import curses
from pprint import pprint
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
        tasks.append(task_v)

stdscr = curses.initscr()
curses.noecho()
stdscr.keypad(True)
curses.start_color()
NOT_FOCUSED = 1
FOCUSED = 2
curses.init_pair(NOT_FOCUSED, curses.COLOR_WHITE, curses.COLOR_BLACK)
curses.init_pair(FOCUSED, curses.COLOR_MAGENTA, curses.COLOR_BLACK)


def print_menu(focused):
    i = 0
    for task in tasks:
        if i == focused:
            color = FOCUSED
        else:
            color = NOT_FOCUSED
        stdscr.addstr(i, 0, str(i).ljust(4) + "[" + task["project_name"] + "] " + task["name"], curses.color_pair(color))
        i += 1

    stdscr.addstr("\n")
    stdscr.refresh()


state = "quit"

task_to_run = None


def main(stdscr):
    global state
    global task_to_run

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
        if key == " ":
            task_to_run = tasks[focused]
            break

        print_menu(focused)


curses.wrapper(main)

print("🍄", task_to_run["project_name"], "🍄", task_to_run["name"], "🍄")
for step in task_to_run["steps"]:
    if "git" in step:
        subprocess.run([f"cd {step['git']} ; git pull origin {step['branch']}"], shell=True)
    elif "script" in step:
        if step["script"][-3:] == ".py":
            args = []
            if "args" in step:
                for arg_k, arg_v in step["args"].items():
                    args.append("--"+arg_k)
                    args.append(arg_v)
                subprocess.run([sys.executable, step["script"], *args])
        elif step["script"][-3:] == ".sh":
            cmd = ""
            cmd += step["script"]
            if "args" in step:
                subprocess.run(["sh", cmd], env=step["args"])
            else:
                subprocess.run(["sh", cmd])
