import os
from enum import Enum
from sys import path as py_path
from tt.controller.exceptions import ReaderError


class Spine:
    """All the information from the spine file to guide the publication process."""

    class PubInfoItem:
        """Every publication file corresponds to a PubInfoItem object to collect the needed information of it."""

        def __init__(self, file_name: str, file_format: str, content_file_list: list, template_list: list):
            """Create a new information item for a file of the publication.

            :param file_name: a file name of the publication.
            :param file_format: the extension of the file name.
            :param content_file_list: the list of the tt files used as content.
            :param template_list: the list of the template files to apply.
            """
            self._file_name = file_name
            self._file_format = file_format
            self._content_file_list = content_file_list
            self._template_list = template_list

        def get_file_name(self):
            """Get the name of the publication file without the extension."""

            return self._file_name

        def get_file_format(self):
            """Get the extension of the publication file."""

            return self._file_format

        def get_file_name_with_ext(self):
            """Get the name of the publication file with the extension."""

            return Paths.put_file_ext(self._file_name, self._file_format)

        def get_file_abs_path(self):
            """Get the absolute path of the publication file."""

            return spine.paths.get_publication_file_abs_path(self.get_file_name_with_ext())

        def get_content_list(self):
            """Get the list of the tt content files."""

            return self._content_file_list

        def get_content_head(self):
            """Get the first input file from input file list."""

            return self._content_file_list[0]

        def get_template_list(self):
            """Get the list of the template files."""

            return self._template_list

    class Definition:
        """Every line on the spine file is a definition about the whole process. They are managed with this object."""

        _tag = ''
        _value = []

        @classmethod
        def set(cls, definition, value=None):
            """Set a definition from json spine file to manage it like an object.

            :param definition: an item from json spine file that is a list of 2 items (value and tag) or it is a tag of
            that definition.
            :param value: a value of that definition. To be specified when the first argument is a tag.
            """
            if value is None:
                if type(definition) is list and len(definition) == 2:
                    cls._tag = definition[1]
                    cls._value = definition[0]
            else:
                cls._tag = definition
                cls._value = value

        @classmethod
        def get_tag(cls):
            """Get the tag of the definition."""

            return cls._tag

        @classmethod
        def has_tag(cls, tag_name_list):
            """Check if the tag name of the definition corresponds to the passed ones.

            :param tag_name_list: a single tag name or a list of tag names to check.
            :return: True or False according to the presence of the definition tag in the list.
            """
            if type(tag_name_list) is str:
                tag_name_list = [tag_name_list]

            return cls._tag in tag_name_list

        @classmethod
        def get_value(cls):
            """Get the value of the definition."""

            return cls._value

    def __init__(self):
        """Instantiate the spine object with all the information to start the publication process and also to track the
        changes during its development."""

        self.paths = Paths(self)
        self.counters = Counters()
        self._pub_info_list = []
        self._current_pub_info_item_index = 0
        self._file_name_lists = {}  # key: list name; value: file name list
        self._pub_file_name_indexes = {}  # key: pub file name; value: pub info index
        self._tt_file_names = set()
        self._json_file_names = []
        self._detected_tt_files = []
        self._unchanged_json_files = []
        self._var = {}  # key: var name; value: text value

    def initialize(self):
        """Initialize again the spine object with the initial values.

        Spine is a global var, if the same script lunches the method write_publication_with_spine more times, the
        following publication needs to have the initial values again to remove the previous values.
        """
        self.__init__()

    def set_content_path(self, rel_folder: str):
        """Set the path of the folder of the content files.

        :param rel_folder: the relative folder of the content files.
        """
        self.paths.set_tt_files_rel_folder(rel_folder)

    def set_template_path(self, rel_folder: str):
        """Set the path of the folder of the template files.

        :param rel_folder: the relative folder of the template files.
        """
        self.paths.template_files_rel_folder = rel_folder

    def set_publication_path(self, rel_folder: str):
        """Set the path of the folder of the publication files.

        :param rel_folder: the relative folder of the publication files.
        """
        self.paths.publication_files_rel_folder = rel_folder

    def set_file_names_to_a_list(self, list_name: str, file_names: list):
        """Create a list with a name containing a list of file names.

        :param list_name: the name of the list to set.
        :param file_names: the file names associated to the list.
        """
        self._file_name_lists[list_name] = file_names

    def has_file_list_named(self, list_name: str):
        """Check if it exists a list with the requested name.

        :param list_name: the name of a list to check.
        :return: True or False according to the existence of a list with the requested name.
        """
        if list_name in self._file_name_lists:
            return True
        else:
            return False

    def get_file_name_list(self, list_name: str):
        """Get the list of file names by the list name.

        :param list_name: the name of the list to get.
        :return: the list of file names.
        """
        return self._file_name_lists[list_name]

    def get_content_head_by_pub_item_index(self, index: int):
        """Get the content head file of a publication item selecting it by its index.

        :param index: the index of the publication item.
        :return: the file name of the content head.
        """
        return self._pub_info_list[index].get_content_head()

    def get_content_list_by_pub_item_index(self, index: int):
        """Get the content file list of a publication item selecting it by its index.

        :param index: the index of the publication item.
        :return: the file names of the content list.
        """
        return self._pub_info_list[index].get_content_list()

    def get_template_list_by_pub_item_index(self, index: int):
        """Get the template file list of a publication item selecting it by its index.

        :param index: the index of the publication item.
        :return: the file names of the template list.
        """
        return self._pub_info_list[index].get_template_list()

    def set_variable(self, name: str, value):
        """Set a global variable of the publication with the name and its value.

        :param name: the name of the global variable of the publication.
        :param value: the value of the variable.
        """
        self._var[name] = value

    def get_variable(self, name: str):
        """Get the value of a global variable of the publication.

        :param name: the name of the global variable of the publication.
        :return: the value of the variable.
        """
        return self._var[name]

    def append_json_file_name(self, file_name: str):
        """Append a file name to the spine forcing the file extension with json.

        :param file_name: the file name to append considered as a json.
        """
        file_name = Paths.put_file_ext(file_name, 'json')
        self._json_file_names.append(file_name)

    def append_pub_info_item(self, file_name: str, file_format: str, input_file_list, template_list: list):
        """Append a publication item to the publication list that guides the publication process.

        :param file_name: a file name of the publication without extension.
        :param file_format: the extension of the file name to publish.
        :param input_file_list: the list of tt files used to generate content of the file to publish.
        :param template_list: the list of templates to apply to generate the final content.
        """
        if type(input_file_list) is not list:
            input_file_list = [input_file_list]

        pub_info_item = self.PubInfoItem(file_name, file_format, input_file_list, template_list)
        self._pub_info_list.append(pub_info_item)

    def append_detected_tt_file(self, file_name: str):
        """Append a detected tt file to the list of detected tt file names.

        :param file_name: the detected tt file name.
        """
        self._detected_tt_files.append(file_name)

    def sort_detected_tt_files(self):
        """Sort the list of the detected tt files."""

        self._detected_tt_files.sort()

    def get_detected_tt_file_names(self):
        """Get the list of the detected tt files."""

        return self._detected_tt_files

    def append_unchanged_json_file(self, file_name: str):
        """Append an unchanged json file to the list of unchanged json file names.

        :param file_name: the unchanged json file name.
        """
        self._unchanged_json_files.append(file_name)

    def get_unchanged_json_file_names(self):
        """Get the list of the unchanged json files."""

        return self._unchanged_json_files

    def set_current_pub_item_index(self, index: int):
        """Save the index of the current publication item by the index of that item.

        :param index: the index of the current publication item.
        """
        self._current_pub_info_item_index = index

    def set_current_pub_item_index_by_its_name(self, tt_file_name: str):
        """Save the index of the current publication item by the file name of that item.

        :param tt_file_name: the file name of a tt content file.
        """
        self.set_current_pub_item_index(self.get_index_of_pub_file_name(tt_file_name))

    def get_current_pub_item_index(self):
        """Get the previously saved publication info item."""

        return self._current_pub_info_item_index

    def get_content_head_of_current_pub_item(self):
        """Get the content data of the content head file of the current publication item."""

        return self.get_content_head_by_pub_item_index(self.get_current_pub_item_index())

    def get_content_list_of_current_pub_item(self):
        """Get the content file list of the current publication item."""

        return self.get_content_list_by_pub_item_index(self.get_current_pub_item_index())

    def get_template_list_of_current_pub_item(self):
        """Get the template file list of the current publication item."""

        return self.get_template_list_by_pub_item_index(self.get_current_pub_item_index())

    def get_pub_info_list(self):
        """Get the list of publication info items."""

        return self._pub_info_list

    def a_pub_info_item_exists(self):
        """Return True if at least one publication info item exists or else False."""

        return len(self._pub_info_list) > 0

    def associate_pub_file_name_to_info_item_index(self, pub_file_name: str, pub_info_item_index: int):
        """Associate a publication file name to the index of a publication info item.

        :param pub_file_name: the publication file name.
        :param pub_info_item_index: the index of a publication info item.
        """
        self._pub_file_name_indexes[pub_file_name] = pub_info_item_index

    def get_index_of_pub_file_name(self, pub_file_name: str):
        """Get the index of a publication info item by its name.

        :param pub_file_name: the publication file name.
        :return: the index of a publication info item.
        """
        return self._pub_file_name_indexes[pub_file_name]

    def collect_tt_file_name(self, tt_file_names):
        """Collect the tt file names in a set without repeating the names.

        :param tt_file_names: a tt file name or a list of tt file names.
        """
        if type(tt_file_names) is list:
            for tt_file_name in tt_file_names:
                self._tt_file_names.add(tt_file_name)
        else:
            self._tt_file_names.add(tt_file_names)

    def get_tt_content_file_names(self):
        """Get the set of tt content file names."""

        return self._tt_file_names

    def get_file_format_of_pub_file(self, pub_file_name: str):
        """Get the file extension of the file of a publication info item.

        :param pub_file_name: the publication file name.
        :return: the extension of the file of a publication info item.
        """
        return self._pub_info_list[self.get_index_of_pub_file_name(pub_file_name)].get_file_format()

    def check_validity_of_file_names(self):
        """Since every elaborated json file is located on a json folder, every json file name has to be unique.
        Check if this condition is met."""

        input_file_set = set()
        template_file_set = set()

        for item in self._pub_info_list:
            simple_list = item.get_content_list()
            if type(simple_list[0]) is list:
                simple_list = simple_list[0]
            input_file_set.update(simple_list)
            template_file_set.update(item.get_template_list())

        for template_name in template_file_set:
            if template_name in input_file_set:
                raise ReaderError.TtNameUsedAsTemplateNameError(template_name)

    def print_writing_operation_info(self):
        """Print on the console the information about the writing operation done."""

        self.sort_detected_tt_files()
        note_of_not_updated = False

        print('Detected:', end=' ')
        for tt_file_name in self._detected_tt_files:
            file_name = tt_file_name.replace('.tt', '')
            print(file_name, end='')
            if tt_file_name in self._unchanged_json_files:
                print('*', end='')
                note_of_not_updated = True
            print('; ', end='')

        if note_of_not_updated:
            print('\n* The json of these files did not need to be updated.')
        else:
            print()
        print('All tagged text files have been processed.')


