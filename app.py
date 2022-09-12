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
    for script_data in project_data["scripts"] or []:
        script_data["project_name"] = project_data["name"]
        script_data["checked"] = False
        scripts_data.append(script_data)

stdscr = curses.initscr()
curses.noecho()
stdscr.keypad(True)


def print_menu(focused):
    i = 0
    for script_data in scripts_data:
        color = curses.color_pair(8)
        if i == focused:
            color = curses.color_pair(0)
        if scripts_data[i]["checked"] == True:
            color = curses.color_pair(16)
        stdscr.addstr(i, 0, str(i).ljust(4) + script_data["name"], color)
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
