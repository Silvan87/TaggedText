"""The Tagged Text Publisher to produce content viewable by the user"""

from tt.model.spine import spine
from tt.model.publications import Publications


class Publisher:
    """An interface to produce a view where the user can see the contents assembled through the templates."""

    @classmethod
    def write_publication(cls):
        """Write the publication according to the defined files.

        The text editors or the browser will be the actual interface for the user.
        """
        spine.paths.make_directory(spine.paths.get_publication_files_abs_folder())
        for pub_file_name in Publications.get_all():
            publication = Publications.get(pub_file_name)
            f = open(publication.get_path(), 'w', encoding='utf-8')
            f.write(publication.get_text())
            f.close()
        spine.print_writing_operation_info()
