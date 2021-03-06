import os
from time import sleep
import re
import sys
import json
import shlex
import subprocess

from manager import Manager as Mgr
from interpreter import Interpreter as Int
import errors as err
import colors as clr

# clr.Fore colors
L_R = clr.Fore.LIGHT_RED
L_B = clr.Fore.LIGHT_BLUE
W = clr.Fore.WHITE
Y = clr.Fore.YELLOW

start_menu_help_text = \
"""
----------------------------------------------------
help                        shows this help
quit/exit                   quits the program
clear                       clears the terminal
reload                      restarts the application (useful if you change config.json)

ch                          if use_standard_db_path is true you can select a db from that directory
                            (only works if "use_standard_db_path" is activated)
ch [db_path]                changes the DB file to your provided file path
create [db_file] [db_name]  creates a new DB at the provided path with the provided DB_NAME
----------------------------------------------------
"""

help_text = \
f"""
----------------------------------------------------

{clr.Fore.DARK_GREY}=============={W}
{clr.Fore.PURPLE}basic commands{W}
{clr.Fore.DARK_GREY}=============={W}
{L_B}help{W}                shows this help
{L_B}quit/exit{W}           quits the program
{L_B}clear{W}               clears the terminal
{L_B}back{W}                get back to start menu
{L_B}reload{W}              reloads config.json // not working at the moment

{clr.Fore.DARK_GREY}============={W}
{clr.Fore.PURPLE}list commands{W}
{clr.Fore.DARK_GREY}============={W}
{L_B}lsg{W}                 lists all groups in database
{L_B}lsea{W}                lists all entries in all groups
{L_B}lse{W} [group_name]    lists all entries in the specified group

{clr.Fore.DARK_GREY}============{W}
{clr.Fore.PURPLE}add commands{W}
{clr.Fore.DARK_GREY}============{W}
{L_B}add{W} {Y}<arg 1> <arg 2> [<arg 3>] {W}:
        {Y}<arg 1>{W}: required; either "group" or "entry"
        {Y}<arg 2>{W}: required; a name for either the group or the entry
            {Y}<arg 3>{W}: entry information: e.g. (id=AUTO;name="EntryOne";group="GroupOne";data_type="int";value="1")
                id (req):       either an integer or AUTO
                name (req):     string
                group (req):    string
                data_type:      [int, float, string, bool, date, text]; if empty, "value" cannot have a value
                value:          same type as data_type

{clr.Fore.DARK_GREY}==============={W}
{clr.Fore.PURPLE}remove commands{W}
{clr.Fore.DARK_GREY}==============={W}
{L_B}rm{W} {Y}<arg 1>{W} {Y}<arg 2>{W}:
        {Y}<arg 1>{W}: required; either "group" or "entry"
        {Y}<arg 2>{W}: required; name of the group or entry's id and group

{clr.Fore.DARK_GREY}==============={W}
{clr.Fore.PURPLE}remove commands{W}
{clr.Fore.DARK_GREY}==============={W}
{L_B}edit{W} {Y}<arg 1>{W} {Y}<arg 2>{W}:
        {Y}<arg 1>{W}: required; either "group" or "entry"
        {Y}<arg 2>{W}: required; name of the group or entry's id and group in the "(id, group)" format
----------------------------------------------------
"""

# basic settings
standard_db_path = ''
use_standard_db_path = False

# class object vars
int_ = None
mgr = None
py_ver = None

# NOTE: will probably be removed
# checks the OS
if sys.platform == 'win32':
    os.system('cls')
    os.system('color F')
elif sys.platform == 'linux':
    import readline
    os.system('clear')

    py_ver = sys.version_info[0] + sys.version_info[1]

