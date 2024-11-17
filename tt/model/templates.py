import os
from tt.model.spine import spine


class Templates:
    """The parsed templates. Each one named with the tt file name without extension and containing tag triggers and
    template rules."""

    _templates = {}

    class _Template:

        def __init__(self):
            """Initialize a template that consists in rules to apply and triggers to know which tags are associated to a
            rule."""

            self._triggers = {}
            self._rules = []

        def get_triggers(self):
            """Get the triggers of the template."""

            return self._triggers

        def get_rules(self):
            """Get the rules of the template."""

            return self._rules

        def set_triggers(self, triggers: dict):
            """Set all the triggers for the template removing the previous ones.

            :param triggers: the triggers previously calculated.
            """
            self._triggers = triggers

        def set_trigger(self, tag_name: str, rule_index: int):
            """Set a trigger to the template.

            :param tag_name: the tag name associated to a rule.
            :param rule_index: the index of the rule to apply.
            """
            self._triggers[tag_name] = rule_index
            # if tag_name.startswith('_list_'):
            #     if tag_name not in self._triggers:
            #         self._triggers[tag_name] = {}
            #         self._triggers[tag_name]['list'] = []
            #     else:
            #         tag_rule_index = self._triggers[tag_name]
            #         self._triggers[tag_name] = {}
            #         self._triggers[tag_name]['tag'] = tag_rule_index
            #         self._triggers[tag_name]['list'] = []
            #     self._triggers[tag_name]['list'].append(rule_index)
            # else:
            #     if tag_name in self._triggers and type(self._triggers[tag_name]) is dict:
            #         self._triggers[tag_name]['tag'] = rule_index
            #     else:
            #         self._triggers[tag_name] = rule_index  # ordinary case

        def set_rules(self, rules: list):
            """Set all the rules to the template removing the previous ones.

            :param rules: all the rules to set.
            """
            self._rules = rules

        def get_rule_index(self, tag_name: str):
            """Get the index of the rule associated to a specified tag name.

            :param tag_name: the tag name associated to the rule.
            :return: the rule index.
            """
            index = -1
            if tag_name in self._triggers.keys():
                index = self._triggers[tag_name]

            return index

    @classmethod
    def reset(cls):
        """Reset Templates removing all the existing templates."""

        cls._templates = {}

    @classmethod
    def initialize(cls, template_name: str):
        """Initialize a new or an existing template.

        :param template_name: tt template file name without extension.
        """
        cls._templates[template_name] = cls._Template()

    @classmethod
    def get(cls, template_name: str):
        """Get the requested template as a dictionary.

        :param template_name: tt template file name without extension, the key of the dictionary.
        :return: the template that is a dictionary with rules and tag triggers.
        """
        return cls._templates[template_name]

    @classmethod
    def get_triggers(cls, template_name: str):
        """Get the triggers as a dictionary to decide which rules apply according to the tags.

        :param template_name: tt template file name without extension, the key of the dictionary.
        :return: the triggers as a dictionary.
        """
        return cls._templates[template_name].get_triggers()

    @classmethod
    def get_tt_file_names(cls):
        """Get the list of the template names"""

        return cls._templates.keys()

    @classmethod
    def set_rules(cls, rule_list: list, template_name: str):
        """Set the rules to a template.

        :param rule_list: json data structure containing the list of the rules.
        :param template_name: tt template file name without extension, the key of the dictionary.
        """
        cls._templates[template_name].set_rules(rule_list)

    @classmethod
    def get_rules(cls, template_name: str):
        """Get the rules of a template.

        :param template_name: tt template file name without extension, the key of the dictionary.
        :return: json data structure containing the list of the rules.
        """
        return cls._templates[template_name].get_rules()

    @classmethod
    def get_rule_index(cls, template_name: str, tag_name: str):
        """Get the index of the rule associated to a specified tag name.

        :param template_name: tt template file name without extension, the key of the dictionary.
        :param tag_name: the tag name associated to a rule.
        :return: the rule index.
        """
        return cls._templates[template_name].get_rule_index(tag_name)

    @classmethod
    def get_template_name(cls, tag_name: str, template_names: list):
        """Get the template name of a rule with a specified tag name.

        :param tag_name: the tag name of the rule.
        :param template_names: the names of the templates where to search the rule.
        :return: the template name.
        """
        if len(template_names) == 1:
            return template_names[0]

        for template_name in template_names:
            rules = Templates.get_rules(template_name)
            for rule in rules:
                if rule[1] == tag_name:
                    return template_name

    @classmethod
    def set_trigger(cls, tag_name: str, rule_index: int, template_name: str):
        """Set a trigger that associates a tag name to a rule index

        :param template_name: tt template file name without extension, the key of the dictionary.
        :param tag_name: the tag name to encounter to apply a template rule.
        :param rule_index: the index of the rule to apply.
        """
        cls._templates[template_name].set_trigger(tag_name, rule_index)

    @classmethod
    def get_latest_modification_date_from_template_name_list(cls, template_name_list: list = None):
        """Get the latest modification date checking the intermediate json of a list of template names.

        :param template_name_list: the list of template names to check.
        :return: the latest modification date.
        """
        latest_modification_date = 0
        if template_name_list is None:
            template_name_list = cls.get_tt_file_names()

        for template_name in template_name_list:
            template_file_abs_path = spine.paths.get_json_file_abs_path(template_name)
            if not os.path.isfile(template_file_abs_path):
                return 0
            template_modification_date = os.path.getmtime(template_file_abs_path)
            if template_modification_date > latest_modification_date:
                latest_modification_date = template_modification_date

        return latest_modification_date
