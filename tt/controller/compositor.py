"""The Compositor of tagged texts that applies template rules to the tagged content."""

import os
from enum import Enum
from tt.controller.exceptions import *
from tt.model.regex import Regex
from tt.model.spine import spine
from tt.model.taggedtexts import Type as TtType
from tt.model.taggedtexts import TaggedTexts
from tt.model.templates import Templates
from tt.model.parsingtree import parsing_tree
from tt.model.publications import *


class TemplateRule:
    """A rule of the template."""

    def __init__(self, tag_rule_index: int, template_name: str):
        """Instantiate a new template rule specifying the template source, the index and preparing other information.

        :param tag_rule_index: the index of the template rule inside the template.
        :param template_name: the template name where the rule is present.
        """
        self._tag_rule_index = tag_rule_index
        self._template_name = template_name
        self._rule = Templates.get_rules(template_name)[tag_rule_index]

    def __getitem__(self, index):
        """Get the sub pieces or the tag of the list of 2 elements of TemplateRule.

        :param index: the index of the element of the list that essentially defines the TemplateRule.
        :return: an element of the list with 2 items of the TemplateRule.
        """
        if index == 0:
            return self.get_sub_pieces()

        elif index == 1:
            return self.get_tag()

    def set_tag_rule(self, index: int, template_name: str):
        """Set the tag rule rewriting index and template name during the initialization.

        :param index: the index of the template rule inside the template.
        :param template_name: the template name where the rule is present.
        """
        self.__init__(index, template_name)

    def get_tag_rule_index(self):
        """Get the index of a rule applied to a tag."""

        return self._tag_rule_index

    def get_tag(self):
        """Get the tag from the rule."""

        return self._rule[1]

    def get_sub_pieces(self):
        """Get the text pieces where the rule is applied."""

        return self._rule[0]

    def get_rule(self):
        """Get the rule as it is in the json structure."""

        return self._rule

    def get_template_name(self):
        """Get the template name where the rule is present."""

        return self._template_name

    def get_template_data(self):
        """Get the template data where the rule is present."""

        return Templates.get_rules(self._template_name)


class ContentPiece:
    """A parsed text piece with content and context."""

    def __init__(self, content_data: list, content_index: int, template_names: list, found_rule: TemplateRule = None):
        """Constructor of a content piece with its context.

        :param content_data: the tagged text in json format where to find the data for the content.
        :param content_index: the index of the content piece inside the content data.
        :param template_names: the list of template names where to search the rule.
        :param found_rule: the TemplateRule with all the information for the rule.
        """
        self._content_data = content_data
        self._piece_index = content_index
        self._piece = content_data[content_index]
        self._template_names = template_names
        self._found_rule = found_rule  # TODO is it really useful to pass the already found rule?
        self._found_list_rule = None
        self._involved_tag_number = 1

        tag = ''
        if content_data:
            tag = self._piece[1]

        # Since a tag can have a tag rule with a tag list rule at the same time,
        # it needs to search in every template and put together these types of rules.
        # Moreover, the subsequent template rules overwrite the previous template rules.
        template_name_index = len(template_names) - 1
        while template_name_index > -1:
            rule_template_name = template_names[template_name_index]

            if tag in Templates.get_triggers(rule_template_name):
                rule_index = Templates.get_rule_index(rule_template_name, tag)
                self._found_rule = TemplateRule(rule_index, rule_template_name)

            if '_list_' + tag in Templates.get_triggers(rule_template_name):
                rule_index = Templates.get_rule_index(rule_template_name, '_list_' + tag)
                self._found_list_rule = TemplateRule(rule_index, rule_template_name)

            template_name_index -= 1

    def get_index(self):
        """Get the index of the parsed text piece."""

        return self._piece_index

    def get_tag(self):
        """Get the tag applied to the parsed text piece."""

        return self._piece[1]

    def get_piece(self):
        """Get the parsed text piece defined by a 2-items list: the content and the tag."""

        return self._piece

    def get_sub_pieces(self):
        """Get the content or the sub pieces defined with a list of indexes of a parsed text piece."""

        return self._piece[0]

    def get_content_data(self):
        """Get all the content data where the parsed text piece is present."""

        return self._content_data

    def get_raw_value(self, starting_piece_value: str = None):
        """Get the raw value of a parsed text piece using its sub pieces without applying any rule.

        :param starting_piece_value: an existing piece of value to prepend to the final raw value.
        :return: the string value related to the content piece avoiding applying rules.
        """
        if starting_piece_value is None:
            starting_piece_value = self._piece[0]

        value = ''
        if type(starting_piece_value) is list:
            for sub_piece_id in starting_piece_value:
                sub_piece_value = self._content_data[sub_piece_id][0]

                if type(sub_piece_value) is list:
                    value += self.get_raw_value(sub_piece_value)
                else:
                    value += sub_piece_value
        else:
            value += starting_piece_value

        return value

    def get_template_name_list(self):
        """Get the template list where it is possible to find the rule for the parsed text piece."""

        return self._template_names

    def get_found_rule(self):
        """Get the found rule for the parsed text piece."""

        return self._found_rule

    def get_found_list_rule(self):
        """Get the found list rule for the parsed text piece."""

        return self._found_list_rule

    def get_involved_tag_number(self):
        """Get the number of involved tag for the parsed text piece considering its sub pieces."""

        return self._involved_tag_number

    def get_depth_level(self, piece_index: int = -1):
        """Get the level of the piece (tagged or not) in its content."""

        current_previous_index = 0
        if piece_index == -1:
            index_to_check = self._piece_index
        else:
            index_to_check = piece_index

        level = 1
        new_level = True

        while new_level:
            new_level = False

            for piece in self._content_data:
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

    def apply_rule_and_arrange_value(self):
        """Apply the found rule of the parsed text piece producing the text result with the Compositor."""

        index_jump = 0
        if self._found_list_rule:
            index_jump = Compositor.arrange_tag_list_value(self)

        elif self._found_rule:
            rule_tag = self._found_rule.get_tag()

            if rule_tag == 'tag':
                Compositor.arrange_value(self)

            elif rule_tag == 'catching-tag':
                Compositor.arrange_catching_tag_value(self._template_names, self.get_found_rule().get_rule())
            else:
                raise CompositorError.NotSupportedTagRuleError(self._found_rule.get_template_name(), rule_tag)

        return index_jump