# loads config.json
def load_config():
    global standard_db_path
    global use_standard_db_path

    try:
        with open('config.json', 'r') as cfg_r:
            json_cfg = cfg_r.read()
        cfg = json.loads(json_cfg)

        if 'standard_db_path' in cfg and not cfg['standard_db_path'].isspace() and cfg['standard_db_path'] != '':
            # checks if standard_db_path exists and is a path
            if not os.path.exists(cfg['standard_db_path']):
                print(L_R + 'The provided path wasn\'t found!\nChange your "config.json" file' + W)
                exit(0)
            if os.path.isfile(cfg['standard_db_path']):
                print(L_R + 'The provided path can\'t be a file!\nChange your "config.json" file' + W)
                exit(0)

            standard_db_path = cfg['standard_db_path']

            if 'use_standard_db_path' in cfg:
                use_standard_db_path = cfg['use_standard_db_path']
            else:
                use_standard_db_path = True

            if not standard_db_path.endswith('/'):
                standard_db_path += '/'             # adds a / if there is no at the end ot the standard_db_path
    except FileNotFoundError:
        print(clr.Fore.YELLOW + '[i] You don\'t have a "config.json" file, using standard settings' + W)
        pass

    print(clr.Fore.YELLOW + '[i] If you change config.json you have to restart the application manually' + W)

def quit():
    """quits the application"""
    print('\nQuitting...')
    sleep(1)
    if sys.platform == 'win32':
        os.system('cls')
        os.system('color F')
    elif sys.platform == 'linux':
        os.system('clear')
    exit(0)

def restart():
    print('\nRestart...')
    sleep(1)
    if sys.platform == 'win32':
        try:
            subprocess.run('python ' + os.path.realpath(__file__))
            sys.exit(0)
        except KeyboardInterrupt:
            exit(0)
    elif sys.platform == 'linux':
        try:
            os.system(py_ver + ' console.py')
        except KeyboardInterrupt:
            exit(0)
    exit(0)

def reload():
    print('\nReloading...')
    sleep(1)
    main()

