import unittest
import tt
from tests._tester import *


class E2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('.', end='')

    def setUp(self):
        test_id = self._testMethodName[5:]
        print('\nTEST:', test_id)

        # given
        Paths.set_test_rel_folder('tests/' + test_id)
        Paths.set_test_file_list(['spine.tt', 'sample.tt', 'template/style.tt'])
        check_test_assets_existence(self)
        empty_json_and_pub_folders()
        print_first_line_of_spine()

    def _launch_standard_e2e_test(self):
        self._when_write_publication_with_spine()
        self._then_check_generated_json_and_pub_files()

    def _when_write_publication_with_spine(self):
        tt.write_publication_with_spine(Paths.get_spine_rel_path())

    def _then_check_generated_json_and_pub_files(self):
        check_json_files_are_equal_to_expected_json_files(self)
        check_pub_files_are_equal_to_expected_pub_files(self)

    def test_base_spine_empty_template(self):
        self._launch_standard_e2e_test()

    def test_base_spine_file_opening_ending(self):
        self._launch_standard_e2e_test()

    def test_articulated_file_opening_ending_text(self):
        self._launch_standard_e2e_test()

    def test_articulated_file_opening_ending_new_line_space(self):
        self._launch_standard_e2e_test()

    def test_articulated_file_opening_ending_from_next_tag(self):
        self._launch_standard_e2e_test()

    def test_articulated_file_opening_ending_from_var(self):
        self._launch_standard_e2e_test()

    def test_articulated_file_opening_ending_from_file(self):
        self._launch_standard_e2e_test()

    def test_not_tagged_text_with_inline_tagged_text_ignored(self):
        self._launch_standard_e2e_test()

    def test_not_tagged_text_and_tagged_text_with_inline_tag(self):
        self._launch_standard_e2e_test()

    def test_inline_tagged_text_without_value(self):
        self._launch_standard_e2e_test()

    def test_tt_object_no_rule_ignored(self):
        self._launch_standard_e2e_test()

    def test_tt_object_rule_new_line_space(self):
        self._launch_standard_e2e_test()

    def test_tt_object_rule_text_content_from_subtag(self):
        self._launch_standard_e2e_test()

    def test_tt_object_rule_from_next_tag_not_usable(self):
        self._launch_standard_e2e_test()

    def test_tt_object_rule_from_next_tag_usable(self):
        self._launch_standard_e2e_test()

    def test_tt_object_rule_from_var(self):
        self._launch_standard_e2e_test()

    def test_tt_object_rule_from_file(self):
        self._launch_standard_e2e_test()

#class Functional(unittest.TestCase):

#    def run(self, result=None):
#        TODO future development
#        super().run(result)

#    def test_0001(self):
        # given
        # when
        # then


if __name__ == '__main__':
    unittest.main()
