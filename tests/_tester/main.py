"""The collection of the methods and the checks to test Tagged Text library"""

import os
import re


class Paths:

    _test_rel_folder = ''
    _test_file_list = []

    @classmethod
    def set_test_rel_folder(cls, folder):
        """Set the relative folder respect to 'test.py' file where the testing files are present."""

        cls._test_rel_folder = folder

    @classmethod
    def set_test_file_list(cls, file_list):
        """Set the testing file list inside the test folder to use for a specific test.
        The first file has to be always the spine file.
        """
        cls._test_file_list = file_list

    @classmethod
    def get_test_rel_folder(cls):
        return cls._test_rel_folder

    @classmethod
    def get_test_file_list(cls):
        return cls._test_file_list

    @classmethod
    def get_spine_rel_path(cls):
        return os.path.join(cls._test_rel_folder, cls._test_file_list[0])

    @classmethod
    def has_folder_name_parent_folder_symbol(cls, folder_name):
        folder_path = os.path.join('.', Paths._test_rel_folder, folder_name)
        if '../' in folder_path or '/../' in folder_path:
            return True
        return False


def print_first_line_of_spine():
    """In the testing collection the first line of the spine files
    is intended to be a description of the test.
    """
    with open(Paths.get_spine_rel_path(), 'r') as f:
        lines = f.readlines(512)
        f.close()
    print(lines[0].lstrip('#').lstrip())

def check_test_assets_existence(test_case):
    check_test_folder_existence(test_case)
    check_test_files_existence(test_case)

def check_test_folder_existence(test_case):
    case_folder = Paths.get_test_rel_folder()
    existing = os.path.isdir(case_folder)
    if not existing:
        test_case.fail(
            case_folder + ' not found. This test suite is not launched where it is expected or the folder name of the '
            'publication test is wrong.'
        )
    return True

def check_test_files_existence(test_case):
    case_folder = Paths.get_test_rel_folder()
    file_list = Paths.get_test_file_list()
    satisfied = True
    for file_name in file_list:
        if not os.path.isfile(os.path.join(case_folder, file_name)):
            print('The expected ' + file_name + ' file is missing in ' + case_folder + ' folder.')
            satisfied = False

    if not satisfied:
        test_case.fail('One or more expected files are missing in ' + case_folder + ' folder.')

    return True

def empty_json_and_pub_folders():
    empty_json_folder()
    empty_pub_folder()

def empty_json_folder():
    _empty_folder('json', ['json'])

def empty_pub_folder():
    _empty_folder('pub', ['txt', 'html', 'xhtml', 'htm'])

def _empty_folder(folder_name, file_format_list):
    """Delete all files inside a folder with the file format specified.

    :param folder_name Folder name to empty. The special folder /../ is forbidden for security reasons.
    :param file_format_list List with file format abbreviations without the dot.
    """
    aborted = False
    json_file_rel_folder = os.path.join('.', Paths.get_test_rel_folder(), folder_name)
    if Paths.has_folder_name_parent_folder_symbol(folder_name):
        print("The folder name '" + json_file_rel_folder + "' has forbidden parent folder symbol /../")
        aborted = True

    if type(file_format_list) is not list:
        print('The parameter file_format_list is not a list.')
        aborted = True

    for format in file_format_list:
        # If the format is not a string or the string is not from 2 to 5 chars,
        # the operation is aborted.
        if type(format) is not str or len(format) < 2 or len(format) > 5:
            aborted = True

    if aborted:
        exit('Operations aborted for security reasons.')

    if not os.path.isdir(json_file_rel_folder):
        return

    file_format_regex = ''
    if len(file_format_list) == 1:
        file_format_regex = file_format_list[0]
    elif len(file_format_list) > 1:
        file_format_regex = '(' + '|'.join(file_format_list) + ')'

    if file_format_regex:
        json_file_list = [f for f in os.listdir(json_file_rel_folder)
                          if re.match(r'.*\.' + file_format_regex + '$', f)]
        for file_name in json_file_list:
            file_path = os.path.join(json_file_rel_folder, file_name)
            os.remove(file_path)

def check_json_files_are_equal_to_expected_json_files(test_case):
    _check_filtered_files_in_a_folder_with_checking_files(
        test_case, ['json'], 'json', 'json-check'
    )

def check_pub_files_are_equal_to_expected_pub_files(test_case):
    _check_filtered_files_in_a_folder_with_checking_files(
        test_case, ['html'], 'pub', 'pub-check'
    )

def _check_filtered_files_in_a_folder_with_checking_files(
        test_case, file_format_list, file_folder,checking_file_folder
    ):
    """Check some generated files with other checking files in a prepared folder. The generated files have to be
    equal to checking files.

    :param test_case: instance of test case to allow the failure of current test.
    :param file_folder: the folder name with the generated files.
    :param checking_file_folder: the folder name with the checking files.
    :param file_format_list: List with file format abbreviations without the dot.
    """
    case_folder = Paths.get_test_rel_folder()
    file_rel_folder = os.path.join('.', case_folder, file_folder)

    file_format_regex = ''
    if len(file_format_list) == 1:
        file_format_regex = file_format_list[0]
    elif len(file_format_list) > 1:
        file_format_regex = '(' + '|'.join(file_format_list) + ')'

    if file_format_regex:
        file_list = [f for f in os.listdir(file_rel_folder)
                     if re.match(r'.*\.' + file_format_regex + '$', f)]
        for file_name in file_list:
            file_path = os.path.join(file_rel_folder, file_name)
            checking_file_path = file_path.replace('/' + file_folder + '/', '/' + checking_file_folder + '/')

            if not os.path.exists(checking_file_path):
                test_case.fail("The checking file " + checking_file_path + " does not exist.")

            lines = _read_text_file_as_line_list(file_path)
            checking_lines = _read_text_file_as_line_list(checking_file_path)
            if not len(lines) == len(checking_lines):
                test_case.fail("The file '" + file_name + "' has a different number of expected lines.")
            n = 0
            while n < len(lines):
                if not lines[n] == checking_lines[n]:
                    test_case.fail("The file '" + file_name + "' has the line n. " + str(n)
                                   + " different from what is expected.")
                n += 1

def _read_text_file_as_line_list(file_path):
    with open(file_path) as json_file_stream:
        line_list = json_file_stream.readlines()
        json_file_stream.close()
    return line_list