def start_menu():
    """start menu provides list of databases if 'use_standard_db_path = True' and allows to create and change a db"""
    global int_
    global mgr
    global use_standard_db_path

    while True:
        print('Current directory: ' + os.path.dirname(os.path.realpath(__file__)))
        cmd = input(f'>> ')
        try:
            _cmd = shlex.split(cmd)
            if '' in _cmd:
                _cmd.remove('')
            
            if _cmd == []:
                continue
        except ValueError:
            print(L_R + 'You need to add closing quotes!' + W)
            continue
            
        if _cmd[0] == 'help':
            print(start_menu_help_text)
        elif _cmd[0] == 'quit' or _cmd[0] == 'exit':
            quit()
        elif _cmd[0] == 'clear':
            if sys.platform == 'win32':
                os.system('cls')
            elif sys.platform == 'linux':
                os.system('clear')
        elif _cmd[0] == 'reload':
            # reload()
            print(clr.Fore.YELLOW + 'not available at the moment, please restart manually' + W)
        elif _cmd[0] == 'restart':
            # restart()
            print(clr.Fore.YELLOW + 'not available at the moment, please restart manually' + W)
        elif _cmd[0] == 'ch':
            if len(_cmd) == 1 and _cmd[0] == 'ch' and not use_standard_db_path:
                print(clr.Fore.YELLOW + 'You set "use_standard_db_path" to false in you config.json. Type in a path or change it and then type in "reload"' + W)
                continue
            if len(_cmd) == 1 and _cmd[0] == 'ch' and use_standard_db_path:           # if standard_db_path is set in config.json and use_standard_db_path = True,
                files_in_std_dir = os.listdir(standard_db_path)                         # this will let the user choose a .pydb file from that directory

                # searches db files and prints a list of them to choose from
                databases_counter = 0
                databases = []
                for i in files_in_std_dir:  # i is the file in files_in_std_dir
                    if os.path.isfile(standard_db_path + i):
                        if i.endswith('.pydb'):
                            databases_counter += 1
                            databases.append([databases_counter, standard_db_path + i])
                            print(clr.Fore.PURPLE + f'[{databases_counter}] ' + W + i)

                if databases_counter == 0:
                    print(clr.Fore.YELLOW + '[i] There is no ".pydb" file in the given directory' + W)
                    print('')
                    # use_standard_db_path = False
                    continue

                print(f'\n{L_R}[q]{W} quit\n')

                while True:
                    # lets the user choose from the list
                    try:
                        select_i = input('Type in the number of the database you want to use\n> ')
                        if select_i == 'q' or select_i == 'quit':
                            start_menu()
                        else:
                            db_num = int(select_i)
                    except ValueError:
                        print(L_R + 'The input needs to be a non decimal number!' + W)
                        continue

                    if db_num < 1 or db_num > databases_counter:
                        print(L_R + 'The number you typed in is out of range!' + W)
                        start_menu()

                    for db in databases:
                        if db_num == db[0]:
                            int_ = Int(db[1])

                            try:
                                int_.check_db_file()
                                print('Loading the database...')
                                int_.get_script()
                                print('Loaded\n')

                                mgr = Mgr(db[1])
                                break
                            except err.FileNotDB as e:
                                print(e)
                            except err.DatabaseNotFound as e:
                                print(e)

                    break
                break
            elif len(_cmd) == 2 and _cmd[0] == 'ch' and _cmd[1] != '' and not _cmd[1].isspace():
                int_ = Int(_cmd[1])

                try:
                    int_.check_db_file()
                    print('Loading the database...')
                    int_.get_script()
                    print('Loaded\n')

                    mgr = Mgr(_cmd[1])
                    break
                except err.FileNotDB as e:
                    print(L_R + str(e) + W)
                except err.DatabaseNotFound as e:
                    print(L_R + str(e) + W)
            elif _cmd[0] == 'ch':
                if len(_cmd) > 2:
                    print(L_R + 'That are too many arguments!' + W)

                if len(_cmd) == 2 and _cmd[1] == '' or _cmd[1].isspace():
                    print(L_R + 'You have to provide a database file!' + W)
        elif _cmd[0] == 'create':
            if len(_cmd) < 3 or _cmd[1] == '' or _cmd[2] == ''  or _cmd[1].isspace() or _cmd[2].isspace():
                print(L_R + 'You have to provide a file name or path and a DB_NAME!' + W)
                continue
            
            db_file = _cmd[1]

            if '/' not in _cmd[1] and use_standard_db_path:
                db_file = standard_db_path + _cmd[1]

            try:
                mgr_ = Mgr(db_file)
                mgr_.create_db(_cmd[2])
            except err.DatabaseAlreadyExists as e:
                print(L_R + str(e) + W)
                continue
            except err.FileNotDB as e:
                print(L_R + str(e) + W)
                continue

            int_ = Int(db_file)
            int_.check_db_file()
            print('Loading the database...')
            int_.get_script()
            print('Loaded\n')

            mgr = Mgr(_cmd[1])
            break
        else:
            print(f'{L_R}"{_cmd[0]}" is an unknown command, type "help" to see a list of all available commands{W}')

