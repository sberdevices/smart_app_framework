# coding: utf-8
import collections
import json
import re
from lazy import lazy
from jinja2 import exceptions as jexcept
from typing import Dict, List, Union, Optional, Any, Callable, Pattern, Set
from itertools import islice

import core.logging.logger_constants as core_log_const
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.basic_models.actions.basic_actions import Action
from core.model.factory import build_factory
from core.model.factory import list_factory
from core.model.registered import Registered
from core.utils.pickle_copy import pickle_deepcopy
from core.unified_template.unified_template import UnifiedTemplate
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from core.model.factory import factory
from core.logging.logger_utils import log
from core.utils.exception_handlers import exc_handler

import scenarios.logging.logger_constants as log_const
from scenarios.user.user_model import User

field_filler_description = Registered()

field_filler_factory = build_factory(field_filler_description)


class FieldFillerDescription(Action):

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super().__init__(items, id)

    def _log_params(self):
        return {
            log_const.KEY_NAME: log_const.FILLER_EXTRACT_VALUE,
            "filler": self.__class__.__name__
        }

    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> None:
        return None

    def on_extract_error(self, text_preprocessing_result, user, params=None):
        log("exc_handler: Filler failed to extract. Return None. MESSAGE: {}.".format(user.message.masked_value), user,
            {log_const.KEY_NAME: core_log_const.HANDLED_EXCEPTION_VALUE}, level="ERROR", exc_info=True)
        return None

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Any]] = None) -> None:
        return self.extract(text_preprocessing_result, user, params)

    def _postprocessing(self, user: User, item: str) -> None:
        last_scenario_name = user.last_scenarios.last_scenario_name
        user.scenario_models[last_scenario_name].postprocessing_data.append(item)


class ExternalFieldFillerDescription(FieldFillerDescription):
    filler: Optional[str]

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(ExternalFieldFillerDescription, self).__init__(items, id)
        self.filler = items.get("filler")

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult,
                user: User, params: Dict[str, Any] = None) -> Optional[Union[int, float, str, bool, List, Dict]]:
        filler = user.descriptions["external_field_fillers"][self.filler]
        return filler.run(user, text_preprocessing_result, params)


class CompositeFiller(FieldFillerDescription):
    fillers: Optional[List[FieldFillerDescription]]

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(CompositeFiller, self).__init__(items, id)
        self._fillers: Optional[List[Dict[str, Any]]] = items.get("fillers") or []

    @lazy
    @list_factory(FieldFillerDescription)
    def fillers(self):
        return self._fillers

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult,
                user: User, params: Dict[str, Any] = None) -> Optional[Union[int, float, str, bool, List, Dict]]:
        extracted = None
        for filler in self.fillers:
            extracted = filler.extract(text_preprocessing_result, user, params)
            if extracted is not None:
                break
        return extracted


class AvailableInfoFiller(FieldFillerDescription):
    loader: Optional[str]
    value: Union[str, Dict]
    loaders = collections.defaultdict(str, {"json": json.loads, "float": float, "int": int})

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(AvailableInfoFiller, self).__init__(items, id)
        value = items['value']
        self.loader = items.get('loader')
        self.template: UnifiedTemplate = UnifiedTemplate(value)

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult,
                user: User, params: Dict[str, Any] = None) -> Optional[Union[int, float, str, bool, List, Dict]]:
        params = params or {}
        collected = user.parametrizer.collect(text_preprocessing_result)
        params.update(collected)
        try:
            # if path is wrong, it may fail with UndefinedError
            # notion: {key: None} will return "None";
            # not existing key or value "" will return ""; otherwise question in scenario will go in cycles
            value = self.template.silent_render(params)
        except jexcept.UndefinedError:
            value = None

        if self.loader:
            if value:
                loader = self.loaders[self.loader]
                value = loader(value)
            else:
                value = None

        return value


class FirstNumberFiller(FieldFillerDescription):
    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[int]:
        numbers = text_preprocessing_result.num_token_values
        if numbers:
            log_params = self._log_params()
            log_params["numbers"] = str(numbers)
            message = "Filler: %(filler)s, Numbers: %(numbers)s"
            log(message, user, log_params)
        return numbers[0] if numbers else None


class FirstCurrencyFiller(FieldFillerDescription):

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        currencies = text_preprocessing_result.ccy_token_values
        if currencies:
            log_params = self._log_params()
            log_params["currencies"] = str(currencies)
            message = "Filler: %(filler)s, Currencies: %(currencies)s"
            log(message, user, log_params)
        return currencies[0] if currencies else None


class FirstOrgFiller(FieldFillerDescription):

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        orgs = text_preprocessing_result.org_token_values
        if orgs:
            log_params = self._log_params()
            log_params["orgs"] = str(orgs)
            message = "Filler: %(filler)s, Organisations: %(orgs)s"
            log(message, user, log_params)
        return orgs[0] if orgs else None


