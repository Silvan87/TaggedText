"""The Tagged Text Parser and Reader to get a model for the compositor."""

import os
import re
import json
from tt.controller.compositor import Compositor
from tt.controller.exceptions import *
from tt.model.regex import Regex
from tt.model.spine import spine, Counters
from tt.model.taggedtexts import Type as TtType
from tt.model.taggedtexts import TaggedTexts
from tt.model.templates import Templates
from tt.model.parsingtree import parsing_tree


class Parser:
    """It parses the tagged text syntax to produce a list of tagged strings collected in a parsing_tree model."""

    class Text:
        """A plain text of a tt file opened as a list of lines. The class is responsible for parsing the special
        characters of the tt language and producing an intermediate Json file meant to be machine-readable."""

        _lines = []
        _current_line_index = -1
        _current_line = ''
        _after_tag_line = ''
        _current_text_value = ''
        _previous_level = 0
        _current_level = 1
        _chunks = []
        _previous_parents = 0
        _parent_stack = []
        _hashtag_id_name_to_apply = ''

        @classmethod
        def reset_cursors(cls):
            """Reset the cursors related to the indexes to walking through the text."""

            cls.start_line()

        @classmethod
        def reset_tag_context(cls):
            """Reset the context of a tag that consists in information about the tag."""

            cls.current_tag = ''
            cls._current_text_value = ''
            cls._previous_level = 0
            cls._previous_parents = 0
            cls._parent_stack.clear()

        @classmethod
        def start_line(cls):
            """Set the index of the text to the first line, if a line is available."""

            if len(cls._lines) > 0:
                cls._current_line_index = 0
                cls._current_line = cls._lines[0].strip()
            else:
                cls._current_line_index = -1

        @classmethod
        def next_line(cls):
            """Set the index of the text to the next line, if available, and read its content."""

            cls._current_line_index += 1
            if cls._current_line_index < len(cls._lines):
                cls._current_line = cls._lines[cls._current_line_index].strip()
            else:
                cls._current_line_index = -1
                cls._current_line = ''

        @classmethod
        def is_there_a_current_line(cls):
            """Get the state of the index if there is or not a new current line.

            :return: True or False if a new current line is present or not.
            """

            if cls._current_line_index < 0 or cls._current_line_index >= len(cls._lines):
                return False
            else:
                return True

        @classmethod
        def is_current_line_not_empty(cls):
            """Get the state of a line if it is or not empty.

            :return: True or False if the current line is empty or not.
            """

            return bool(cls._current_line)

        @classmethod
        def strip_escape_char_from_beginning_and_end_of_line(cls, line: str):
            """Remove the escape char in the beginning and in the end of the line.

            :param line: the line where to check the escape chars.
            :return: the line edited.
            """
            if len(line) > 0 and line[0] == '\\':
                line = line[1:]

            if len(line) > 0 and line[-1] == '\\':
                line = line[:-1]

            return line

        @classmethod
        def look_for_hashtag_without_value(cls):
            """Look for a hashtag without value in a text line.

            :return: True or False if a hashtag without value is found or not.
            """

            # Case 1: only a double hashtag
            match = re.search('^' + Regex.hashtag_no_value + '$', cls._current_line)
            if match:
                tag_name = match.group(0)[1:-1]
                parsing_tree.append_tagged_piece('', tag_name)
                return True

            # Case 2: full line that starts with double hashtag
            match = re.search('^' + Regex.hashtag_no_value, cls._current_line)
            if match:
                cls.pick_multi_text_lines(text_to_prepend=cls._current_line)
                cls.evaluate_presence_of_inline_tags(cls._current_text_value, '')
                return True

        @classmethod
        def look_for_hashtag(cls):
            """Try to look for a hashtag in a text line managing exceptions and errors.

            :return: True or False if a hashtag is found or not.
            """
            try:
                return cls.try_to_look_for_hashtag()

            except Exception as e:
                raise e

        @classmethod
        def try_to_look_for_hashtag(cls):
            """Look for a hashtag in a text line taking all the implied following lines.

            :return: True or False if a hashtag is found or not.
            """
            search_start = cls._current_line_index
            search_steps = 0

            while search_start + search_steps < len(cls._lines):
                cls._current_text_value = ''
                forward_line = cls._lines[search_start + search_steps].strip()

                match_hashtag = re.search('^' + Regex.hashtag, forward_line)
                if match_hashtag:
                    tag_name = match_hashtag.group(0)

                    # the level of the tag is given by the number of # chars in the tag name
                    tag_level = len(tag_name)
                    tag_name = tag_name.lstrip('#')
                    tag_level -= len(tag_name)

                    # if this line has a top-level tag, the current processed hashtag is finished
                    if tag_level == 1 and search_steps > 0:
                        cls._previous_level = 0
                        break

                    # it checks the next level is introduced gradually (#, ##, ###, etc.)
                    if tag_level - cls._previous_level > 1:
                        raise ParserError.SkippedDeeperTagLevelError(
                            spine.paths.get_current_tt_file_abs_path(),
                            search_start + search_steps + 1,
                            tag_level,
                            cls._previous_level
                        )

                    if tag_level < cls._previous_level:
                        cls._parent_stack = cls._parent_stack[:tag_level - 1]

                    elif tag_level == cls._previous_level:
                        cls._parent_stack = cls._parent_stack[:-1]

                    cls._after_tag_line = forward_line[len(tag_name) + tag_level:].strip()

                    # between the hashes ## and the tag name there could be a space,
                    # but you can remove it after the calculation for the _after_tag_line
                    tag_name = tag_name.lstrip()

                    if cls._after_tag_line:
                        cls.look_for_hashtag_id()
                        if cls._after_tag_line:
                            cls._after_tag_line += '\n'

                    cls._current_level = tag_level
                    cls.pick_multi_text_lines(cls._after_tag_line)
                    search_steps = cls._current_line_index - search_start

                    cls._current_line_index = search_start + search_steps + 1
                    current_parent_id = len(parsing_tree.get_json_data())
                    cls._parent_stack.append(current_parent_id)

                    parsing_tree.append_tagged_piece([current_parent_id + 1], tag_name)
                    id_of_piece_with_id_name = 0
                    if cls._hashtag_id_name_to_apply:
                        id_of_piece_with_id_name = parsing_tree.get_number_of_parsed_pieces() - 1

                    cls.evaluate_presence_of_inline_tags(cls._current_text_value)
                    search_steps = cls._current_line_index - search_start - 1

                    if tag_level > 1:
                        grandparent_id = cls._parent_stack[tag_level - 2]
                        grandparent_value = parsing_tree.get_value_of_tagged_piece(grandparent_id)
                        if isinstance(grandparent_value, list):
                            if current_parent_id not in grandparent_value:
                                parsing_tree.append_id_to_tagged_piece_value(grandparent_id, current_parent_id)

                    if cls._hashtag_id_name_to_apply:
                        id_of_id_name = parsing_tree.get_number_of_parsed_pieces()
                        parsing_tree.append_id_to_tagged_piece_value(id_of_piece_with_id_name, id_of_id_name)
                        parsing_tree.append_tagged_piece(cls._hashtag_id_name_to_apply, '_id_name')
                        cls._hashtag_id_name_to_apply = ''

                    cls._previous_level = tag_level
                else:
                    break
                search_steps += 1

            if search_steps > 0:
                cls._current_line_index = search_start + search_steps - 1
                return True
            else:
                return False

        @classmethod
        def look_for_hashtag_id(cls):
            """Look for the hashtag id in _after_tag_line.

            :return: True or False if the hashtag id is found or not.
            """

            match = re.search(Regex.hashtag_id, cls._after_tag_line)

            # If there is an escape \ before the special chars, ignore them
            if match:
                if match.start() - 1 >= 0:
                    if cls._after_tag_line[match.start() - 1] == '\\':
                        match = None

            if match:
                cls._hashtag_id_name_to_apply = match.group(0)[1:]
                cls._after_tag_line = cls._after_tag_line[len(cls._hashtag_id_name_to_apply) + 1:].strip()
                return True
            else:
                return False

        @classmethod
        def look_for_comment(cls):
            """Look for a comment in a text line.

            :return: True or False if a comment is found or not.
            """

            match = re.search(Regex.comment, cls._current_line)
            if match:
                return True

            match = re.search(Regex.comment_delimiter, cls._current_line)
            if match:
                search_start = cls._current_line_index
                search_steps = 1
                while search_start + search_steps < len(cls._lines):
                    match = re.search(Regex.comment_delimiter, cls._lines[search_start + search_steps].strip())
                    if match:
                        break
                    search_steps += 1

                cls._current_line_index += search_steps
                return True
            else:
                return False

        @classmethod
        def look_for_text_without_tag(cls):
            """Look for text without any tag in the next text lines.

            :return: True as a confirmation the search has been done.
            """

            cls.pick_multi_text_lines(cls._current_line)
            next_piece_id = parsing_tree.get_number_of_parsed_pieces() + 1
            parsing_tree.append_tagged_piece([next_piece_id], '')
            cls.evaluate_presence_of_inline_tags(cls._current_text_value)
            return True

        @classmethod
        def pick_multi_text_lines(cls, text_to_prepend: str = ''):
            """Pick multi text lines until to find a new tag.

            :param text_to_prepend: if a previous line started with a tag and there is some text after the tag, this
            parameter can prepend the text after the tag to the collected multi lines text.
            """
            search_start = cls._current_line_index
            search_steps = 1
            while search_start + search_steps < len(cls._lines):
                forward_line = cls._lines[search_start + search_steps].lstrip()
                match = re.search('^' + Regex.hashtag, forward_line)
                # TODO BUG currently this cycle that picks lines it is not ready to skip the comments
                if match:
                    break
                else:
                    cls._current_text_value += forward_line
                search_steps += 1

            cls._current_line_index = search_start + search_steps - 1
            cls._current_text_value = text_to_prepend + cls._current_text_value
            cls._current_text_value = cls._current_text_value.rstrip().replace('\n', '\\n')

        @classmethod
        def give_next_text_to_tag(cls, tag_name: str, after_tag: str):
            """Give to the current tag the next text processed to find inline tags.

            :param tag_name: the name of the current tag.
            :param after_tag: the part of text line after the found tag.
            """
            if cls._current_line_index >= len(cls._lines):
                parsing_tree.append_tagged_piece('', tag_name)
                return

            cls._current_text_value = cls._lines[cls._current_line_index].strip()
            match = re.search(Regex.not_normal_text, cls._current_text_value)
            if match:
                parsing_tree.append_tagged_piece('', tag_name)
                return

            search_start = cls._current_line_index
            search_steps = 1

            while search_start + search_steps < len(cls._lines):
                forward_line = cls._lines[search_start + search_steps].strip()
                match = re.search(Regex.not_normal_text, forward_line)
                if match:
                    break
                else:
                    cls._current_text_value += '\n' + forward_line
                search_steps += 1

            cls._current_line_index += search_steps - 1
            cls._current_text_value = after_tag + cls._current_text_value
            cls._current_text_value = cls._current_text_value.rstrip().replace('\n', '\\n')
            cls._previous_parents = 0
            cls.evaluate_presence_of_inline_tags(cls._current_text_value, tag_name)

        @classmethod
        def evaluate_presence_of_inline_tags(cls, line: str, tag_name: str = ''):
            """Evaluate if a line is divided by inline tags and use a list of child indexes to refer to the line pieces
            or else use the plain line.

            :param line: the line to evaluate.
            :param tag_name: if available, the current tag name that can receive the line (divided or not).
            """

            # If a tag applies to multiple tagged text strings, there will be an array of indexes
            # Those indexes refer to the future append strings with only 1 level of depth
            parent_position = parsing_tree.get_number_of_parsed_pieces()
            child_indexes = cls.look_for_inline_tags(line)
            if child_indexes:
                parsing_tree.insert_parsed_piece(parent_position, child_indexes, tag_name)
            else:
                if cls._current_text_value or tag_name:
                    parsing_tree.append_tagged_piece(line, tag_name)
                else:
                    parsing_tree.remove_first_piece_id_from_piece_value(cls._parent_stack[-1])

        @classmethod
        def look_for_inline_tags(cls, line: str):
            """Look for inline tags in a text line.

            :param line: the line where to look for inline tags.
            :return: a list of IDs of the new strings found after the processing of the inline tags. If the line is not
            split, False is returned.
            """
            child_ids = []

            # The chunk list needs to be a new object for every sub-line
            chunks = cls.split_line_into_chunks(line).copy()
            if len(chunks) < 2:
                return False
            else:
                cls._previous_parents += 1
                i = 0
                while i < len(chunks):
                    child_ids.append(parsing_tree.get_number_of_parsed_pieces() + cls._previous_parents)
                    if re.search('^' + Regex.open_inline_tag + '$', chunks[i]):
                        sub_line = chunks[i + 1]
                        tag_name = chunks[i][2:-2]
                        parents_before_nesting = cls._previous_parents
                        cls.evaluate_presence_of_inline_tags(sub_line, tag_name)
                        cls._previous_parents = parents_before_nesting
                        i += 3
                    elif re.search('^' + Regex.hashtag_no_value + '$', chunks[i]):
                        tag_name = chunks[i][1:-1]
                        parsing_tree.append_tagged_piece('', tag_name)
                        i += 1
                    else:
                        parsing_tree.append_tagged_piece(chunks[i], '')
                        i += 1
                return child_ids

        @classmethod
        def split_line_into_chunks(cls, line: str):
            """Split a text line in substrings according to the inline tags found.

            :param line: the line where to look for inline tags.
            :return: a list of substrings in which the line has been split.
            """
            regex = Regex
            cls._chunks.clear()
            parsing_progression_index = 0
            # open_tag_start_index = 0
            # open_tag_end_index = 0
            closed_tag_start_index = 0
            closed_tag_end_index = 0

            while parsing_progression_index < len(line):
                number_of_nested_open_tags = 0
                closed_tag_match = False
                main_open_tag_match = re.search(regex.open_inline_tag, line[parsing_progression_index:])

                # If there is an escape \ before the special chars, ignore them
                if main_open_tag_match:
                    if main_open_tag_match.start() - 1 >= 0:
                        if line[main_open_tag_match.start() - 1] == '\\':
                            main_open_tag_match = None

                if main_open_tag_match:
                    open_tag_start_index = parsing_progression_index + main_open_tag_match.start()
                    if closed_tag_end_index != open_tag_start_index:
                        cls.look_for_inline_hashtag_without_value(line[closed_tag_end_index:open_tag_start_index])
                    open_tag_end_index = parsing_progression_index + main_open_tag_match.end()
                    parsing_progression_index = open_tag_end_index

                    while number_of_nested_open_tags >= 0:
                        closed_tag_match = re.search(regex.closed_inline_tag, line[parsing_progression_index:])
                        if not closed_tag_match:
                            parsing_progression_index = len(line)
                        else:
                            nested_open_tag_match = re.search(regex.open_inline_tag, line[parsing_progression_index:])
                            if nested_open_tag_match:
                                if nested_open_tag_match.start() < closed_tag_match.start():
                                    # Each opening tag actually includes a closing tag
                                    # So the end of the found closing tag is the end of the opening tag
                                    # Moreover, it needs to find the closing tag of the found nested opening tag
                                    # You can count the opening tags and subtract the respective closing tags
                                    number_of_nested_open_tags += 1
                                    parsing_progression_index += closed_tag_match.end()
                                    continue
                            number_of_nested_open_tags -= 1
                            closed_tag_start_index = parsing_progression_index + closed_tag_match.start()
                            parsing_progression_index += closed_tag_match.end()
                            closed_tag_end_index = parsing_progression_index

                    cls._chunks.append(line[open_tag_start_index:open_tag_end_index])
                    if closed_tag_match:
                        cls.look_for_inline_hashtag_without_value(line[open_tag_end_index:closed_tag_start_index])
                        cls._chunks.append(line[closed_tag_start_index:closed_tag_end_index])
                    else:
                        cls.look_for_inline_hashtag_without_value(line[open_tag_start_index:])
                else:
                    if parsing_progression_index < len(line):
                        cls.look_for_inline_hashtag_without_value(line[parsing_progression_index:])
                    break
            return cls._chunks

        @classmethod
        def look_for_inline_hashtag_without_value(cls, line: str):
            """Look for all the inline hashtags without value in a text line and add to _chunks the new substrings
            generated by the presence of these tags.

            :param line: the text line where to look for.
            """
            match_hashtag_no_value = re.search(Regex.hashtag_no_value, line)

            # If there is an escape \ before the special chars, ignore them
            if match_hashtag_no_value:
                if match_hashtag_no_value.start() - 1 >= 0:
                    if line[match_hashtag_no_value.start() - 1] == '\\':
                        match_hashtag_no_value = None

            if match_hashtag_no_value:
                if match_hashtag_no_value.start() > 0:
                    cls._chunks.append(line[0:match_hashtag_no_value.start()])
                cls._chunks.append(line[match_hashtag_no_value.start():match_hashtag_no_value.end()])
                cls.look_for_inline_hashtag_without_value(line[match_hashtag_no_value.end():])
            else:
                if line != '':
                    cls._chunks.append(line)

    @classmethod
    def parse_spine_and_all_required_files(cls, tt_spine_rel_path: str):
        """Parse every required files (tt contents and templates) starting from spine file.

        :param tt_spine_rel_path: the relative path of tt spine file respect to make.py
        """
        _Reader.parse_spine(tt_spine_rel_path)
        _Reader.parse_required_tagged_texts()


