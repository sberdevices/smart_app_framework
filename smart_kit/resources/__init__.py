import json

import core.basic_models.operators.comparators as cmp
import core.basic_models.operators.operators as op
import core.basic_models.requirement.device_requirements as dr
import scenarios.scenario_models.field.composite_fillers as cffd
import scenarios.scenario_models.field.field_filler_description as ffd
import scenarios.scenario_models.field_requirements.field_requirements as frd
from core.basic_models.actions.basic_actions import actions, action_factory, Action, \
    DoingNothingAction, RequirementAction, ChoiceAction, ElseAction, CompositeAction
from core.basic_models.actions.client_profile_actions import GiveMeMemoryAction, RememberThisAction
from core.basic_models.actions.counter_actions import CounterIncrementAction, CounterDecrementAction, \
    CounterClearAction, CounterSetAction, CounterCopyAction
from core.basic_models.actions.external_actions import ExternalAction
from core.basic_models.actions.external_actions import ExternalActions
from core.basic_models.actions.push_action import PushAction, PUSH_NOTIFY
from core.basic_models.actions.string_actions import StringAction, AfinaAnswerAction, SDKAnswer, \
    SDKAnswerToUser
from core.basic_models.answer_items.answer_items import items_factory, SdkAnswerItem, answer_items, BubbleText, \
    ItemCard, PronounceText, SuggestText, SuggestDeepLink, RawItem
from core.basic_models.classifiers.basic_classifiers import classifiers, classifier_factory, Classifier, \
    ExternalClassifier, SciKitClassifier, SkipClassifier
from core.basic_models.classifiers.external_classifiers import ExternalClassifiers
from core.basic_models.requirement.basic_requirements import requirement_factory, IntersectionRequirement
from core.basic_models.requirement.basic_requirements import requirements, Requirement, AndRequirement, \
    OrRequirement, NotRequirement, TemplateRequirement, RandomRequirement, TimeRequirement, DateTimeRequirement, \
    ClassifierRequirement, FormFieldValueRequirement, EnvironmentRequirement, CharacterIdRequirement, \
    FeatureToggleRequirement
from core.basic_models.requirement.counter_requirements import CounterValueRequirement, CounterUpdateTimeRequirement
from core.basic_models.requirement.device_requirements import ChannelRequirement
from core.basic_models.requirement.external_requirements import ExternalRequirement
from core.basic_models.requirement.external_requirements import ExternalRequirements
from core.basic_models.requirement.project_requirements import SettingsRequirement
from core.basic_models.requirement.user_text_requirements import AnySubstringInLoweredTextRequirement, \
    IntersectionWithTokensSetRequirement, NormalizedTextInSetRequirement, \
    PhoneNumberNumberRequirement, NumInRangeRequirement
from core.basic_models.scenarios.base_scenario import BaseScenario
from core.basic_models.scenarios.base_scenario import scenarios
from core.configs.base_config import BaseConfig
from core.db_adapter.aioredis_adapter import AIORedisAdapter
from core.db_adapter.db_adapter import db_adapters
from core.db_adapter.ignite_adapter import IgniteAdapter
from core.db_adapter.memory_adapter import MemoryAdapter
from core.descriptions.descriptions import registered_description_factories
from core.model.queued_objects.limited_queued_hashable_objects_description import \
    LimitedQueuedHashableObjectsDescriptionsItems
from core.model.registered import registered_factories
from core.repositories.classifier_repository import ClassifierRepository
from core.repositories.file_repository import FileRepository
from core.repositories.folder_repository import FolderRepository
from core.request.base_request import requests_registered
from core.request.rest_request import RestRequest
from core.utils.loader import ordered_json
from scenarios.actions.action import (
    BreakScenarioAction, ChoiceScenarioAction, ClearCurrentScenarioAction,
    ClearCurrentScenarioFormAction, ClearFormAction, ClearInnerFormAction, ClearScenarioByIdAction,
    ClearVariablesAction, CompositeFillFieldAction, DeleteVariableAction, FillFieldAction,
    RemoveCompositeFormFieldAction, RemoveFormFieldAction, SaveBehaviorAction, SetVariableAction,
    ResetCurrentNodeAction, RunScenarioAction, RunLastScenarioAction, AddHistoryEventAction, SetLocalVariableAction,
    ClearAllScenariosAction
)
from scenarios.actions.action import ProcessBehaviorAction, SelfServiceActionWithState, EmptyAction
from scenarios.behaviors.behavior_descriptions import BehaviorDescriptions
from scenarios.requirements.requirements import AskAgainExistRequirement, TemplateInArrayRequirement, \
    ArrayItemInTemplateRequirement, RegexpInTemplateRequirement
