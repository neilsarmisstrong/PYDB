import os
import re
import time

from interpreter import Interpreter as Int
import errors as err
import colors as clr

class Manager:
    def __init__(self, db_path: str):
        self.db = db_path
        self.int_ = Int(self.db)

    def create_db(self, db_name: str):
        if not self.db.endswith('.pydb'):
            raise err.FileNotDB

        if db_name == '' or db_name.isspace():
            raise err.DBNameEmpty

        if os.path.exists(self.db):
            raise err.DatabaseAlreadyExists

        with open(self.db, 'w+') as db_creator:
            db_creator.write(f'DB_NAME["{db_name}"]')
            db_creator.flush()
            db_creator.seek(0)
            db_creator.close()

    def remove_db(self):
        pass

    def add_group(self, group_name: str):
        """adds group to database"""
        self.int_.get_groups()
        script = self.int_.script_lines

        if group_name in self.int_.db_groups:
            raise err.GroupAlreadyExists

        if self.int_.db_groups == []:
            script.insert(1, '')
            script.insert(2, f'GROUP[name="{group_name}"]')
        else:
            for line in script:
                if re.search(r'GROUP\[name="(.*?)"]', line):
                    try:
                        if not re.findall(r'GROUP\[name="(.*?)"]', script[script.index(line) + 1]):
                            script.insert(script.index(line) + 1, f'GROUP[name="{group_name}"]')
                            break
                    except IndexError:
                            script.insert(script.index(line) + 1, f'GROUP[name="{group_name}"]')
                            break

        with open(self.db, 'w') as group_add:
            for line in script:
                group_add.write(line + '\n')

    def remove_group(self, group: str):
        """removes group from db with all its entries"""
        entries_in_group = self.int_.get_entries_in_group(group)
        script = self.int_.script_lines
        entries_in_group_r = []
        script_ = []

        for line in script:
            if line == f'GROUP[name="{group}"]':
                script.pop(script.index(line))

        for line in script:
            if re.search(r'^ENTRY\[id="(\d+)", name="(.+?)", group="%s", type="(.*?)", value="(.*?)"]$' % group, line):
                entries_in_group_r.append(line)

        for line in script:
            if line not in entries_in_group_r:
                script_.append(line)

        i = 0
        while i < len(script_) or script[-1].isspace():
            i += 1
            if script_[-1] == '':
                del script_[-1]

        with open(self.int_.db, 'w') as rm_entry:
            for line in script_:
                rm_entry.write(line + '\n')

        print(script_)

    def edit_group(self, group: str, new_group_name: str):
        """changes group name"""
        entries_in_group = self.int_.get_entries_in_group(group)
        script = self.int_.script_lines

        if new_group_name.isspace() or new_group_name == '':
            raise err.GroupNameEmpty

        if new_group_name in self.int_.db_groups:
            raise err.GroupAlreadyExists

        for line in script:
            # print(line)
            # print('line end')
            if line == f'GROUP[name="{group}"]':
                group_indx = script.index(line)
                script.remove(line)
                script.insert(group_indx, f'GROUP[name="{new_group_name}"]')
            # print(line)
            # print('line end')
            if re.search(r'^ENTRY\[id="(\d+)", name="(.+?)", group="%s", type="(.*?)", value="(.*?)"]$' % group, line):
                entry_indx = script.index(line)
                print(line)
                script.remove(line)
                script.insert(entry_indx, line.replace(f'group="{group}"', f'group="{new_group_name}"'))



        # for line in script:
        #     if line == f'GROUP[name="{group}"]':
        #         group_indx = script.index(line)
        #         script.remove(line)
        #         script.insert(group_indx, f'GROUP[name="{new_group_name}"]')
        #         continue

        #     print(line)
        #     if re.search(r'ENTRY\[id="(.*?)", name="(.*?)", group="' + group + r'"]', line):
        #         print(line)
        #         print('line end')


            # # FIXME: TODO: make re.search safe, so value won't be scanned
            # if re.search(r'ENTRY\[id="(\d)", name="(.?)", group="' + group + r'"', line):
            #     # ENTRY[id="2", name="entryOne", group="1", type="int", value="1234"]
            #     entry_indx = script.index(line)
            #     print(line)
            #     script.remove(line)
            #     script.insert(entry_indx, line.replace(f'group="{group}"', f'group="{new_group_name}"'))
            
        with open(self.db, 'w') as group_edit:
            for line in script:
                group_edit.write(line + '\n')

    def add_entry(self, name: str, group: str, data_type='', value='', id_value=''):
        """adds entry to database"""
        self.int_.get_groups()

        entries_in_group = self.int_.get_entries_in_group(group)
        
        # check id first
        entry_ids = []
        for entry in entries_in_group:
            if id_value == entry['id']:
                raise err.DoubleID
            entry_ids.append(entry['id'])
        
        if id_value == 'AUTO':
            if entry_ids == []:
                id_value = 1
            else:
                id_value = int(max(entry_ids)) + 1

        # checks data types
        data_types = ['int', 'float', 'string', 'bool', 'date', 'text']

        # FIXME: if data_type == '', value could be set
        if value == '':
            pass
        else:
            try:
                if data_type == data_types[0]:      # int
                    value = int(value)
                elif data_type == data_types[1]:    # float
                    value = float(value)
                elif data_type == data_types[2]:    # string
                    value = str(value)
                elif data_type == data_types[3]:    # bool
                    if value.lower() != 'true' and value.lower() != 'false' and value != '0' and value != '1':
                        raise err.DBValueError
                    value = bool(value.lower())
                elif data_type == data_types[4]:    # date
                    if not re.search('^(\d)(\d)/(\d)(\d)/(\d)(\d)(\d)(\d)$', str(value)):
                        raise err.DBValueError
                elif data_type == data_types[5]:    # text
                    if not value.isalpha():
                        raise err.DBValueError
            except ValueError:
                raise err.DBValueError

        entry = f'ENTRY[id="{id_value}", name="{name}", group="{group}", type="{data_type}", value="{value}"]'

        # check where to add the entry
        # TODO: remove unnecessary blank lines in db file
        script = self.int_.script_lines

        r_groups = re.compile(r'^GROUP\[name="(.*?)"]$')
        r_entries = re.compile(r'^ENTRY\[id="(\d+)", name="(.+?)", group="(.+?)", type="(.*?)", value="(.*?)"]$')

        groups = list(filter(r_groups.match, script))
        entries = list(filter(r_entries.match, script))
        
        if entries == []:
            last_group_index = script.index(groups[-1])
            
            script.insert(last_group_index + 1, '')
            script.insert(last_group_index + 2, entry)
        else:
            last_entry_index = script.index(entries[-1])

            script.insert(last_entry_index + 1, entry)

        print(script)
        i = 0
        while i < len(script):
            i += 1
            if script[-1] == '' or script[-1].isspace():
                print('as')
                del script[-1]

        with open(self.int_.db, 'w') as add_entry_f:
            for line in script:
                add_entry_f.write(line + '\n')

    def remove_entry(self, id: int, group: str):
        """removes entry from db"""
        # FIXME: check if group exists
        entries_in_group = self.int_.get_entries_in_group(group)
        script = self.int_.script_lines

        for entry in entries_in_group:
            if entry["id"] == id and entry["group"] == group:
                for line in script:
                    if line == f'ENTRY[id="{entry["id"]}", name="{entry["name"]}", group="{entry["group"]}", type="{entry["type"]}", value="{entry["value"]}"]':
                        script.remove(line)

                        if script[-1] == '':
                            del script[-1]

                        with open(self.db, 'w') as entry_rm:
                            for line in script:
                                entry_rm.write(line + '\n')
                
                return 0
        
        raise err.EntryNotFound
        

    def edit_entry(self, id: int, group: str, attributes: dict):
        """edit entry attributes"""
        entries_in_group = self.int_.get_entries_in_group(group)

        self.int_.get_groups()
        if group not in self.int_.db_groups:
            raise err.GroupNotFound

        entries_in_group = self.int_.get_entries_in_group(group)
        script = self.int_.script_lines

        for entry in entries_in_group:
            if entry['id'] == str(id):
                if 'id' in attributes:
                    raise err.EntryIDchange