class _Reader:
    """It collects methods to open the tt files and to read the raw text in order to produce a machine-readable
    structure in the memory."""

    @classmethod
    def parse_spine(cls, tt_spine_rel_path: str):
        """Parse the spine file to prepare the steps of the whole process setting all the needed variables.

        :param tt_spine_rel_path: the relative path of tt spine file respect to make.py
        """
        spine.initialize()
        spine.paths.prepare_reading_starting_from_spine_path(tt_spine_rel_path)
        cls._parse_tt_file(os.path.basename(tt_spine_rel_path), TtType.SPINE)

        try:
            cls._try_to_parse_spine()

        except (ReaderError.TtNameUsedAsTemplateNameError,
                ReaderError.PublicationFileWithoutContentFile) as error:
            error.stop_process_with_error_message()

    @classmethod
    def _try_to_parse_spine(cls):

        class _TagManager:
            """To manage the special tags used in the spine file. The subclass Tag allows to extend special tags."""

            @classmethod
            def get_tag_names(cls):
                """Use all method names inside class Tag to get the managed tag names.

                :return: list of managed tag names.
                """
                return [name.replace('_', '-') for name in dir(cls.Tag)
                        if callable(getattr(cls.Tag, name)) and not name.startswith('__')]

            @classmethod
            def get_method_name_from_tag(cls, tag_name: str):
                """Get the method name from a tag name. They are the same, the only difference is the snake_case for the
                methods and the kebab-case for the tags.

                :param tag_name: the tag name of which the method is retrieved.
                :return: the method associated to the tag.
                """

                return tag_name.replace('-', '_')

            class Tag:
                """All the managed special tags in the spine file. You can create a new class method with the name in
                snake_case, then you can use in the spine file the new tag with the same name of the new method but in
                kebab-case."""

                @classmethod
                def template_path(cls):
                    """To define the path where to find the templates."""

                    spine.set_template_path(Compositor.get_raw_first_value_of_item(definition))

                @classmethod
                def publication_path(cls):
                    """To define the path where to write the publication."""

                    spine.set_publication_path(Compositor.get_raw_first_value_of_item(definition))

                @classmethod
                def var(cls):
                    """To define a variable to use in the templates."""

                    var_name = Compositor.get_raw_first_value_of_item(definition)
                    value = Compositor.get_raw_subtag_value_of_tag(definition, 'text')
                    spine.set_variable(var_name, value)

                @classmethod
                def file_list(cls):
                    """To give a name to a list of files and call the list instead of each file"""

                    list_name = Compositor.get_raw_first_value_of_item(definition)
                    file_names = Regex.whitespace_split(
                        Compositor.get_raw_subtag_value_of_tag(definition, 'list')
                    )
                    spine.set_file_names_to_a_list(list_name, file_names)

                @classmethod
                def publish(cls):
                    """To publish a file or a list of files defining an extension (file format), a content file or a
                    list of content files and a template or a list of templates."""

                    pub_format = Compositor.get_raw_subtag_value_of_tag(definition, 'format')

                    pub_file_and_list_names = Regex.whitespace_split(
                        Compositor.get_raw_first_value_of_item(definition)
                    )
                    pub_file_names = []

                    for name in pub_file_and_list_names:
                        name_with_format = name.split('.')
                        file_name = name_with_format[0]

                        if pub_format == '' and len(name_with_format) > 1:
                            pub_format = name_with_format[1]

                        if spine.has_file_list_named(name):
                            list_name = name
                            for name_from_list in spine.get_file_name_list(list_name):
                                pub_file_names.append(name_from_list)
                        else:
                            pub_file_names.append(name)

                    content_file_and_list_names = Regex.whitespace_split(
                        Compositor.get_raw_subtag_value_of_tag(definition, 'content')
                    )
                    content_file_names = []

                    for name in content_file_and_list_names:
                        name_with_format = name.split('.')
                        file_name = name_with_format[0]

                        if spine.has_file_list_named(name):
                            list_name = name
                            for name_from_list in spine.get_file_name_list(list_name):
                                content_file_names.append(name_from_list)
                        else:
                            content_file_names.append(name)

                    template_file_and_list_names = Regex.whitespace_split(
                        Compositor.get_raw_subtag_value_of_tag(definition, 'template')
                    )
                    template_file_names = []

                    for name in template_file_and_list_names:
                        if spine.has_file_list_named(name):
                            for name_from_list in spine.get_file_name_list(name):
                                Templates.initialize(name_from_list)
                                template_file_names.append(name_from_list)
                        else:
                            Templates.initialize(name)
                            template_file_names.append(name)

                    if len(pub_file_names) > 1:
                        if len(pub_file_names) != len(content_file_names):
                            raise ReaderError.PublicationFileWithoutContentFile
                        else:
                            for i, pub_name in enumerate(pub_file_names):
                                spine.append_pub_info_item(
                                    pub_name, pub_format, content_file_names[i], template_file_names
                                )
                    else:
                        spine.append_pub_info_item(
                            pub_file_names[0], pub_format, content_file_names, template_file_names
                        )

        # Pass the json data to parsing_tree object
        with open(spine.paths.get_current_json_file_abs_path()) as json_file_stream:
            parsing_tree.set_json_data(json.load(json_file_stream))
            json_file_stream.close()

        # Check if each spine tag exists in the TagManager and call the related method
        for index, definition in enumerate(parsing_tree.get_json_data()):
            spine.Definition.set(definition)

            if spine.Definition.has_tag(_TagManager.get_tag_names()):
                tag_method_name = _TagManager.get_method_name_from_tag(spine.Definition.get_tag())
                getattr(_TagManager.Tag, tag_method_name)()

        # Each tt file name has to be unique. Check if this condition is met.
        spine.check_validity_of_file_names()

    @classmethod
    def parse_required_tagged_texts(cls):
        """Parse all the needed tt files (tt contents and templates) into json files or load them from the previous
        up-to-date json files. Then prepare the triggers tags and the rules from the templates."""

        # Associate each publication file name to a publication info item thru an index and collect each pub file name.
        pub_info_index = 0
        for pub_item in spine.get_pub_info_list():
            spine.associate_pub_file_name_to_info_item_index(pub_item.get_file_name(), pub_info_index)
            for input_file_name in pub_item.get_content_list():
                spine.collect_tt_file_name(input_file_name)
            pub_info_index += 1

        # Parse each tt template file.
        for input_file_name in Templates.get_tt_file_names():
            input_file_name = spine.paths.put_file_ext(input_file_name, 'tt')
            cls._parse_tt_file(input_file_name, TtType.TEMPLATE)

        # Parse each tt content file.
        for tt_file_name in spine.get_tt_content_file_names():
            tt_file_name = spine.paths.put_file_ext(tt_file_name, 'tt')
            cls._parse_tt_file(tt_file_name, TtType.CONTENT)
            spine.counters.reset_counters_with_scope_file()

        cls._load_tagged_texts()
        cls._prepare_trigger_tags_and_rules_from_templates()

    @classmethod
    def _parse_tt_file(cls, tt_file_name: str, tt_type: TtType = TtType.CONTENT):
        """Parse a tt file to obtain a json. But first, check if an up-to-date version of that json is available and
        also save the elaborated json for the next time.

        :param tt_file_name: the name of the tagged text without extension.
        :param tt_type: the type of the tagged text file.
        """
        TaggedTexts.set_current_tt_file(tt_file_name, tt_type)

        try:
            cls._parse_text_lines(tt_file_name)
            cls._save_json_file()

        except FlowException.ReadJsonStillUpToDateException:
            spine.append_unchanged_json_file(tt_file_name)

    @classmethod
    def _is_last_read_version_of_json_usable(cls, tt_file_name: str, tt_type: TtType = TtType.CONTENT):
        """Check if the last read json file is still a usable version, or it has to be generated again from the tt
        content file.

        :param tt_file_name: the name of the tt file of which the old json eventually can be used again.
        :param tt_type: the type of the tt file.
        :return: True or False according to the possibility to use the json again avoiding generating it again.
        """
        template_mod_date = 0
        if tt_type == TtType.TEMPLATE:
            spine.paths.set_current_tt_file_abs_path(spine.paths.get_template_file_abs_path(tt_file_name))
        else:
            spine.paths.set_current_tt_file_abs_path(spine.paths.get_tt_file_abs_path(tt_file_name))
            if spine.a_pub_info_item_exists():
                associated_template_list = spine.get_template_list_of_current_pub_item()
                template_mod_date = Templates.get_latest_modification_date_from_template_name_list(
                    associated_template_list)
        json_file_name = spine.paths.put_file_ext(tt_file_name, 'json')
        spine.paths.set_current_json_file_abs_path(json_file_name)
        spine.append_detected_tt_file(tt_file_name)

        # Load json file only if the tt source and all of the its templates are older than it
        json_file_exists = spine.paths.get_current_json_file_abs_path()
        is_tt_source_newer = True
        is_one_template_newer = True

        if json_file_exists:
            json_mod_date = os.path.getmtime(spine.paths.get_current_json_file_abs_path())
            tt_mod_date = os.path.getmtime(spine.paths.get_current_tt_file_abs_path())
            is_tt_source_newer = json_mod_date < tt_mod_date
            is_one_template_newer = json_mod_date < template_mod_date

        if not json_file_exists or is_tt_source_newer or is_one_template_newer:
            return False
        else:
            return True

    @classmethod
    def _parse_text_lines(cls, tt_file_name: str):
        """Parse each text line looking for the special chars of the tt syntax and producing the parsed content.

        :param tt_file_name: the tt file name to parse.
        """
        if cls._is_last_read_version_of_json_usable(tt_file_name, TaggedTexts.get_current_tt_type()):
            raise FlowException.ReadJsonStillUpToDateException

        cls._read_all_text_lines()
        parsing_tree.clear_parsed_data()
        Parser.Text.reset_cursors()
        while Parser.Text.is_there_a_current_line():
            if Parser.Text.is_current_line_not_empty():
                Parser.Text.look_for_hashtag_without_value() or \
                    Parser.Text.look_for_hashtag() or \
                    Parser.Text.look_for_comment() or \
                    Parser.Text.look_for_text_without_tag()
                Parser.Text.reset_tag_context()
            Parser.Text.next_line()

    @classmethod
    def _read_all_text_lines(cls):
        """Read all the text lines from the textual tt file."""

        f = open(spine.paths.get_current_tt_file_abs_path(), 'r')
        Parser.Text._lines = f.readlines()
        f.close()

    @classmethod
    def _save_json_file(cls):
        """Save as a json file in the permanent memory in the dedicated json folder the parsed content."""

        f = open(spine.paths.get_current_json_file_abs_path(existing_file=False), 'w')
        f.write('[\n')
        is_first_item = True
        for item in parsing_tree.get_json_data():
            if is_first_item:
                is_first_item = False
            else:
                f.write(',\n')
            f.write('[')
            if isinstance(item[0], str):
                if len(item[0]) > 0 and item[0][-1] == '\\':
                    item[0] = item[0][:-1]
                line_with_managed_escapes = (
                    item[0].replace('\\n', '\n')
                    .replace('\\', '\\\\').replace('"', '\\"')
                    .replace('\n', '\\n')
                )
                f.write('"' + line_with_managed_escapes + '"')
            else:
                if len(item[0]) == 0:
                    f.write('""')
                else:
                    f.write(str(item[0]))
            f.write(', "' + str(item[1]) + '"')
            f.write(']')
        f.write('\n]')
        f.close()

    @classmethod
    def _load_tagged_texts(cls):
        """Load all parsed tt content files in the memory as json files."""

        for file_name in spine.get_tt_content_file_names():
            json_file_path = spine.paths.get_json_file_abs_path(file_name)
            with open(json_file_path) as json_file_stream:
                TaggedTexts.put(file_name, json.load(json_file_stream))
                json_file_stream.close()

    @classmethod
    def _prepare_trigger_tags_and_rules_from_templates(cls):
        """Prepare trigger tags from the templates and associate the relative template rule to them.

        Load all the template tt files in the memory as json files in the 'rules' key of each template.
        """
        TaggedTexts.set_current_tt_type(TtType.TEMPLATE)
        for template_name in Templates.get_tt_file_names():
            input_file_name = spine.paths.put_file_ext(template_name, 'json')
            with open(spine.paths.get_json_file_abs_path(input_file_name)) as json_file_stream:
                parsing_tree.set_json_data(json.load(json_file_stream))
                json_file_stream.close()
            Compositor.set_content_reference(spine.get_tt_content_file_names())
            Compositor.set_template_reference([template_name])
            Compositor.set_current_template_name(template_name)
            Templates.set_rules(parsing_tree.get_json_data(), template_name)

            for index, item in enumerate(parsing_tree.get_json_data()):
                if item[1] in ['file-opening', 'file-ending']:
                    Templates.set_trigger(tag_name=item[1], rule_index=index, template_name=template_name)

                elif item[1] in ['catching-tag', 'tag']:
                    trigger_tag = Compositor.get_raw_first_value_of_item(item)
                    Templates.set_trigger(tag_name=trigger_tag, rule_index=index, template_name=template_name)

                elif item[1] == 'tag-list':
                    trigger_tags = Regex.whitespace_split(Compositor.get_raw_first_value_of_item(item))
                    for trigger_tag in trigger_tags:
                        Templates.set_trigger(
                            tag_name='_list_' + trigger_tag,
                            rule_index=index,
                            template_name=template_name
                        )

                elif item[1] == 'counter':
                    counter_name = Compositor.get_raw_first_value_of_item(item)
                    scope = Compositor.get_raw_subtag_value_of_tag(item, 'scope', Counters.Scope.FILE)
                    step = Compositor.get_raw_subtag_value_of_tag(item, 'step', 1)
                    start = Compositor.get_raw_subtag_value_of_tag(item, 'start', 1)
                    spine.counters.put(counter_name, scope, start, step)