from scenarios.scenario_descriptions.form_filling_scenario import FormFillingScenario
from scenarios.scenario_descriptions.scenarios_description import ScenariosDescriptions
from scenarios.scenario_descriptions.tree_scenario.tree_scenario import TreeScenario
from scenarios.scenario_models.field.composite_field import CompositeField
from scenarios.scenario_models.field.external_field_filler_descriptions import ExternalFieldFillerDescriptions
from scenarios.scenario_models.field.field import field_models, field_model_factory, BasicField, IntegrationField, \
    QuestionField
from scenarios.scenario_models.field.field_descriptions.basic_field_description import field_descriptions, \
    field_description_factory, BasicFieldDescription
from scenarios.scenario_models.field.field_descriptions.composite_field_description import CompositeFieldDescription
from scenarios.scenario_models.field.field_descriptions.integration_field_description import IntegrationFieldDescription
from scenarios.scenario_models.field.field_descriptions.question_field_description import QuestionFieldDescription
from scenarios.scenario_models.forms.composite_forms import CompositeForm
from scenarios.scenario_models.forms.form import BaseForm, form_models, form_model_factory, Form
from scenarios.scenario_models.forms.form_description import form_descriptions, form_description_factory, \
    BaseFormDescription, FormDescription, CompositeFormDescription
from scenarios.scenario_models.forms.forms_description import FormsDescription
from scenarios.scenario_models.history import HistoryDescription, \
    EventFormatter, formatters, formatters_factory, HistoryEventFormatter
from scenarios.scenario_models.scenario_models import scenario_models, scenario_model_factory, BaseScenarioModel, \
    TreeScenarioModel, FormFillingScenarioModel
from scenarios.user.last_scenarios.last_scenarios_descriptions import LastScenariosDescriptionsItems
from scenarios.user.preprocessing_messages.preprocessing_messages_description import \
    PreprocessingMessagesDescription
from smart_kit.action.http import HTTPRequestAction
from smart_kit.message.get_to_message import to_messages
from smart_kit.message.smart_app_push_message import SmartAppPushToMessage
from smart_kit.request.kafka_request import SmartKitKafkaRequest

from core.db_adapter.aioredis_sentinel_adapter import AIORedisSentinelAdapter


