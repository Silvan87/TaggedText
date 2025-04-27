import copy
from enum import Enum
from tt.model.spine import spine


class Type(Enum):
    """The type of tagged text."""

    SPINE = 0
    CONTENT = 1
    TEMPLATE = 2


class TaggedTexts:
    """The parsed tagged texts. Each one accessible through the public methods specifying the related tt file name
    without extension."""

    _tagged_texts = {}
    _joined_tagged_texts = {}
    _current_tt_type = Type.CONTENT

    @classmethod
    def reset(cls):
        """Reset TaggedTexts removing all the tagged texts."""

        cls._tagged_texts = {}
        cls._joined_tagged_texts = {}
        cls._current_tt_type = Type.CONTENT

    @classmethod
    def put(cls, tt_file_name: str, json_file_content: list):
        """Add or rewrite the parsed content of a tagged text.

        :param tt_file_name: tt file name without extension.
        :param json_file_content: the content of a tagged text in json format.
        """
        cls._tagged_texts[tt_file_name] = json_file_content

    @classmethod
    def get(cls, tt_file_name):
        """Get the parsed content of one or more tagged texts.

        :param tt_file_name: tt file name without extension, even a list of tt file names.
        :return: the content of a tagged text in json format.
        """
        if type(tt_file_name) is list:
            if len(tt_file_name) > 1:
                tuple_key = tuple(tt_file_name)
                if tuple_key not in cls._joined_tagged_texts:
                    joined_tagged_text = []
                    i = 0
                    while i < len(tt_file_name):
                        reached_line_number = len(joined_tagged_text)
                        copied_tagged_text = copy.deepcopy(cls._tagged_texts[tt_file_name[i]])
                        joined_tagged_text += cls._increase_tagged_text_indexes(copied_tagged_text, reached_line_number)
                        i += 1

                    cls._joined_tagged_texts[tuple_key] = joined_tagged_text
                    return joined_tagged_text
                else:
                    return cls._joined_tagged_texts[tuple_key]
            else:
                return cls._tagged_texts[tt_file_name[0]]
        else:
            return cls._tagged_texts[tt_file_name]

    @classmethod
    def _increase_tagged_text_indexes(cls, tagged_text: list, increment: int):
        """Increase the indexes of a tagged text with an integer number.

        :param tagged_text: the tagged text to edit.
        :param increment: an integer number to increase all the indexes.
        :return: a tagged text increased with the requested number of indexes.
        """
        if increment > 0:
            line_number = len(tagged_text)
            for line_index in range(0, line_number):
                if type(tagged_text[line_index][0]) is list:
                    id_number = len(tagged_text[line_index][0])
                    for id_index in range(0, id_number):
                        tagged_text[line_index][0][id_index] += increment

        return tagged_text

    @classmethod
    def get_tt_name_related_to_an_item_in_joined_tts(cls, tt_file_name_list, item_index: int):
        """Get the tt name related to an item in a list of joined tagged texts.

        :param tt_file_name_list: the list of joined tagged texts.
        :param item_index: the index of the item.
        :return: the name of the original tagged text before the conjunction.
        """
        tt_lengths = []
        farthest_reached_index = 0
        for tt_name in tt_file_name_list:
            farthest_reached_index += len(cls._tagged_texts[tt_name]) - 1
            tt_lengths.append(farthest_reached_index)

        for file_index, farthest_index in enumerate(tt_lengths):
            if item_index <= farthest_index:
                return tt_file_name_list[file_index]

        return None

    @classmethod
    def get_item_number(cls, tt_file_name: str | list):
        """Get the number of the items of a tagged text.

        :param tt_file_name: the tt file name without extension.
        :return: the number of the items of a tagged text content.
        """
        item_number = 0
        if type(tt_file_name) is list:
            i = 0
            while i < len(tt_file_name):
                item_number += len(cls._tagged_texts[tt_file_name[i]])
                i += 1
            return item_number
        else:
            return len(cls._tagged_texts[tt_file_name])

    @classmethod
    def get_tagged_line(cls, tt_file_name: str | list, line_index: int):
        """Get the tagged line from a tagged text using the line index.

        :param tt_file_name: the tt file name without extension.
        :param line_index: the index of the tagged line.
        :return: the tagged line that is a list of 2 items (value and tag).
        """
        if type(tt_file_name) is list:
            i = 0
            while line_index >= len(tt_file_name[i]):
                line_index -= len(tt_file_name[i]) - 1
                i += 1
            actual_name = tt_file_name[i]
        else:
            actual_name = tt_file_name

        return cls._tagged_texts[actual_name][line_index]

    @classmethod
    def get_depth_level(cls, tt_file: str | list, index_to_check: int):
        """Get the level of the piece (tagged or not) in its content.

        :param tt_file: the tt file name or the tt file content. It will be used to have tt file content.
        :param index_to_check: the index of the tagged or not text piece to know the level in the structured text.
        :return: the level of the text piece.
        """
        content_data = tt_file
        if type(tt_file) is str:
            content_data = cls.get(tt_file)

        current_previous_index = 0
        level = 1
        new_level = True

        while new_level:
            new_level = False

            for piece in content_data:
                if current_previous_index >= index_to_check:
                    break
                if type(piece[0]) is list:
                    for sub_piece_index in piece[0]:
                        if index_to_check == sub_piece_index:
                            level += 1
                            index_to_check = current_previous_index
                            new_level = True
                            break

                current_previous_index += 1

        return level

    @classmethod
    def get_current_tt_type(cls):
        """Get the current tagged text type."""

        return cls._current_tt_type

    @classmethod
    def set_current_tt_type(cls, tt_type: Type):
        """Set the current tagged text type.

        :param tt_type: the tagged text type.
        """
        cls._current_tt_type = tt_type

    @classmethod
    def set_current_tt_file(cls, tt_file_name: str, tt_type: Type = None):
        """Set the current tagged text file path and the type for the current process on spine.Paths.

        :param tt_file_name: the name of the tagged text file without extension or folder.
        :param tt_type: the tagged text type. The default is the current tt file type.
        """
        if tt_type is None:
            tt_type = cls._current_tt_type
        else:
            cls._current_tt_type = tt_type

        if tt_type == Type.TEMPLATE:
            spine.paths.set_current_tt_file_abs_path(spine.paths.get_template_file_abs_path(tt_file_name))
        else:
            spine.paths.set_current_tt_file_abs_path(spine.paths.get_tt_file_abs_path(tt_file_name))
