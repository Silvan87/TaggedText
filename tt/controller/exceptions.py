"""The collection of all flow exceptions and process errors."""

import tt.controller.main as main


class ReaderError:

    class TtNameUsedAsTemplateNameError(Exception):
        """A template file name is equal to a tagged text file name: this is forbidden."""

        def __init__(self, template_name):
            message = (
                f"A tagged text name is equal to this template name: {template_name}.\n"
                "File homonyms are forbidden. Please give your tt files unique names."
            )
            self.args += (message,)

    class PublicationFileWithoutContentFile(Exception):
        """A 'publish' instruction has to have as many pub files as content files."""

        def __init__(self, template_name):
            message = (
                "In a 'publish' instruction of the spine the number of publication files are different from the number "
                "of the content files. If you have more than one publication file, the numbers have to be the same or a"
                "publication file will remain without content."
            )
            self.args += (message,)


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

            message = (
                f"Parsing error for {self._file_name} file.\nText line n. {self._line_number} specifies tag level n. "
                f"{current_tag_level} but the previous tag level was only n. {previous_tag_level}\n"
                "The deeper levels have to be specified gradually."
            )
            self.args += (message,)


class CompositorError:

    class MissingContextIndexWithContentDataError(SyntaxError):
        """A context for a text piece has the piece index without the content data."""

        def __init__(self):
            self.args += ("A content index was indicated but without the content data.",)

    class MissingExpectedTagError(SyntaxError):
        """An expected tag is missing respect to a defined tag or to a rule."""

        def __init__(self, current_tag, expected_subtag):
            message = (
                f"The tag '{current_tag}' has not the expected subtag '{expected_subtag}'."
            )
            self.args += (message,)

    class RepeatedContentSubtagError(SyntaxError):
        """The subtag Content has been repeated, and it is not allowed."""

        def __init__(self):
            message = (
                f"The tag 'content' is present more than once, but it must be unique."
            )
            self.args += (message,)

    class NotSupportedTagRuleError(SyntaxError):
        """A tag rule in the template is not supported."""

        def __init__(self, template_file_name, rule_tag):
            message = (
                f"The template file '{template_file_name}' has a not supported rule tag: '{rule_tag}'."
            )
            self.args += (message,)

    class NotSupportedSubtagRuleError(SyntaxError):
        """A tag rule in the template is not supported."""

        def __init__(self, template_file_name, rule_subtag):
            message = (
                f"The template file '{template_file_name}' has a not supported rule subtag: '{rule_subtag}'."
            )
            self.args += (message,)


class FlowException:
    """It moves the flow from the ordinary routine to a different one."""

    class ReadJsonStillUpToDateException(Exception):
        """A read json file is up-to-date, so it doesn't need to be generated again."""

        pass