class Paths:
    """To get some relative or absolute folders or paths and other path utilities.

    Naming convention: path = folder + file name; file name includes file extension.
    The path and the folder can be relative (rel) or absolute (abs).
    """
    def __init__(self, spine_instance: Spine):
        """Instantiate the Paths object with variables to hold the computed paths and a reference to the Spine object
        to obtain information.

        :param spine_instance: the instantiated Spine object.
        """
        self.spine = spine_instance
        self.make_file_abs_folder = py_path[0]
        self.spine_rel_folder = ''
        self.tt_files_rel_folder = ''
        self.template_files_rel_folder = ''
        self.publication_files_rel_folder = ''

        self.current_tt_file_abs_path = ''
        self.current_json_file_abs_path = ''

    def get_tt_files_abs_folder(self):
        """Get the absolute folder of the tt content files."""

        return os.path.join(self.make_file_abs_folder, self.tt_files_rel_folder)

    def get_json_files_rel_folder(self):
        """Get the relative folder of the intermediate json files."""

        return os.path.join(self.tt_files_rel_folder, 'json')

    def get_json_files_abs_folder(self):
        """Get the absolute folder of the intermediate json files."""

        return os.path.join(self.make_file_abs_folder, self.spine_rel_folder, 'json')

    def get_template_files_abs_folder(self):
        """Get the absolute folder of the template files."""

        return os.path.join(self.make_file_abs_folder, self.spine_rel_folder, self.template_files_rel_folder)

    def get_template_files_rel_folder(self):
        """Get the relative folder of the template files."""

        return os.path.join(self.spine_rel_folder, self.template_files_rel_folder)

    def get_publication_files_abs_folder(self):
        """Get the absolute folder of the publication files."""

        return os.path.join(self.make_file_abs_folder, self.spine_rel_folder, self.publication_files_rel_folder)

    def get_tt_file_abs_path(self, file_name: str):
        """Get the absolute path of a tt content file.

        :param file_name: the name of the tt content file.
        :return: the absolute path of the tt content file.
        """
        return os.path.join(self.get_tt_files_abs_folder(), file_name)

    def get_json_file_abs_path(self, file_name: str):
        """Get the absolute path of an intermediate json file.

        :param file_name: the name of the json file.
        :return: the absolute path of the json file.
        """
        file_name = self.put_file_ext(file_name, 'json')
        return os.path.join(self.get_json_files_abs_folder(), file_name)

    def get_current_tt_file_abs_path(self):
        """Get the current and existing tt file abs path or else None is returned."""

        if os.path.isfile(self.current_tt_file_abs_path):
            return self.current_tt_file_abs_path

    def get_current_json_file_abs_path(self, existing_file: bool = True):
        """Get the current json file abs path, only if requested it should also exist.

        :param existing_file: True or False if the file should also exist, or it is not required.
        :return: the absolute path of the current json file or None if it should exist and it doesn't.
        """
        if existing_file is True:
            if os.path.isfile(self.current_json_file_abs_path):
                return self.current_json_file_abs_path
        else:
            return self.current_json_file_abs_path

    def get_template_file_abs_path(self, file_name: str):
        """Get the absolute path of a template file.

        :param file_name: the name of the template file.
        :return: the absolute path of the template file.
        """
        return os.path.join(self.get_template_files_abs_folder(), file_name)

    def get_publication_file_abs_path(self, file_name: str):
        """Get the absolute path of a publication file.

        :param file_name: the name of the publication file.
        :return: the absolute path of the publication file.
        """
        return os.path.join(self.get_publication_files_abs_folder(), file_name)

    def set_tt_files_rel_folder(self, rel_folder: str):
        """Set the relative folder of the tt content files.

        :param rel_folder: the relative folder of the tt content files.
        """
        if not self.tt_files_rel_folder:
            self.tt_files_rel_folder = rel_folder
        else:
            self.tt_files_rel_folder = os.path.join(self.tt_files_rel_folder, rel_folder)

    def set_current_tt_file_abs_path(self, abs_path: str):
        """Set the absolute path of the current tt content file.

        :param abs_path: the absolute path of the current tt content file.
        """
        self.current_tt_file_abs_path = abs_path

    def set_current_json_file_abs_path(self, abs_path: str):
        """Set the absolute path of the current tt content file.

        :param abs_path: the absolute path of the current tt content file.
        """
        if not os.path.isabs(abs_path):
            abs_path = self.get_json_file_abs_path(abs_path)
        self.current_json_file_abs_path = abs_path

    def prepare_reading_starting_from_spine_path(self, tt_spine_rel_path: str):
        """Print a message to inform about the used spine file. Set the relative folder of tt files to know where to
        find source code of the publication. Create the folder of json intermediate files to have a location for
        machine-readable files before to compose the publication. Append the json spine file to spine object because it
        needs to track every json file to be processed.

        :param tt_spine_rel_path: the relative path of tt spine file respect to make.py
        """
        print('Making a publication by reading ' + tt_spine_rel_path)
        if not os.path.isfile(tt_spine_rel_path):
            raise FileNotFoundError(f"The file {tt_spine_rel_path} does not exist.")

        self.spine_rel_folder = os.path.dirname(tt_spine_rel_path)
        self.set_tt_files_rel_folder(os.path.dirname(tt_spine_rel_path))
        self.make_directory(self.get_json_files_abs_folder())
        self.spine.append_json_file_name(os.path.basename(tt_spine_rel_path))

    @classmethod
    def put_file_ext(cls, file_name: str, extension: str):
        """Append a file extension to the file name only if that extension is not already present.

        :param file_name: the file name where to put the extension.
        :param extension: the extension without initial dot.
        :return: a new file name with the specified extension.
        """
        ext_index = file_name.rfind('.') + 1
        if ext_index == 0:
            file_name += '.' + extension
        elif not file_name[ext_index:] == extension:
            file_name = file_name[0:ext_index] + extension
        return file_name

    @classmethod
    def make_directory(cls, path: str):
        """Create a directory if it doesn't exist.

        :param path: the path of the folder.
        """
        if not os.path.exists(path):
            os.mkdir(path)