class Compositor:
    """Get values based on the rules defined in the tt templates and using tt contents.

    It should be prepared by setting the content reference and the template reference. It allows to look for each tag
    and if a tag triggers a template rule, it applies every rule.
    """

    _json_content_name_list = []
    _current_template_name_list = []
    _current_template_name = ''
    _current_rule_index = 0
    _current_rule = None
    _current_pub_file_name = ''

    @classmethod
    def set_content_reference(cls, content_name_list: list):
        """Set the content reference to be used to produce the final text result.

        :param content_name_list: the list of the content processed files.
        """
        cls._json_content_name_list = content_name_list

    @classmethod
    def set_template_reference(cls, template_name_list: list):
        """Set the template reference to be used to produce the final text result.

        :param template_name_list: the list of the template processed files.
        """
        cls._json_template_name_list = template_name_list

    @classmethod
    def set_current_template_name(cls, template_name: str):
        """Set the current used template among the list of template reference.

        :param template_name: the template name currently used.
        """
        cls._current_template_name = template_name

    @classmethod
    def get_involved_item_number_in_an_item(cls, item_index: int):
        """Get the number of the involved items in an item identified by its index.

        :param item_index: the index of the item to analyze.
        """
        content_data = TaggedTexts.get(cls._json_content_name_list)
        final_index = item_index
        item = content_data[item_index]

        while type(item[0]) is list:
            final_index = item[0][-1]
            item = content_data[final_index]

        return final_index - item_index + 1

    @classmethod
    def look_for_rule_in_templates(cls, tag: str, tag_list_first: bool = False):
        """Look for rules applied to a tag considering the template reference.

        :param tag: the tag of which searching if a rule is applied to it.
        :param tag_list_first: if a tag list rule is present, with True it is checked first.
        :return: the found rule or None if nothing is found.
        """
        cls._current_rule = None
        tags_to_search = []

        if tag_list_first:
            tags_to_search.append('_list_' + tag)
        tags_to_search.append(tag)

        for tag in tags_to_search:
            template_name_index = len(cls._current_template_name_list) - 1

            while template_name_index > -1:
                if tag in Templates.get_triggers(cls._current_template_name_list[template_name_index]):
                    cls._current_template_name = cls._current_template_name_list[template_name_index]
                    cls._current_rule_index = Templates.get_rule_index(cls._current_template_name, tag)
                    cls._current_rule = TemplateRule(cls._current_rule_index, cls._current_template_name)
                template_name_index -= 1

            if cls._current_rule:
                break

        return cls._current_rule

    @classmethod
    def is_last_tag_found_in_rules(cls):
        """Get a boolean to know if the last check for a tag has found a rule or not."""

        if len(cls._current_rule) == 0:
            return False
        else:
            return True

    @classmethod
    def get_last_found_rule(cls):
        """Get the last found rule by the Compositor for a tag."""

        return cls._current_rule

    @classmethod
    def get_current_content_data(cls):
        """Get the current content data related to the current rule."""

        if TaggedTexts.get_current_tt_type() == TtType.SPINE:
            content_data = parsing_tree.get_json_data()
        elif TaggedTexts.get_current_tt_type() == TtType.TEMPLATE:
            content_data = Templates.get_rules(cls._current_template_name)
        else:  # TtType.CONTENT
            content_data = TaggedTexts.get(cls._json_content_name_list)

        return content_data

    @classmethod
    def get_raw_first_value_of_item(cls, item: list | TemplateRule, content_data: list = None):
        """Get a simple string of the first child of this item. If it is composed by sub pieces they are ignored.
        An item can be a template rule.

        :param item: the item passed as a piece of the parsed text.
        :param content_data: all the content data of the parsed text.
        :return: the string value of that item.
        """

        if content_data is None:
            content_data = cls.get_current_content_data()
        value = content_data[item[0][0]][0]

        # If the first child is a list, there is no simple string value
        while type(value) is list:
            value = ''
        return value

    @classmethod
    def get_raw_first_value_of_item_thru_piece(
            cls, item: list, content_piece: ContentPiece, template_as_content: bool = False
        ):
        """Get a simple string from the first value of an item. If it is composed by pieces take the first value of the
        first piece that is not a list.

        :param item: the item passed as a piece of the parsed text.
        :param content_piece: the content piece with content and context.
        :param template_as_content: True if the content for the piece has to be its template.
        :return: the string value of that item.
        """
        if template_as_content:
            content_data = content_piece.get_found_rule().get_template_data()
        else:
            content_data = content_piece.get_content_data()
        value = content_data[item[0][0]][0]

        # If the value is described by a list, that is not expected.
        # So, take the first value in the list that is not a list.
        while type(value) is list:
            value = value[0]
        return value

    @classmethod
    def get_raw_subtag_value_of_tag(
            cls, item: list, subtag: str, default='', content_data: list = None, with_index: bool = False
        ):
        """Get a simple string from a subtag corresponding to a specified tag.

        :param item: the item where to search for the sub item.
        :param subtag: the tag requested for the sub item.
        :param default: a default string value if nothing is found.
        :param content_data: the content data where to search for the item and its sub items.
        :param with_index: True to get a tuple with the index of the sub item and its value.
        :return: the string value of a sub item tagged as requested. With with_index=True a tuple is returned as defined
        above.
        """
        if content_data is None:
            content_data = cls.get_current_content_data()

        for child_index in item[0]:
            child = content_data[child_index]
            if child[1] == subtag:
                if with_index:
                    return child_index, cls.get_raw_first_value_of_item(child, content_data)
                else:
                    return cls.get_raw_first_value_of_item(child, content_data)

        if default:
            return default
        else:
            return ''

    @classmethod
    def get_raw_next_tag_value(cls, content_data: list, start_index: int, next_tag: str, default: str = ''):
        """Get a simple string of next tag at the same level of this item.

        :param content_data: the content data where to search for the next item with the defined tag.
        :param start_index: the index of the item from which starting the search. If it is -1 it means the calling rule
        has no item as a level reference and the level has to be considered 1.
        :param next_tag: the requested tag for the next item of which to take the raw value.
        :param default: a default string value if nothing is found.
        :return: the string value of the next item with the requested tag.
        """
        initial_level = 1
        if start_index == -1:
            start_index = 0
        else:
            initial_level = TaggedTexts.get_depth_level(content_data, start_index) + 1

        content_index = start_index
        while content_index < len(content_data):
            item = content_data[content_index]
            current_level = TaggedTexts.get_depth_level(content_data, content_index)

            if current_level == initial_level and item[1] == next_tag:
                return cls.get_raw_first_value_of_item(item)

            content_index += 1

        return default

    @classmethod
    def arrange_first_value_of_item_thru_piece(cls, item: list, content_piece: ContentPiece):
        """Arrange the value of the first child of this item in the developing tree.

        :param item: the item where to take the first sub item.
        :param content_piece: the content piece of which the item is part of.
        """
        content_data = content_piece.get_content_data()
        value = content_data[item[0][0]][0]
        if type(value) is list:
            cls.look_for_rules_for_each_items(value, content_data)
        else:
            Publications.add_branch(value)

    @classmethod
    def arrange_first_value_of_item_thru_its_content(cls, item: list, content_data: list):
        """Arrange the value of the first child of this item in the developing tree.

        :param item: the item where to take the first sub item.
        :param content_data: the content data of which the item is part of.
        """
        value = content_data[item[0][0]][0]
        if type(value) is list:
            cls.look_for_rules_for_each_items(value, content_data)
        else:
            Publications.add_branch(value)

    @classmethod
    def arrange_value(cls, content_piece: ContentPiece):
        """Try to arrange the value on the content developing tree managing exceptions and errors.

        :param content_piece: the piece of content whose value to process and arrange in the publication.
        """
        try:
            cls.try_to_arrange_value(content_piece)

        except Exception as e:
            raise e

    @classmethod
    def try_to_arrange_value(cls, content_piece: ContentPiece):
        """Arrange the value on the content developing tree by applying a template rule to an indexed content.

        :param content_piece: the piece of content whose value to process and arrange in the publication.
        """

        content_occurrences = 0
        template_rule = content_piece.get_found_rule()

        if template_rule:
            template_data = template_rule.get_template_data()
        else:
            if content_piece.get_tag() == '':
                Publications.add_branch(content_piece.get_raw_value())
            return

        content_index = content_piece.get_index()
        content_data = content_piece.get_content_data()

        for rule_piece_index in template_rule.get_sub_pieces():
            rule_piece = template_data[rule_piece_index]

            if rule_piece[1] == 'text':
                cls.arrange_first_value_of_item_thru_its_content(rule_piece, template_data)

            elif rule_piece[1] == 'space':
                Publications.add_branch(' ')

            elif rule_piece[1] == 'new-line':
                Publications.add_branch('\n')

            elif rule_piece[1] == 'from-subtag':
                subtag_name = cls.get_raw_first_value_of_item(rule_piece, template_data)
                subtag_index, subtag_value = cls.get_raw_subtag_value_of_tag(
                    content_data[content_index], subtag_name,'', with_index=True
                )
                if type(subtag_value) is list:
                    cls.look_for_rules_for_each_items(subtag_value, content_data)
                else:
                    Publications.add_branch(subtag_value)

            elif rule_piece[1] == 'from-next-tag':
                start_index = 0
                next_tag_name = cls.get_raw_first_value_of_item_thru_piece(
                    rule_piece, content_piece, template_as_content=True
                )
                if content_piece.get_tag() in ['file-opening', 'file-ending']:
                    content_data = TaggedTexts.get(spine.get_content_head_of_current_pub_item())
                    start_index = -1
                else:
                    start_index = content_index
                next_tag_value = cls.get_raw_next_tag_value(content_data, start_index, next_tag_name)
                Publications.add_branch(next_tag_value)

            elif rule_piece[1] == 'from-var':
                value = spine.get_variable(cls.get_raw_first_value_of_item(rule_piece, template_data))
                Publications.add_branch(value)

            elif rule_piece[1] == 'from-counter':
                counter_name = cls.get_raw_first_value_of_item(rule_piece, template_data)
                value = str(spine.counters.get_value(counter_name))
                Publications.add_branch(value)
                spine.counters.take_a_step(counter_name)

            elif rule_piece[1] == 'from-file':
                file_name = cls.get_raw_first_value_of_item_thru_piece(
                    rule_piece, content_piece, template_as_content=True
                )
                template_rel_folder = spine.paths.get_template_files_rel_folder()
                file_path = os.path.join(spine.paths.make_file_abs_folder, template_rel_folder, file_name)
                f = open(file_path, 'r')
                value = ''.join(f.readlines())
                f.close()
                Publications.add_branch(value)

            elif rule_piece[1] == 'content':
                cls.look_for_rules_for_each_items(content_data[content_index][0], content_data)

                content_occurrences += 1
                if content_occurrences > 1:
                    raise CompositorError.RepeatedContentSubtagError

            else:
                if rule_piece[1] != "":
                    print("rule_piece[1] not managed:", rule_piece[1])

    @classmethod
    def arrange_tag_list_value(cls, content_piece: ContentPiece):
        """Try to arrange the value of a tag list rule on the content developing tree.

        :param content_piece: the piece of content whose value to process and arrange in the publication.
        """
        try:
            return cls.try_to_arrange_tag_list_value(content_piece)

        except Exception as e:
            raise e

    @classmethod
    def try_to_arrange_tag_list_value(cls, content_piece: ContentPiece):
        """Arrange the value of a tag list rule on the content developing tree.

        :param content_piece: the piece of content whose value to process and arrange in the publication.
        """
        # lists of couples: {key: type of text piece; value: value of text piece}
        # 1° list: the beginning of the list
        # 2° list: the end of the list
        # In the middle can be present only 1 content (the list of items)
        list_text = [[], []]
        item_separator = ''

        # list of item_text subrules, each list is a list of 3 lists of couples.
        # Lists of couple: {key: type of text piece; value: value of text piece}
        # 1° list: the beginning of the item
        # 2° list: the content and the things between contents of the item
        # 3° list: the end of the item
        items_text = []
        item_text_index = -1

        template_rule = content_piece.get_found_list_rule()
        template_data = template_rule.get_template_data()

        tag_list = Regex.whitespace_split(
            cls.get_raw_first_value_of_item(template_rule, template_data)
        )

        rule_piece_number = 0
        max_piece_number = len(template_rule.get_sub_pieces())
        while rule_piece_number < max_piece_number:
            rule_piece_index = template_rule.get_sub_pieces()[rule_piece_number]
            rule_piece = template_data[rule_piece_index]

            if rule_piece[1] == 'list':
                part = 0
                for sub_rule_index in rule_piece[0]:
                    sub_rule_piece = template_data[sub_rule_index]

                    if sub_rule_piece[1] == 'text':
                        list_text[part].append({
                            "type": "dynamic-text",
                            "value": [cls.look_for_rules_for_each_items, sub_rule_piece[0], template_data]
                        })
                    elif sub_rule_piece[1] == 'space':
                        list_text[part].append({
                            "type": "space",
                            "value": " "
                        })
                    elif sub_rule_piece[1] == 'new-line':
                        list_text[part].append({
                            "type": "new-line",
                            "value": "\n"
                        })
                    elif sub_rule_piece[1] == 'content':
                        if part > 0:
                            raise CompositorError.RepeatedContentSubtagError
                        part += 1

            elif rule_piece[1] == 'item-separator':
                for sub_rule_index in rule_piece[0]:
                    sub_rule_piece = template_data[sub_rule_index]

                    if sub_rule_piece[1] == 'text':
                        exit(  # TODO
                            "TODO occorre trovare il modo di gestire le sottoregole condivise da più tag con un metodo "
                            "generale"
                        )
                    elif sub_rule_piece[1] == 'space':
                        item_separator = " "

                    elif sub_rule_piece[1] == 'new-line':
                        item_separator = "\n"

                    elif sub_rule_piece[1] == '':
                        item_separator = sub_rule_piece[0]

            elif rule_piece[1] == 'item':
                item_text_index += 1
                items_text.append([[], [], []])
                item_part_index = 0
                item_last_content_index = -1

                for sub_rule_index in rule_piece[0]:
                    sub_rule_piece = template_data[sub_rule_index]

                    if item_part_index == 1 and item_last_content_index != -1:
                        if sub_rule_index > item_last_content_index:
                            item_part_index += 1

                    if sub_rule_piece[1] == 'text':
                        items_text[item_text_index][item_part_index].append({
                            "type": "dynamic-text",
                            "value": [cls.look_for_rules_for_each_items, sub_rule_piece[0], template_data]
                        })
                    elif sub_rule_piece[1] == 'space':
                        items_text[item_text_index][item_part_index].append({
                            "type": "space",
                            "value": " "
                        })
                    elif sub_rule_piece[1] == 'new-line':
                        items_text[item_text_index][item_part_index].append({
                            "type": "new-line",
                            "value": "\n"
                        })
                    elif sub_rule_piece[1] == 'content':
                        if item_part_index == 0:
                            item_part_index += 1

                        if item_last_content_index == -1:
                            # Until there is a content subtag to be processed, the item part has to be the middle part
                            # So it needs to find the last occurrence of content subtag.
                            exploring_index = len(rule_piece[0]) - 1
                            while exploring_index >= 0:
                                exploring_rule_piece_index = rule_piece[0][exploring_index]
                                if template_data[exploring_rule_piece_index][1] == 'content':
                                    item_last_content_index = exploring_rule_piece_index
                                    break
                                exploring_index -= 1

                        items_text[item_text_index][item_part_index].append({
                            "type": "content",
                            "value": ""
                        })
                    elif sub_rule_piece[1] == 'caught-tag-file-name':
                        items_text[item_text_index][item_part_index].append({
                            "type": "caught-tag-file-name",
                            "value": ""
                        })
                    else:
                        raise CompositorError.NotSupportedSubtagRuleError(
                            template_rule.get_template_name(), sub_rule_piece[1]
                        )
            rule_piece_number += 1

        content_data = content_piece.get_content_data()
        index = content_piece.get_index()

        # List opening
        for list_text_piece in list_text[0]:
            if list_text_piece['type'] == 'dynamic-text':
                list_text_piece['value'][0](*list_text_piece['value'][1:])
            else:
                Publications.add_branch(list_text_piece['value'])

        starting_index = index
        starting_level = content_piece.get_depth_level()
        item_text_index = -1

        # List body (items)
        while index < len(content_data):
            tagged_line = content_data[index]
            tag = tagged_line[1]
            current_level = content_piece.get_depth_level(index)

            if current_level <= starting_level and tag not in tag_list:
                index -= 1
                break

            elif current_level == starting_level and tag in tag_list:
                cls.look_for_rule_in_templates(tag, tag_list_first=False)
                rule = cls.get_last_found_rule()

                if not rule:
                    if type(tagged_line[0]) is list:

                        # List body (sub items)
                        for sub_item_index in tagged_line[0]:
                            content_piece = ContentPiece(
                                content_data, sub_item_index,
                                cls._current_template_name_list,
                                rule
                            )
                            if content_piece.get_found_rule():
                                if item_text_index + 1 < len(items_text):
                                    item_text_index += 1

                                if item_separator and index > starting_index and sub_item_index == tagged_line[0][0]:
                                    Publications.add_branch(item_separator)

                                # Initial part of an item of the list
                                if sub_item_index == tagged_line[0][0]:
                                    cls._add_text_pieces_to_publication(items_text[item_text_index][0])

                                for item_text_piece in items_text[item_text_index][1]:
                                    if item_text_piece['type'] == 'content':
                                        cls.arrange_value(content_piece)

                                    elif item_text_piece['type'] == 'dynamic-text':
                                        item_text_piece['value'][0](*item_text_piece['value'][1:])
                                    else:
                                        Publications.add_branch(item_text_piece['value'])

                                # Final part of an item of the list
                                if sub_item_index == tagged_line[0][-1]:
                                    cls._add_text_pieces_to_publication(items_text[item_text_index][2])

                    else:
                        index += 1
                        continue

                elif rule[1] == 'tag':
                    if item_text_index + 1 < len(items_text):
                        item_text_index += 1

                    content_piece = ContentPiece(
                        content_data, index,
                        cls._current_template_name_list
                    )
                    if item_separator and index > starting_index:
                        Publications.add_branch(item_separator)

                    # Initial part of an item of the list
                    cls._add_text_pieces_to_publication(items_text[item_text_index][0])

                    for item_text_piece in items_text[item_text_index][1]:
                        if item_text_piece['type'] == 'content':
                            cls.arrange_value(content_piece)

                        elif item_text_piece['type'] == 'dynamic-text':
                            item_text_piece['value'][0](*item_text_piece['value'][1:])
                        else:
                            Publications.add_branch(item_text_piece['value'])

                    # Final part of an item of the list
                    cls._add_text_pieces_to_publication(items_text[item_text_index][2])

                elif rule[1] == 'tag-list':
                    exit("A tag-list overlapped to a tag-list is not supported.")

                elif rule[1] == 'catching-tag':
                    exit("A catching-tag overlapped to a tag-list is not supported.")
                else:
                    exit("Not managed RULE TAG inside a tag-list:" + rule[1])

            involved_items = cls.get_involved_item_number_in_an_item(index)
            index += involved_items

        # List ending
        for list_text_piece in list_text[1]:
            if list_text_piece['type'] == 'dynamic-text':
                list_text_piece['value'][0](*list_text_piece['value'][1:])
            else:
                Publications.add_branch(list_text_piece['value'])

        return index - starting_index + 1

    @classmethod
    def _add_text_pieces_to_publication(cls, text_pieces):
        """Add to the publication the list of text pieces passed.

        :param text_pieces: a list of dictionary items with 2 keys 'type' and 'value'.
        """
        for item_text_piece in text_pieces:
            if item_text_piece['type'] == 'dynamic-text':
                item_text_piece['value'][0](*item_text_piece['value'][1:])
            else:
                Publications.add_branch(item_text_piece['value'])

    @classmethod
    def arrange_catching_tag_value(cls, template_data=None, template_rule=None):
        """Arrange the value of a catching tag on the content developing tree."""

        Publications.add_branch('<LISTA FROM CATCHING TAG>')
        return  # TODO BUG method to be refactored

        tags_to_catch = []
        list_text = ['', '']
        item_text = []  # list of couples: {key: type of text piece; value: value of text piece}

        if template_data is None:
            template_data = Templates.get_rules()

        elif type(template_data) is str:
            template_data = Templates.get_rules(template_data)

        elif type(template_data) is list:
            template_data = Templates.get_rules(template_data[0])

        if template_rule is None:
            template_rule = cls.get_last_found_rule()

        rule_piece_number = 0
        max_piece_number = len(template_rule[0]) - 1
        while rule_piece_number <= max_piece_number:
            rule_piece_index = template_rule[0][rule_piece_number]
            rule_piece = template_data[rule_piece_index]

            if rule_piece[1] == 'caught-tags':
                tags_to_catch = Regex.whitespace_split(cls.get_raw_first_value_of_item(rule_piece, template_data))

            elif rule_piece[1] == 'list':
                part = 0
                for sub_rule_index in rule_piece[0]:
                    sub_rule_piece = template_data[sub_rule_index]

                    # TODO BUG se la lista ha trovato un valore ma si sta costruendo per inserirlo a posteriori
                    # non è possibile che venga chiamato look_for_rules_for_each_items, dato che inserirà subito
                    # degli elementi e quindi si sfaserà tutto... Bisogna ripensare il modo in cui viene gestito TAG LIST
                    if sub_rule_piece[1] == 'text':
                        list_text[part] += str(cls.look_for_rules_for_each_items(sub_rule_piece[0], template_data))

                    elif sub_rule_piece[1] == 'space':
                        list_text[part] += ' '

                    elif sub_rule_piece[1] == 'new-line':
                        list_text[part] += '\n'

                    elif sub_rule_piece[1] == 'content':
                        part += 1

            elif rule_piece[1] == 'item':
                for sub_rule_index in rule_piece[0]:
                    sub_rule_piece = template_data[sub_rule_index]

                    if sub_rule_piece[1] == 'text':
                        item_text.append({
                            "type": "text",
                            "value": cls.look_for_rules_for_each_items(sub_rule_piece[0], template_data)
                        })
                    elif sub_rule_piece[1] == 'space':
                        item_text.append({
                            "type": "space",
                            "value": " "
                        })
                    elif sub_rule_piece[1] == 'new-line':
                        item_text.append({
                            "type": "new-line",
                            "value": "\n"
                        })
                    elif sub_rule_piece[1] == 'content':
                        item_text.append({
                            "type": "content",
                            "value": ""
                        })
                    elif sub_rule_piece[1] == 'caught-tag-file-name':
                        item_text.append({
                            "type": "caught-tag-file-name",
                            "value": ""
                        })
                    else:
                        main.end_to_write_publication_with_spine(
                            f"The subtag '{sub_rule_piece[1]}' under the tag 'item' is not managed.")

            rule_piece_number += 1

        value = list_text[0]
        content_data = TaggedTexts.get(cls._json_content_name_list)
        for index, item in enumerate(content_data):
            if item[1] in tags_to_catch:
                for sub_item in item_text:
                    if sub_item['type'] == 'content':
                        cls.look_for_rules_for_each_items(item[0], content_data)

                    elif sub_item['type'] == 'caught-tag-file-name':
                        current_tt_name = TaggedTexts.get_tt_name_related_to_an_item_in_joined_tts(
                            cls._json_content_name_list, index)
                        file_format = spine.get_file_format_of_pub_file(current_tt_name)
                        value += spine.paths.put_file_ext(current_tt_name, file_format)

                    else:
                        value += str(sub_item['value'])

        # return value + list_text[1]

    @classmethod
    def look_for_rules_for_each_items(cls, item_list, content_data: list = None):
        """Look for the rules for each content item and arrange the processed value on the developing tree.

        :param item_list: the list of items that compose the parsed tagged text.
        :param content_data: the content data to use to produce the final text.
        """
        if type(item_list) is str:
            Publications.add_branch(item_list)
            return

        item_number = 0
        while item_number < len(item_list):
            item_index = item_list[item_number]
            index_jump = 0
            item = content_data[item_index]
            tag = item[1]

            if tag == '':
                cls.look_for_rules_for_each_items(item[0], content_data)

            elif cls.look_for_rule_in_templates(tag, tag_list_first=True):
                rule = cls.get_last_found_rule()

                if rule[1] == 'tag':
                    content_piece = ContentPiece(
                        content_data, item_index,
                        cls._current_template_name_list,
                        cls.look_for_rule_in_templates(tag)
                    )
                    cls.arrange_value(content_piece)

                elif rule[1] == 'catching-tag':
                    text = 'catching-tag content'
                    Publications.add_branch(text)

                elif rule[1] == 'tag-list':
                    content_piece = ContentPiece(
                        content_data, item_index,
                        cls._current_template_name_list,
                        rule
                    )
                    index_jump = cls.arrange_tag_list_value(content_piece)
                else:
                    exit("Not managed RULE TAG inside a first-level tag:" + rule[1])

            if index_jump > 0:
                item_number += index_jump
            else:
                item_number += 1

    @classmethod
    def apply_templates(cls):
        """Apply all the templates through the tag triggers to each tt file in the spine."""

        TaggedTexts.set_current_tt_type(TtType.CONTENT)

        for file_info_index, file_info in enumerate(spine.get_pub_info_list()):
            spine.set_current_pub_item_index(file_info_index)
            head_input_file = file_info.get_content_head()
            cls._current_template_name_list = file_info.get_template_list()
            cls._current_pub_file_name = file_info.get_file_name_with_ext()
            Publications.initialize(cls._current_pub_file_name, file_info.get_file_abs_path())

            if cls.look_for_rule_in_templates('file-opening'):
                value = cls.get_raw_first_value_of_item(
                    cls._current_rule,
                    Templates.get_rules(cls._current_template_name)
                )
                if value != '':
                    Publications.add_branch(value)

                piece = ContentPiece(
                    Templates.get_rules(cls._current_template_name),
                    cls._current_rule_index,
                    cls._current_template_name_list,
                    TemplateRule(cls._current_rule_index, cls._current_template_name)
                )
                cls.arrange_value(piece)

            Publications.add_node()

            if cls.look_for_rule_in_templates('file-ending'):
                value = cls.get_raw_first_value_of_item(
                    cls._current_rule,
                    Templates.get_rules(cls._current_template_name)
                )
                if value != '':
                    Publications.add_branch(value)

                piece = ContentPiece(
                    Templates.get_rules(cls._current_template_name),
                    cls._current_rule_index,
                    cls._current_template_name_list,
                    TemplateRule(cls._current_rule_index, cls._current_template_name)
                )
                cls.arrange_value(piece)

            Publications.make_next_node_the_current_node()

            index = 0
            while index < TaggedTexts.get_item_number(head_input_file):
                tagged_line = TaggedTexts.get_tagged_line(head_input_file, index)
                tag = tagged_line[1]
                if tag == '':
                    piece = ContentPiece(
                        TaggedTexts.get(head_input_file), index, cls._current_template_name_list
                    )
                    cls.arrange_value(piece)
                    index += cls.get_involved_item_number_in_an_item(index)
                else:
                    piece = ContentPiece(
                        TaggedTexts.get(file_info.get_content_list()), index,
                        cls._current_template_name_list,
                        cls.look_for_rule_in_templates(tag)
                    )
                    index_jump = piece.apply_rule_and_arrange_value()

                    if index_jump > 0:
                        index += index_jump
                    else:
                        used_tag_count = piece.get_involved_tag_number()
                        while used_tag_count > 0:
                            used_tag_count -= 1
                            index += cls.get_involved_item_number_in_an_item(index)
