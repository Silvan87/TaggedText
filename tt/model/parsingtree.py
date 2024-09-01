"""Parsing Tree is a list of tagged pieces to store the result of the process that converts a tagged text file in a JSON
tagged tree structure. It is specialized to assist the process along its elaboration."""

import re
from tt.model.regex import Regex


class ParsingTree:
    """A list of tagged pieces with a hierarchical structure like a tree. It offers the entire structured data in JSON
    format and methods to add or get tagged pieces and other specific information."""

    def __init__(self):
        self._parsed_data = []

    def set_json_data(self, read_data: list):
        """Set the all JSON structured data as a list of tagged pieces. Usually when a saved JSON is read from a file.

        :param read_data: the JSON structured data as a list of tagged pieces.
        """
        self._parsed_data = read_data

    def get_json_data(self):
        """Get the entire JSON structure data as a list of tagged pieces."""

        return self._parsed_data

    def clear_parsed_data(self):
        """Empty the list of the tagged pieces."""

        self._parsed_data.clear()

    def append_tagged_piece(self, tagged_piece, tag_name: str = None):
        """Append a tagged piece to the current parsed data. This piece is a list with two elements, the 1st is the
        tagged value and the 2nd is the tag name. The value can be a string or a list of tagged piece IDs.

        :param tagged_piece: if the 2nd parameter is omitted it should be the list with two elements (the value and the
        tag name). If the 2nd parameter is present, this parameter should be only the tagged value.
        :param tag_name: the tag name of the tagged piece. Optional but if omitted it changes the structure of the 1st
        parameter.
        """
        if tag_name is None:
            tagged_piece[0] = self.strip_escape_char_from_beginning_and_end_of_piece(tagged_piece[0])
            tagged_piece[0] = self.strip_escape_char_from_special_chars(tagged_piece[0])
            self._parsed_data.append(tagged_piece)
        else:
            tagged_piece = self.strip_escape_char_from_beginning_and_end_of_piece(tagged_piece)
            tagged_piece = self.strip_escape_char_from_special_chars(tagged_piece)
            self._parsed_data.append([tagged_piece, tag_name])

    def insert_parsed_piece(self, piece_position: int, tagged_piece, tag_name: str = None):
        """Insert a tagged piece in a specific position. This piece is a list with two elements, the 1st is the tagged
        value and the 2nd is the tag name. The value can be a string or a list of tagged piece IDs.

        :param piece_position: the index of a piece after which insert the new piece.
        :param tagged_piece: if the 2nd parameter is omitted it should be the list with two elements (the value and the
        tag name). If the 2nd parameter is present, this parameter should be only the tagged value.
        :param tag_name: the tag name of the tagged piece. Optional but if omitted it changes the structure of the 1st
        parameter.
        """
        if tag_name is None:
            tagged_piece[0] = self.strip_escape_char_from_beginning_and_end_of_piece(tagged_piece[0])
            self._parsed_data.insert(piece_position, tagged_piece)
        else:
            tagged_piece = self.strip_escape_char_from_beginning_and_end_of_piece(tagged_piece)
            self._parsed_data.insert(piece_position, [tagged_piece, tag_name])

    def strip_escape_char_from_beginning_and_end_of_piece(self, piece: str):
        """Remove the escape char in the beginning and in the end of the piece.

        :param piece: the piece where to check the escape chars.
        :return: the piece edited.
        """
        if type(piece) is list:
            return piece

        if len(piece) > 0 and piece[0] == '\\':
            piece = piece[1:]

        if len(piece) > 0 and piece[-1] == '\\':
            piece = piece[:-1]

        piece = piece.replace('\\n\\', '\\n')
        piece = piece.replace('\\\\n', '\\n')

        return piece

    def strip_escape_char_from_special_chars(self, piece: str):
        """Remove the escape char from the beginning of the special chars.

        :param piece: the piece where to check the escape chars.
        :return: the piece edited.
        """
        if type(piece) is list:
            return piece

        piece = re.sub(r'\\(?=' + Regex.open_inline_tag + ')', '', piece)
        piece = re.sub(r'\\(?=' + Regex.hashtag_no_value + ')', '', piece)
        piece = re.sub(r'\\(?=' + Regex.hashtag_id + ')', '', piece)
        return piece

    def remove_first_piece_id_from_piece_value(self, piece_id: int):
        """Remove the first piece ID from the value of a specified piece.

        :param piece_id: ID of a piece of which you want to change the value.
        """
        self._parsed_data[piece_id][0].pop(0)

    def get_number_of_parsed_pieces(self):
        """Get the number of current parsed pieces. It corresponds to the index of the next new tagged piece."""

        return len(self._parsed_data)

    def get_value_of_tagged_piece(self, piece_id: int):
        """Get value of a tagged piece using its ID from the parsed data.

        :param piece_id: ID of the tagged piece.
        :return: value of the tagged piece.
        """
        return self._parsed_data[piece_id][0]

    def append_id_to_tagged_piece_value(self, parent_piece_id: int, child_piece_id: int):
        """Append an ID to a value of a tagged piece. The value must be a list of piece IDs.

        :param parent_piece_id: the ID of a parent piece that has child IDs on its value.
        :param child_piece_id: the ID of a piece that is a child of the parent piece.
        """
        self._parsed_data[parent_piece_id][0].append(child_piece_id)


parsing_tree = ParsingTree()