# TODO: rework back method and start menu
def main():
    # welcome text
    print('-------------------------------------------')
    print('Welcome to PYDB')
    print('dev v1.0')
    print('type "help" for a list of available commands')
    print('-------------------------------------------\n')
    
    load_config()

    try:
        start_menu()

        while True:
            cmd = input(f'({L_R}{int_.db_name}{W})>> ')
            # _cmd = re.split(r'\s+(?=[^"]*(?:\(|$))', cmd)
            _cmd = shlex.split(cmd)
            if '' in _cmd:
                _cmd.remove('')
            cmd_str = cmd
            cmd = cmd.split()

            if _cmd == []:
                continue

            if _cmd[0] == 'exit' or _cmd[0] == 'quit':
                """quits console"""
                quit()
            elif _cmd[0] == 'help':
                """prints help text"""
                print(help_text)
            elif _cmd[0] == 'back':
                print('\n-----Start Menu-----\ntype "help" for a list of available commands\n' + '-' * 20 + '\n')
                start_menu()
            elif _cmd[0] == 'clear':
                if sys.platform == 'win32':
                    os.system('cls')
                elif sys.platform == 'linux':
                    os.system('clear')
            elif _cmd[0] == 'reload':
                # reload()
                print(clr.Fore.YELLOW + 'not available at the moment, please restart manually' + W)
            elif _cmd[0] == 'restart':
                # restart()
                print(clr.Fore.YELLOW + 'not available at the moment, please restart manually' + W)
            elif _cmd[0] == 'lsg':
                """lists all groups in DB"""
                int_.get_groups()

                if not int_.db_groups:
                    print('There are no groups in this database')
                    continue

                print('\n' + f'----- Groups in "{clr.Fore.PURPLE}{int_.db_name}{W}" -----')
                for group in int_.db_groups:
                    print(clr.Fore.ORANGE + group + W)

                print('-' * len(f'----- Groups in "{int_.db_name}" -----') + '\n')
            elif _cmd[0] == 'lsea':
                """lists all entries in all groups in DB"""
                int_.get_entries()
                if int_.db_entries == []:
                    print('There are no entries in this database')
                    continue

                print('')
                print(f'{clr.Fore.CYAN}ID\t{clr.Fore.ORANGE}Group\t\t{clr.Fore.LIGHT_GREEN}Name\n{W}')
                for entry in int_.db_entries:
                    print(clr.Fore.CYAN + entry['id'] + '\t' + clr.Fore.ORANGE + entry['group'] + '\t\t' + clr.Fore.LIGHT_GREEN + entry['name'] + W)
                print('')
            elif _cmd[0] == 'lse':
                """lists all entries in specified group"""
                if len(cmd) < 2:
                    print(L_R + 'You need to specify a group!' + W)
                    continue

                try:
                    try:
                        entries_in_group = int_.get_entries_in_group(_cmd[1])
                    except IndexError:
                        entries_in_group = int_.get_entries_in_group(cmd[1])

                    if entries_in_group == []:
                        print(clr.Fore.YELLOW + 'There are no entries in the specified group' + W)
                        continue

                    print(f'{clr.Fore.CYAN}ID\t{clr.Fore.LIGHT_GREEN}Name\n{W}')
                    for entry in entries_in_group:
                        print(clr.Fore.CYAN + entry['id'] + '\t' + entry['name'] + W)
                except err.GroupNotFound as e:
                    print(L_R + str(e) + W)
            elif _cmd[0] == 'add':
                """adds group or entry"""
                if len(_cmd) < 2 or _cmd[1] == '' or _cmd[1].isspace():
                    print(L_R + 'You need to specify what you want to add\nType "help" to see a list of all available commands' + W)
                    continue
                
                # adds group
                if _cmd[1] == 'group':
                    if len(_cmd) < 3:
                        print(L_R + 'You need to specify a name for the group' + W)
                        continue
                    elif len(_cmd) > 3:
                        print(L_R + '2 arguments excpected; got ' + str(len(_cmd) - 1) + W)
                        continue

                    try:
                        mgr.add_group(_cmd[2])
                    except err.GroupAlreadyExists as e:
                        print(L_R + str(e) + W)
                        continue

                    print('Added group')
                    continue
                # adds entry
                elif _cmd[1] == 'entry':
                    if len(_cmd) < 3:
                        print(L_R + 'You need to specify an entry schema' + W)
                        continue

                    if re.search(r'\(id=(.*?);name="(.*?)";group="(.*?)";data_type="(.*?)";value="(.*?)"\)', cmd_str):
                        entry_values = re.findall(r'\(id=(.*?);name="(.*?)";group="(.*?)";data_type="(.*?)";value="(.*?)"\)', cmd_str)

                        id = entry_values[0][0]
                        name = entry_values[0][1]
                        group = entry_values[0][2]
                        data_type = entry_values[0][3]
                        value = entry_values[0][4]
                        
                        try:
                            int(id)
                        except ValueError:
                            if id == '':
                                print(L_R + '"id" cannot be empty, it needs to be either set to an integer or to "AUTO"' + W)
                                continue
                            elif id != 'AUTO':
                                print(L_R + '"id" needs to be an integer or set to "AUTO" (without quotes)' + W)
                                continue

                        if name == '':
                            print(L_R + '"name" cannot be empty' + W)
                            continue
                        if group == '':
                            print(L_R + '"group" cannot be empty' + W)
                            continue
                        
                        try:
                            mgr.add_entry(name, group, data_type, value, id)
                        except (err.DoubleID, err.GroupNotFound, err.DBValueError) as e:
                            print(L_R + str(e) + W)

                    else:
                        print(L_R + 'Your schema caused an error. Please try again.' + W)

            elif _cmd[0] == 'rm':
                """removes group or entry"""
                # TODO: rm entry
                if len(_cmd) < 2 or _cmd[1] == '' or _cmd[1].isspace():
                    print(L_R + 'You need to specify what you want to delete\nType "help" to see a list of all available commands' + W)
                    continue

                # removes group
                if _cmd[1] == 'group':
                    if len(_cmd) < 3:
                        print(L_R + 'You need to specify the name of the group' + W)
                        continue
                    elif len(_cmd) > 3:
                        print(L_R + '2 arguments excpected; got ' + str(len(_cmd) - 1) + W)
                        continue

                    int_.get_groups()
                    if _cmd[2] not in int_.db_groups:
                        print(L_R + 'The specified group could not be found!' + W)
                        continue

                    confirmation = input('Are you sure about deleting the group "' + _cmd[2] + '"? All entries within this group will be remove as well.\n[y/n] ')

                    if confirmation == 'n':
                        print('Group didn\'t get removed')
                    elif confirmation == 'y':
                        try:
                            mgr.remove_group(_cmd[2])
                        except err.GroupNotFound as e:
                            print(L_R + str(e) + W)
                            continue
                    else:
                        print('Abort removing process. Group didn\'t get removed')
                elif _cmd[1] == 'entry':
                    if len(_cmd) < 3:
                        print(L_R + 'You need to specify the entry you want to delete' + W)
                        continue
                    elif len(_cmd) > 3:
                        print(L_R + '2 arguments excpected; got ' + str(len(_cmd) - 1) + W)
                        continue

                    if re.search(r'\(id="(\d*)";group="(.*?)"\)', cmd_str):
                        entry_values = re.findall(r'\(id="(\d*)";group="(.*?)"\)', cmd_str)

                        id = entry_values[0][0]
                        group = entry_values[0][1]

                        if id == '':
                            print(L_R + '"id" cannot be empty' + W)
                            continue
                        if group == '':
                            print(L_R + '"group" cannot be empty' + W)
                            continue

                        try:
                            mgr.remove_entry(id, group)
                        except (err.GroupNotFound, err.EntryNotFound) as e:
                            print(L_R + str(e) + W)
                    else:
                        print(L_R + 'Your schema caused an error. Please try again.' + W)
                else:
                    print(L_R + f'"rm {_cmd[1]}" is not a valid command' + W)

            elif _cmd[0] == 'edit':
                # TODO: edit entry
                if len(_cmd) < 2 or _cmd[1] == '' or _cmd[1].isspace():
                    print(L_R + 'You need to specify what you want to edit\nType "help" to see a list of all available commands' + W)
                    continue

                # changes group name
                if _cmd[1] == 'group':
                    if len(_cmd) < 3:
                        print(L_R + 'You need to specify the name of the group' + W)
                        continue
                    if len(_cmd) > 4:
                        print(L_R + '2 arguments excpected; got ' + str(len(_cmd) - 1) + W)
                        continue

                    int_.get_groups()
                    if _cmd[2] not in int_.db_groups:
                        print(L_R + 'The specified group could not be found!' + W)
                        continue

                    new_name = input('new group name: ')

                    try:
                        mgr.edit_group(_cmd[2], new_name)
                        print('Successfully updated group')
                    except (err.GroupAlreadyExists, err.GroupNameEmpty) as e:
                        print(L_R + str(e) + W)
            else:
                print(f'{L_R}"{cmd[0]}" is an unknown command, type "help" to see a list of all available commands{W}')
    except KeyboardInterrupt:
        quit()

if __name__ == '__main__':
    main()