class SmartAppResources(BaseConfig):
    def __init__(self, source, references_path, settings):
        super(SmartAppResources, self).__init__(source=source)
        self.references_path = references_path
        self.repositories = [
            FolderRepository(self.subfolder_path("forms"), loader=ordered_json, source=source,
                             key="forms"),
            FolderRepository(self.subfolder_path("scenarios"), loader=ordered_json, source=source,
                             key="scenarios"),
            FileRepository(self.subfolder_path("preprocessing_messages_for_scenarios_settings.json"),
                           loader=ordered_json,
                           source=source, key="preprocessing_messages_for_scenarios"),
            FileRepository(self.subfolder_path("last_scenarios_descriptions.json"), loader=ordered_json,
                           source=source, key="last_scenarios"),
            FileRepository(self.subfolder_path("history.json"), loader=ordered_json, source=source,
                           key="history"),
            FolderRepository(self.subfolder_path("behaviors"), loader=ordered_json, source=source,
                             key="behaviors"),
            FolderRepository(self.subfolder_path("actions"), loader=ordered_json, source=source,
                             key="external_actions"),
            FolderRepository(self.subfolder_path("requirements"), loader=ordered_json, source=source,
                             key="external_requirements"),
            FolderRepository(self.subfolder_path("field_fillers"), loader=ordered_json, source=source,
                             key="external_field_fillers"),
            FileRepository(self.subfolder_path("responses.json"), loader=ordered_json, source=source,
                           key="responses"),
            FileRepository(self.subfolder_path("last_action_ids.json"), loader=ordered_json,
                           source=source, key="last_action_ids"),
            FolderRepository(self.subfolder_path("bundles"), loader=ordered_json, source=source,
                             key="bundles"),
            ClassifierRepository(
                description_path=self.subfolder_path("classifiers"),
                data_path=self.subfolder_path("classifiers_data"),
                loader=json.loads,
                source=source,
                key="external_classifiers"
            )
        ]

        self.repositories = self.override_repositories(self.repositories)
        self.init()

    @property
    def _subfolder(self):
        return self.references_path

    def override_repositories(self, repositories: list):
        """
        Метод предназначен для переопределения репозиториев в дочерних классах.
        :param repositories: Список репозиториев родителя
        :return: Переопределённый в наследниках список репозиториев
        """
        return repositories

    def init(self):
        super(SmartAppResources, self).init()
        self.init_factories()
        self.init_field_filler_description()
        self.init_scenarios()
        self.init_field_requirements()
        self.init_repo_factories()
        self.init_scenario_models()
        self.init_form_descriptions()
        self.init_form_model()
        self.init_field_descriptions()
        self.init_field_model()
        self.init_actions()
        self.init_requirements()
        self.init_operators()
        self.init_comparators()
        self.init_sdk_items()
        self.init_history_formatters()
        self.init_db_adapters()
        self.init_classifiers()
        self.init_message_handlers()

    def init_field_requirements(self):
        frd.field_requirements[None] = frd.FieldRequirement
        frd.field_requirements["and"] = frd.AndFieldRequirement
        frd.field_requirements["comparison"] = frd.ComparisonFieldRequirement
        frd.field_requirements["field_text_length"] = frd.TextLengthFieldRequirement
        frd.field_requirements["is_int"] = frd.IsIntFieldRequirement
        frd.field_requirements["not"] = frd.NotFieldRequirement
        frd.field_requirements["or"] = frd.OrFieldRequirement
        frd.field_requirements["token_part_in_set"] = frd.TokenPartInSet
        frd.field_requirements["value_in_set"] = frd.ValueInSetRequirement

    def init_field_filler_description(self):
        ffd.field_filler_description[None] = ffd.FieldFillerDescription
        ffd.field_filler_description["all_regexps"] = ffd.AllRegexpsFieldFiller
        ffd.field_filler_description["approve"] = ffd.ApproveFiller
        ffd.field_filler_description["approve_strictly"] = ffd.ApproveRawTextFiller
        ffd.field_filler_description["available_info_filler"] = ffd.AvailableInfoFiller
        ffd.field_filler_description["choice"] = cffd.ChoiceFiller
        ffd.field_filler_description["classifier"] = ffd.ClassifierFiller
        ffd.field_filler_description["classifier_meta"] = ffd.ClassifierFillerMeta
        ffd.field_filler_description["composite"] = ffd.CompositeFiller
        ffd.field_filler_description["currency_first"] = ffd.FirstCurrencyFiller
        ffd.field_filler_description["else"] = cffd.ElseFiller
        ffd.field_filler_description["external"] = ffd.ExternalFieldFillerDescription
        ffd.field_filler_description["geo"] = ffd.FirstGeoFiller
        ffd.field_filler_description["get_first_person"] = ffd.FirstPersonFiller
        ffd.field_filler_description["intersection"] = ffd.IntersectionFieldFiller
        ffd.field_filler_description["intersection_original_text"] = ffd.IntersectionOriginalTextFiller
        ffd.field_filler_description["number_first"] = ffd.FirstNumberFiller
        ffd.field_filler_description["organisation"] = ffd.FirstOrgFiller
        ffd.field_filler_description["previous_messages_filler"] = ffd.PreviousMessagesFiller
        ffd.field_filler_description["regexp"] = ffd.RegexpFieldFiller
        ffd.field_filler_description["regexp_string_operations"] = ffd.RegexpAndStringOperationsFieldFiller
        ffd.field_filler_description["requirement"] = cffd.RequirementFiller
        ffd.field_filler_description["user_id"] = ffd.UserIdFiller
        ffd.field_filler_description["date_period_filler"] = ffd.DatePeriodFiller

    def init_scenarios(self):
        scenarios[None] = BaseScenario
        scenarios["base"] = BaseScenario
        scenarios["form_filling"] = FormFillingScenario
        scenarios["tree"] = TreeScenario

    def init_form_descriptions(self):
        form_descriptions[None] = FormDescription
        form_descriptions["base"] = FormDescription
        form_descriptions["composite"] = CompositeFormDescription

    def init_form_model(self):
        form_models[FormDescription] = Form
        form_models[CompositeFormDescription] = CompositeForm

    def init_field_descriptions(self):
        field_descriptions[None] = QuestionFieldDescription
        field_descriptions["question"] = QuestionFieldDescription
        field_descriptions["composite"] = CompositeFieldDescription
        field_descriptions["integration"] = IntegrationFieldDescription

    def init_field_model(self):
        field_models[BasicFieldDescription] = BasicField
        field_models[CompositeFieldDescription] = CompositeField
        field_models[QuestionFieldDescription] = QuestionField
        field_models[IntegrationFieldDescription] = IntegrationField

    def init_scenario_models(self):
        scenario_models[FormFillingScenario] = FormFillingScenarioModel
        scenario_models[TreeScenario] = TreeScenarioModel

    def init_factories(self):
        registered_factories[Action] = action_factory
        registered_factories[ffd.FieldFillerDescription] = ffd.field_filler_factory
        registered_factories[frd.FieldRequirement] = frd.field_requirement_factory
        registered_factories[BaseScenarioModel] = scenario_model_factory
        registered_factories[BaseFormDescription] = form_description_factory
        registered_factories[BaseForm] = form_model_factory
        registered_factories[BasicFieldDescription] = field_description_factory
        registered_factories[BasicField] = field_model_factory
        registered_factories[op.Operator] = op.operator_factory
        registered_factories[cmp.Comparator] = cmp.comparator_factory
        registered_factories[Requirement] = requirement_factory
        registered_factories[SdkAnswerItem] = items_factory
        registered_factories[EventFormatter] = formatters_factory
        registered_factories[Classifier] = classifier_factory

    def init_repo_factories(self):
        registered_description_factories["forms"] = FormsDescription
        registered_description_factories["scenarios"] = ScenariosDescriptions
        registered_description_factories["preprocessing_messages_for_scenarios"] = PreprocessingMessagesDescription
        registered_description_factories["last_scenarios"] = LastScenariosDescriptionsItems
        registered_description_factories["external_actions"] = ExternalActions
        registered_description_factories["behaviors"] = BehaviorDescriptions
        registered_description_factories["history"] = HistoryDescription
        registered_description_factories["external_requirements"] = ExternalRequirements
        registered_description_factories["external_field_fillers"] = ExternalFieldFillerDescriptions
        registered_description_factories["last_action_ids"] = LimitedQueuedHashableObjectsDescriptionsItems
        registered_description_factories["external_classifiers"] = ExternalClassifiers

    def init_actions(self):
        actions[None] = EmptyAction
        actions["add_history_event"] = AddHistoryEventAction
        actions["break_scenario"] = BreakScenarioAction
        actions["choice"] = ChoiceAction
        actions["choice_scenario"] = ChoiceScenarioAction
        actions["clear_current_scenario"] = ClearCurrentScenarioAction
        actions["clear_all_scenarios"] = ClearAllScenariosAction
        actions["clear_current_scenario_form"] = ClearCurrentScenarioFormAction
        actions["clear_form_by_id"] = ClearFormAction
        actions["clear_inner_form_by_id"] = ClearInnerFormAction
        actions["clear_scenario_by_id"] = ClearScenarioByIdAction
        actions["clear_variables"] = ClearVariablesAction
        actions["composite"] = CompositeAction
        actions["composite_fill_field"] = CompositeFillFieldAction
        actions["counter_clear"] = CounterClearAction
        actions["counter_copy"] = CounterCopyAction
        actions["counter_decrement"] = CounterDecrementAction
        actions["counter_increment"] = CounterIncrementAction
        actions["counter_set"] = CounterSetAction
        actions["delete_variable"] = DeleteVariableAction
        actions["do_nothing"] = DoingNothingAction
        actions["else"] = ElseAction
        actions["external"] = ExternalAction
        actions["fill_field"] = FillFieldAction
        actions["http_request"] = HTTPRequestAction
        actions["process_behavior"] = ProcessBehaviorAction
        actions["random_field_answer"] = AfinaAnswerAction
        actions["remove_composite_form_field"] = RemoveCompositeFormFieldAction
        actions["remove_form_field"] = RemoveFormFieldAction
        actions["requirement"] = RequirementAction
        actions["reset_current_node"] = ResetCurrentNodeAction
        actions["run_last_scenario"] = RunLastScenarioAction
        actions["run_scenario"] = RunScenarioAction
        actions["save_behavior"] = SaveBehaviorAction
        actions["sdk_answer"] = SDKAnswer
        actions["sdk_answer_to_user"] = SDKAnswerToUser
        actions["self_service_with_state"] = SelfServiceActionWithState
        actions["set_local_variable"] = SetLocalVariableAction
        actions["set_variable"] = SetVariableAction
        actions["string"] = StringAction
        actions["push"] = PushAction
        actions["give_me_memory"] = GiveMeMemoryAction
        actions["remember_this"] = RememberThisAction

    def init_requirements(self):
        requirements[None] = Requirement
        requirements["and"] = AndRequirement
        requirements["any_substring_in_lowered_text"] = AnySubstringInLoweredTextRequirement
        requirements["app_type"] = dr.AppTypeRequirement
        requirements["array_item_in_template"] = ArrayItemInTemplateRequirement
        requirements["ask_again_exist"] = AskAgainExistRequirement
        requirements["capabilities_property_available"] = dr.CapabilitiesPropertyAvailableRequirement
        requirements["channel"] = ChannelRequirement
        requirements["character_id"] = CharacterIdRequirement
        requirements["classifier"] = ClassifierRequirement
        requirements["counter_time"] = CounterUpdateTimeRequirement
        requirements["counter_value"] = CounterValueRequirement
        requirements["datetime"] = DateTimeRequirement
        requirements["environment"] = EnvironmentRequirement
        requirements["external"] = ExternalRequirement
        requirements["feature_toggle_check"] = FeatureToggleRequirement
        requirements["form_field_value"] = FormFieldValueRequirement
        requirements["intersection"] = IntersectionRequirement
        requirements["intersection_with_tokens"] = IntersectionWithTokensSetRequirement
        requirements["normalized_text_in_set"] = NormalizedTextInSetRequirement
        requirements["not"] = NotRequirement
        requirements["num_in_range"] = NumInRangeRequirement
        requirements["or"] = OrRequirement
        requirements["phone_number_number"] = PhoneNumberNumberRequirement
        requirements["platform_type"] = dr.PlatformTypeRequirement
        requirements["platform_version"] = dr.PlatformVersionRequirement
        requirements["random"] = RandomRequirement
        requirements["regexp_in_template"] = RegexpInTemplateRequirement
        requirements["surface"] = dr.SurfaceRequirement
        requirements["surface_version"] = dr.SurfaceVersionRequirement
        requirements["template"] = TemplateRequirement
        requirements["template_in_array"] = TemplateInArrayRequirement
        requirements["time"] = TimeRequirement
        requirements["settings"] = SettingsRequirement

    def init_sdk_items(self):
        answer_items["bubble_text"] = BubbleText
        answer_items["item_card"] = ItemCard
        answer_items["pronounce_text"] = PronounceText
        answer_items["raw"] = RawItem
        answer_items["suggest_deeplink"] = SuggestDeepLink
        answer_items["suggest_text"] = SuggestText

    def init_operators(self):
        op.operators["any"] = op.AnyOperator
        op.operators["composite"] = op.CompositeOperator
        op.operators["endswith"] = op.EndsWithOperator
        op.operators["equal"] = op.EqualOperator
        op.operators["exists"] = op.Exists
        op.operators["in"] = op.InOperator
        op.operators["less"] = op.LessOperator
        op.operators["less_or_equal"] = op.LessOrEqualOperator
        op.operators["more"] = op.MoreOperator
        op.operators["more_or_equal"] = op.MoreOrEqualOperator
        op.operators["not_equal"] = op.NotEqualOperator
        op.operators["startswith"] = op.StartsWithOperator

    def init_comparators(self):
        cmp.comparators["equal"] = cmp.EqualComparator
        cmp.comparators["less"] = cmp.LessComparator
        cmp.comparators["less_or_equal"] = cmp.LessOrEqualComparator
        cmp.comparators["more"] = cmp.MoreComparator
        cmp.comparators["more_or_equal"] = cmp.MoreOrEqualComparator
        cmp.comparators["not_equal"] = cmp.NotEqualComparator

    def init_history_formatters(self):
        formatters[None] = HistoryEventFormatter
        formatters["history_formatter_20"] = HistoryEventFormatter

    def init_requests(self):
        requests_registered[None] = SmartKitKafkaRequest
        requests_registered["kafka"] = SmartKitKafkaRequest
        requests_registered["rest"] = RestRequest

    def init_db_adapters(self):
        db_adapters[None] = MemoryAdapter
        db_adapters["ignite"] = IgniteAdapter
        db_adapters["memory"] = MemoryAdapter
        db_adapters["aioredis"] = AIORedisAdapter
        db_adapters["aioredis_sentinel"] = AIORedisSentinelAdapter

    def init_classifiers(self):
        classifiers[None] = Classifier
        classifiers["external"] = ExternalClassifier
        classifiers["scikit"] = SciKitClassifier
        classifiers["skip"] = SkipClassifier

    def init_message_handlers(self):
        to_messages[PUSH_NOTIFY] = SmartAppPushToMessage
