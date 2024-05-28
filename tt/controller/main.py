"""It offers the entry and the exit points to the Tagged Text module.

The main entry point is write_publication_with_spine(tt_spine_rel_path)
You can use a tagged text spine file to indicate tagged text content files
that use tagged text template files to produce any kind of textual results.
"""

from tt.controller.parser import Parser
from tt.controller.compositor import Compositor
from tt.controller.publisher import Publisher


def write_publication_with_spine(tt_spine_rel_path: str):
    """Parse the tagged text spine file and all its tt dependencies, then write the publication.

    :param tt_spine_rel_path: the relative path of tt spine file respect to make.py
    """
    Parser.parse_spine_and_all_required_files(tt_spine_rel_path)
    Compositor.apply_templates()
    Publisher.write_publication()


def end_to_write_publication_with_spine(message: str=None):
    """The exit point if the method write_publication_with_spine ends.
    It's useful to execute expected final routines. Currently only a message to print is managed.

    :param message: a message that informs the user about the reason of process termination.
    """
    if message:
        print(message)
