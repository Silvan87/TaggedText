"""The collection of all flow exceptions and process errors."""

import tt.controller.main as main


class ReaderError:

    class TtNameUsedAsTemplateNameError(Exception):
        """A template file name is equal to a tagged text file name: this is forbidden."""

        def __init__(self, template_name):
            self._template_name = template_name

        def stop_process_with_error_message(self):
            main.end_to_write_publication_with_spine(
                f"A tagged text name is equal to this template name: {self._template_name}.\n"
                "File homonyms are forbidden. Please give your tt files unique names."
            )

    class PublicationFileWithoutContentFile(Exception):
        """A 'publish' instruction has to have as many pub files as content files."""

        def stop_process_with_error_message(self):
            main.end_to_write_publication_with_spine(
                f"In a 'publish' instruction of the spine the number of publication files are different from the number"
                " of the content files. If you have more than one publication file, the numbers have to be the same or "
                "a publication file will remain without content."
            )


class ParserError:

    class TaggedTextLineSyntaxError(SyntaxError):
        """A generic syntax error in a line of a tt file."""

        def __init__(self, file_name, line_number):
            self._file_name = file_name
            self._line_number = line_number

    class SkippedDeeperTagLevelError(TaggedTextLineSyntaxError):
        """The error about skipping an intermediate level going deeper in a tag level."""

        def __init__(self, file_name, line_number, current_tag_level, previous_tag_level):
            super().__init__(file_name, line_number)

            self._current_tag_level = current_tag_level
            self._previous_tag_level = previous_tag_level

        def stop_parsing_with_error_message(self):
            main.end_to_write_publication_with_spine(
                f"Parsing error for {self._file_name} file.\nText line n. {self._line_number} specifies tag level "
                f"n. {self._current_tag_level} but the previous tag level was only n. {self._previous_tag_level}\n"
                "The deeper levels have to be specified gradually."
            )


class CompositorError:

    class MissingContextIndexWithContentDataError(SyntaxError):
        """A context for a text piece has the piece index without the content data."""

        def __init__(self):
            pass

        def stop_parsing_with_error_message(self):
            main.end_to_write_publication_with_spine("A content index was indicated but without the content data")

    class MissingExpectedTagError(SyntaxError):
        """An expected tag is missing respect to a defined tag or to a rule."""

        def __init__(self, current_tag, expected_subtag):
            self._current_tag = current_tag
            self._expected_subtag = expected_subtag

        def stop_parsing_with_error_message(self):
            main.end_to_write_publication_with_spine(
                f"The tag '{self._current_tag}' has not the expected subtag '{self._expected_subtag}'."
            )

    class RepeatedContentSubtagError(SyntaxError):
        """The subtag Content has been repeated, and it is not allowed."""

        def __init__(self):
            pass

        def stop_parsing_with_error_message(self):
            main.end_to_write_publication_with_spine(
                "The tag 'content' is present more than once, but it must be unique."
            )

    class NotSupportedTagRuleError(SyntaxError):
        """A tag rule in the template is not supported."""

        def __init__(self, template_file_name, rule_tag):
            self._template_file_name = template_file_name
            self._rule_tag = rule_tag

        def stop_parsing_with_error_message(self):
            main.end_to_write_publication_with_spine(
                f"The template file '{self._template_file_name}' has a not supported rule tag: '{self._rule_tag}'."
            )


class FlowException:
    """It moves the flow from the ordinary routine to a different one."""

    class ReadJsonStillUpToDateException(Exception):
        """A read json file is up-to-date, so it doesn't need to be generated again."""

        pass