class FirstGeoFiller(FieldFillerDescription):

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        geos = text_preprocessing_result.geo_token_values
        if geos:
            log_params = self._log_params()
            log_params["geos"] = str(geos)
            message = "Filler: %(filler)s, Toponyms: %(geos)s"
            log(message, user, log_params)
        return geos[0] if geos else None


class RegexpFieldFiller(FieldFillerDescription):
    regexp: str
    delimiter: Optional[str]

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(RegexpFieldFiller, self).__init__(items, id)
        self.regexp = items["exp"]
        self.delimiter = items.get("delimiter", ",")

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        original_text = text_preprocessing_result.original_text
        match = re.findall(self.regexp, original_text)
        if match:
            log_params = self._log_params()
            log_params["match"] = str(match)
            message = "Filler: %(filler)s, Data: %(match)s"
            log(message, user, log_params)
            return self.delimiter.join(match)


class RegexpAndStringOperationsFieldFiller(RegexpFieldFiller):
    regexp: str
    delimiter: Optional[str]
    operations: List[Dict]

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(RegexpAndStringOperationsFieldFiller, self).__init__(items, id)
        self.operations = items["operations"]
        self.functions_mapping: Dict[str, Callable] = {
            "strip": str.strip,
            "rstrip": str.rstrip,
            "lstrip": str.lstrip,
            "upper": str.upper,
            "lower": str.lower
        }

    def _operation(self, original_text, typeOp, amount):
        func = self.functions_mapping[typeOp]
        return func(original_text, amount) if amount else func(original_text)

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        original_text = text_preprocessing_result.original_text
        if self.operations:
            for op in self.operations:
                original_text = self._operation(original_text, op["type"], op.get("amount"))
        text_preprocessing_result_copy = pickle_deepcopy(text_preprocessing_result)
        text_preprocessing_result_copy.original_text = original_text
        return super(RegexpAndStringOperationsFieldFiller, self).extract(text_preprocessing_result_copy, user, params)


class AllRegexpsFieldFiller(FieldFillerDescription):
    exps: Optional[List[str]]
    delimiter: Optional[str]
    original_text_lower: Optional[bool]

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(AllRegexpsFieldFiller, self).__init__(items, id)
        self.exps = items.get("exps") or []
        self.regexps: List[Pattern] = [re.compile(r) for r in self.exps]
        self.delimiter = items.get("delimiter") or ","
        self.original_text_lower = items.get("original_text_lower") or False

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        original_text = text_preprocessing_result.original_text
        if self.original_text_lower:
            original_text = original_text.lower()
        matches = []
        for r in self.regexps:
            matches.extend(r.findall(original_text))
        if matches:
            result = self.delimiter.join(matches)
            log_params = self._log_params()
            log_params["regexp_result"] = str(result)
            message = "Filler: %(filler)s, Data: %(regexp_result)s"
            log(message, user, log_params)
            return result


class FirstPersonFiller(FieldFillerDescription):

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        persons = text_preprocessing_result.person_token_values
        if persons:
            log_params = self._log_params()
            log_params["persons"] = str(persons)
            message = "Filler: %(filler)s, Persons: %(persons)s"
            log(message, user, log_params)
        return persons[0] if persons else None


class PreviousMessagesFiller(FieldFillerDescription):
    filler: Optional[FieldFillerDescription]
    count: Optional[int]

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(PreviousMessagesFiller, self).__init__(items, id)
        self._filler: Optional[Dict[str, Any]] = items.get("filler")
        self.count = items.get("count")

    @lazy
    @factory(FieldFillerDescription)
    def filler(self):
        return self._filler

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        result = self.filler.extract(text_preprocessing_result, user, params)
        if result is None:
            result = self._try_extract_last_messages(user, params)
        return result

    def _try_extract_last_messages(self, user, params):
        processed_items = user.preprocessing_messages_for_scenarios.processed_items
        count = self.count - 1 if self.count else len(processed_items)
        for preprocessing_result_raw in islice(processed_items, 0, count):
            preprocessing_result = TextPreprocessingResult(preprocessing_result_raw)
            result = self.filler.extract(preprocessing_result, user, params)
            if result is not None:
                return result


class UserIdFiller(FieldFillerDescription):

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        result = user.message.uuid.get('userId')
        return result


