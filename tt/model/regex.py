"""Regex tool specific for Tagged Text modules"""

import re


class Regex:
    """Define tags and comment syntax by regular expressions and other utilities."""

    hashtag = '(#|#{2,} ?)[A-Za-z0-9-]+'
    hashtag_no_value = '#[A-Za-z0-9-]+#'
    hashtag_id = '\|[A-Za-z0-9-]+'
    open_inline_tag = '/\*[A-Za-z0-9-]+\*/'
    closed_inline_tag = '\*/'
    comment = '^#\s.*$'
    comment_delimiter = '^#+$'
    not_normal_text = '(' + hashtag + '|' + comment + '|' + comment_delimiter + ')'

    @classmethod
    def whitespace_split(cls, string_values: str):
        """Splits a string using white characters as separators.

        :param string_values: a string containing values separated by white characters.
        :return: the list of values to get from the passed string.
        """
        return re.split('[\n\t ]+', string_values)
