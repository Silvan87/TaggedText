"""This is the model closest to the contents of the view, before to write files into a memory storage"""

class Publications:
    """The publication is written in the RAM before being saved to a memory storage.
    Thus, it is safe to cancel the process or add any post-process to the final text."""

    _publications = {}  # key: pub file name; value: publication object
    _current_pub_index = 0
    _last_used_file_name = ''

    class _Publication:

        def __init__(self, path):
            """Create a new publication file. It has the path where to write the file and the content organized in a
            special tree. This tree is a list of branches. A branch can be a string or a list of branches. During the
            development of the tree, the position where to put a new set of branches is called node.

            :param path: the path of the publication file.
            """
            self._path = path
            self._developing_tree = []  # Empty list of branches
            self._current_node_position = []  # A series of indexes to reach the current node
            self._next_node_position = []  # A series of indexes to reach the next node from which to restart

        def _get_current_node(self):
            """Get the list of the branches of the current selected node."""

            if len(self._current_node_position) == 0:
                return self._developing_tree
            else:
                sub_node = self._developing_tree
                for intermediate_position in self._current_node_position:
                    sub_node = sub_node[intermediate_position]
                return sub_node

        def get_path(self):
            """Get the path of the publication file."""

            return self._path

        def get_text(self, branch_list: list = None):
            """Get the final text of the publication file."""

            text = ''

            if branch_list is None:
                branch_list = self._developing_tree

            for branch in branch_list:
                if type(branch) is str:
                    text += branch
                elif type(branch) is list:
                    text += self.get_text(branch)

            return text

        def add_branch(self, text: str):
            """Add a new branch in the current selected node.

            :param text: the elaborated text produced for this branch.
            """
            self._get_current_node().append(text)

        def add_node(self):
            """Add a new node after the current branch inside the current node.
            Also track the position of the new added node."""

            current_node = self._get_current_node()
            current_branch_number = len(current_node)
            current_node.append([])
            self._next_node_position.append(current_branch_number)

        def make_next_node_the_current_node(self):
            """Select the next node as the new current node."""

            self._current_node_position = self._next_node_position


    @classmethod
    def initialize(cls, file_name: str, path: str):
        """Create in the memory a publication called with the file name. It has the path where to write the file and a
        special tree to develop the elaborated content. It is created with a new empty list of branches in the tree.

        :param file_name: the name of the file is the name of the publication.
        :param path: the path where to write the publication file.
        """
        cls._publications[file_name] = cls._Publication(path)
        cls._last_used_file_name = file_name

    @classmethod
    def set_current_pub_index(cls, index: int):
        """Save the passed index to track the current publication through different contexts.

        :param index: the index of the current publication.
        """
        cls._current_pub_index = index

    @classmethod
    def get_current_pub_index(cls):
        """Get the index of the current worked publication previously saved."""

        return cls._current_pub_index

    @classmethod
    def get_all(cls):
        """Get the dictionary of all generated publications."""

        return cls._publications

    @classmethod
    def get(cls, file_name: str):
        """Get a publication file by its name.

        :param file_name: the name of the publication file to get.
        :return: the publication called.
        """
        return cls._publications[file_name]

    @classmethod
    def add_branch(cls, text: str):
        """Add a new branch in the current selected node of the current publication.

        :param text: the elaborated text produced for this branch.
        """
        cls._publications[cls._last_used_file_name].add_branch(text)

    @classmethod
    def add_node(cls):
        """Add a new node after the current branch inside the current node of the current publication."""

        cls._publications[cls._last_used_file_name].add_node()

    @classmethod
    def make_next_node_the_current_node(cls):
        """Select the next node as the new current node of the current publication."""

        cls._publications[cls._last_used_file_name].make_next_node_the_current_node()
