import curses
from sqlite3 import adapt
import subprocess
import sys
import yaml

file = open(r"data.yaml")
data = yaml.load(file, Loader=yaml.FullLoader)
file.close()

scripts_data = []
for project_key, project_data in data["projects"].items():
    for script_key, script_data in project_data["scripts"].items():
        script_data["id"] = project_key + ":" + script_key
        script_data["project_name"] = project_data["name"]
        script_data["checked"] = False
        scripts_data.append(script_data)

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
    for script_data in scripts_data:
        if i == focused:
            color = FOCUSED_CHECKED if scripts_data[i]["checked"] else FOCUSED_NOT_CHECKED
        else:
            color = NOT_FOCUSED_CHECKED if scripts_data[i]["checked"] else NOT_FOCUSED_NOT_CHECKED
        stdscr.addstr(i, 0, str(i).ljust(4) + script_data["name"], curses.color_pair(color))
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
            if focused < len(scripts_data)-1:
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
            scripts_data[focused]["checked"] = not scripts_data[focused]["checked"]

        print_menu(focused)


curses.wrapper(main)

if state == "go":
    for script in scripts_data:
        print("#" * 80)
        print("# " + script["project_name"])
        print("#" * 80)
        if script["checked"]:
            args = []
            if "script" in script:
                if "args" in script["script"]:
                    for arg_k, arg_v in script["script"]["args"].items():
                        args.append("--"+arg_k)
                        args.append(arg_v)
                subprocess.run([sys.executable, script["script"]["file"], *args])