class Counters:
    """The collection of the counters."""

    _counters = {}

    class Scope(Enum):
        """The scope of a counter within which it is not reset."""

        FILE = 0
        PUBLICATION = 1

    class Counter:
        """A counter to count some elements in a publication"""

        def __init__(self, scope: object, start: int, step: int, value: int=None):
            """Initialize a counter with its scope and all the needed values.

            :param scope: the scope of the counter.
            :param start: the initial value.
            :param step: the number by which the counter has to advance.
            :param value: the current value of the counter.
            """
            if value is None:
                value = start

            self._scope = scope
            self._start = int(start)
            self._step = int(step)
            self._value = int(value)

        def reset(self):
            """Reset the current value to the starting value."""

            self._value = int(self._start)

        def get_value(self):
            """Get the current value of the counter."""

            return int(self._value)

        def take_a_step(self):
            """Advance of one step."""

            self._value += int(self._step)

    def reset_counters_with_scope_file(self):
        """Reset all the counters that have the scope of a file."""

        for counter in self._counters:
            if counter['scope'] == self.Scope.FILE:
                counter.reset()

    def put(self, counter_name: str, scope: object, start: int, step: int):
        """Put a new counter specifying the required initial values on an existing counter selected by its name.

        :param counter_name: the name of the counter.
        :param scope: the scope of the counter.
        :param start: the initial value.
        :param step: the number by which the counter has to advance.
        """
        self._counters[counter_name] = self.Counter(scope, start, step)

    def get_value(self, counter_name: str):
        """Get the current value of the counter selected by its name.

        :param counter_name: the name of the counter.
        :return: the current value of the counter.
        """
        return self._counters[counter_name].get_value()

    def take_a_step(self, counter_name: str):
        """Advance of one step the counter selected by its name.

        :param counter_name: the name of the counter.
        """
        self._counters[counter_name].take_a_step()


spine = Spine()
