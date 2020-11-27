from core.basic_models.requirement.basic_requirements import requirements
from core.basic_models.actions.basic_actions import actions
from core.db_adapter.db_adapter import db_adapters

import scenarios.scenario_models.field.field_filler_description as ffd

from smart_kit.configs import SmartAppResources
from app.adapters.db_adapters import CustomDBAdapter
from app.basic_entities.actions import CustomAction
from app.basic_entities.fillers import CustomFieldFiller
from app.basic_entities.requirements import CustomRequirement


class CustomAppResourses(SmartAppResources):

        def __init__(self, source, references_path, settings):
            super(CustomAppResourses, self).__init__(source, references_path, settings)

        def override_repositories(self, repositories: list):
            """
            Метод предназначен для переопределения репозиториев в дочерних классах.
            :param repositories: Список репозиториев родителя
            :return: Переопределённый в наследниках список репозиториев
            """
            return repositories

        def init_field_filler_description(self):
            super(CustomAppResourses, self).init_field_filler_description()
            ffd.field_filler_description["simple_filler"] = CustomFieldFiller

        def init_actions(self):
            super(CustomAppResourses, self).init_actions()
            actions["custom_action"] = CustomAction

        def init_requirements(self):
            super(CustomAppResourses, self).init_requirements()
            requirements["sample_requirement"] = CustomRequirement

        def init_db_adapters(self):
            super(CustomAppResourses, self).init_db_adapters()
            db_adapters["custom_db_adapter"] = CustomDBAdapter