# r_entries = re.compile(r'^ENTRY\[id="(\d+)", name="(.+?)", group="(.+?)", type="(.*?)", value="(.*?)"]$')
                for line in script:
                    if re.search(r'^ENTRY\[id="%s", name="(.*?)", group="%s", type="(.*?)", value="(.*?)"]$' % (id, group), line):
                        line_original = line
                        line_edit = line
                        for key in attributes:
                            if key == 'name':
                                r_entry_name = re.compile(r'name="(.*?)"')
                                line_edit = re.sub(r_entry_name, 'name="%s"' % attributes['name'], line_edit)
                            elif key == 'group':
                                if not attributes['group'] in self.int_.db_groups:
                                    raise err.GroupNotFound

                                # check id first
                                entry_ids = []
                                for entry in self.int_.get_entries_in_group(attributes['group']):
                                    entry_ids.append(entry['id'])
                                
                                if entry_ids == []:
                                    entry_ids.append('0')

                                for e_id in entry_ids:
                                    e_id = int(max(entry_ids)) + 1
                                    id = e_id

                                script = self.int_.script_lines # reloads script, because any self.int_ function clears it for some reason

                                r_entry_group = re.compile(r'group="(.*?)"')
                                r_entry_id = re.compile(r'id="(.*?)"')
                                line_edit = re.sub(r_entry_group, 'group="%s"' % attributes['group'], line_edit)
                                line_edit = re.sub(r_entry_id, 'id="%s"' % id, line_edit)
                            elif key == 'type':
                                # TODO: set value to NULL
                                r_entry_type = re.compile(r'type="(.*?)"')
                                line_edit = re.sub(r_entry_type, 'type="%s"' % attributes['type'], line_edit)
                            elif key == 'value':
                                # TODO: check if value is the right datatype
                                r_entry_value = re.compile(r'value="(.*?)"')
                                line_edit = re.sub(r_entry_value, 'value="%s"' % attributes['value'], line_edit)
                            else:
                                raise err.EntryAttributeNotFound

                        old_entry_index = script.index(line_original)
                        script.remove(line_original)
                        script.insert(old_entry_index, line_edit)

                        if script[-1] == '':
                            del script[-1]

                        with open(self.db, 'w') as entry_edit:
                            for line in script:
                                entry_edit.write(line + '\n')
                return 0
        
        raise err.EntryNotFound