class IntersectionFieldFiller(FieldFillerDescription):
    cases: Optional[Dict[str, List[str]]]

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(IntersectionFieldFiller, self).__init__(items, id)
        self.cases = items.get("cases") or {}
        self.default = items.get("default")
        from smart_kit.configs import get_app_config
        app_config = get_app_config()

        self.normalized_cases = []
        for key, val in self.cases.items():
            tokens_list = []
            for message in app_config.NORMALIZER.normalize_sequence(val):
                case = set()
                for norm in message["tokenized_elements_list"]:
                    if norm.get("token_type") != "SENTENCE_ENDPOINT_TOKEN":
                        case.add(norm.get("lemma"))
                tokens_list.append(case)
            self.normalized_cases.append((key, tokens_list))

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: TextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        tpr_tokenized_set = {norm.get("lemma") for norm in text_preprocessing_result.tokenized_elements_list if
                             norm.get("token_type") != "SENTENCE_ENDPOINT_TOKEN"}
        for key, tokens_list in self.normalized_cases:
            for tokens in tokens_list:
                if tpr_tokenized_set >= tokens:
                    log_params = self._log_params()
                    log_params["words_tokenized_set"] = str(tpr_tokenized_set)
                    log_params["tokens"] = str(tokens)
                    message = "Filler: %(filler)s, words_normalized_set: %(words_tokenized_set)s, tokens: %(tokens)s"
                    log(message, user, log_params)
                    return key
        if self.default:
            return self.default


class IntersectionOriginalTextFiller(FieldFillerDescription):

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(IntersectionOriginalTextFiller, self).__init__(items, id)
        self.cases = items.get("cases", {})
        self.original_cases = [(key, [{*phrase.split()} for phrase in val]) for key, val in self.cases.items()]

        self._exceptions = items.get("exceptions", {})
        self.exceptions = {key: [{*phrase.split()} for phrase in val] for key, val in self._exceptions.items()}

    def _check_exceptions(self, key, tpr_original_set):
        if key in self.exceptions.keys():
            for exc_tokens in self.exceptions[key]:
                if tpr_original_set >= exc_tokens:
                    return True
        return False

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: TextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[str]:
        tpr_original_set = {*text_preprocessing_result.original_text.split()}
        for key, tokens_list in self.original_cases:
            for tokens in tokens_list:
                if tpr_original_set >= tokens and not self._check_exceptions(key, tpr_original_set):
                    log_params = self._log_params()
                    log_params["tpr_original_set"] = str(tpr_original_set)
                    log_params["tokens"] = str(tokens)
                    message = "Filler: %(filler)s, tpr_original_set: %(tpr_original_set)s, tokens: %(tokens)s"
                    log(message, user, log_params)
                    return key


class ApproveFiller(FieldFillerDescription):
    yes_words: Optional[List]
    no_words: Optional[List]

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(ApproveFiller, self).__init__(items, id)

        from smart_kit.configs import get_app_config
        app_config = get_app_config()

        self.yes_words = items.get("yes_words")
        self.no_words = items.get("no_words")
        self.set_yes_words: Set = set(self.yes_words or [])
        self.set_no_words: Set = set(self.no_words or [])
        self.yes_words_normalized: Set = {
            TextPreprocessingResult(result).tokenized_string for result in
            app_config.NORMALIZER.normalize_sequence(self.set_yes_words)
        }
        self.no_words_normalized: Set = {
            TextPreprocessingResult(result).tokenized_string for result in
            app_config.NORMALIZER.normalize_sequence(self.set_no_words)
        }

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: TextPreprocessingResult, user: User,
                params: Dict[str, Any] = None) -> Optional[bool]:
        if text_preprocessing_result.tokenized_string in self.yes_words_normalized:
            params = self._log_params()
            params["tokenized_string"] = text_preprocessing_result.tokenized_string
            params["yes_words"] = self.yes_words_normalized
            message = "Filler: %(filler)s, normalized_text: %(tokenized_string)s, self.yes_words: %(yes_words)s"
            log(message, user, params)
            response = True
        elif text_preprocessing_result.words_tokenized_set.intersection(self.no_words_normalized):
            params = self._log_params()
            params["tokenized_string"] = text_preprocessing_result.words_tokenized_set
            params["no_words"] = self.no_words_normalized
            message = "Filler: %(filler)s, normalized_text: %(tokenized_string)s, self.no_words: %(no_words)s"
            log(message, user, params)
            response = False
        else:
            response = None
        return response


class ApproveRawTextFiller(ApproveFiller):
    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(
            self, text_preprocessing_result: TextPreprocessingResult, user: User, params: Dict[str, Any] = None
    ) -> Optional[bool]:
        original_text = ' '.join(text_preprocessing_result.original_text.split()).lower().rstrip('!.)')
        if original_text in self.set_yes_words:
            params = self._log_params()
            params["original_text"] = original_text
            params["yes_words"] = self.set_yes_words
            message = "Filler: %(filler)s, original_text: %(original_text)s, self.yes_words: %(yes_words)s"
            log(message, user, params)
            response = True
        elif text_preprocessing_result.words_tokenized_set.intersection(self.no_words_normalized):
            params = self._log_params()
            params["words_tokenized_set"] = text_preprocessing_result.words_tokenized_set
            params["no_words"] = self.set_no_words
            message = "Filler: %(filler)s, words_normalized_set: %(words_tokenized_set)s, self.no_words: %(no_words)s"
            log(message, user, params)
            response = False
        else:
            response = None
        return response
