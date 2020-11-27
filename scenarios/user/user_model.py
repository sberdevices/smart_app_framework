import json
from lazy import lazy


from core.logging.logger_utils import log
from core.model.field import Field
from core.model.base_user import BaseUser

from scenarios.scenario_models.scenario_models import ScenarioModels
from scenarios.scenario_models.forms.forms import Forms
from scenarios.user.last_fields.last_fields import LastFields
from scenarios.user.last_scenarios.last_scenarios import LastScenarios
from scenarios.user.preprocessing_messages.prepricessing_messages_for_scenarios import \
    PreprocessingScenariosMessages
from scenarios.scenario_models.history import History
from scenarios.behaviors.behaviors import Behaviors
from scenarios.user.reply_selector.reply_selector import ReplySelector


class User(BaseUser):

    forms: Forms
    last_fields: LastFields
    last_scenarios: LastScenarios
    scenario_models: ScenarioModels
    preprocessing_messages_for_scenarios: PreprocessingScenariosMessages
    behaviors: Behaviors
    history: History

    def __init__(self, id, message, db_data, settings, descriptions, parametrizer_cls, load_error=False):
        self.settings = settings
        try:
            user_values = json.loads(db_data) if db_data else None
        except ValueError:
            user_values = None
            load_error = True
        super(User, self).__init__(id, message, user_values, descriptions, load_error)
        self.__parametrizer_cls = parametrizer_cls
        self.do_not_save = False
        self.initial_db_data = db_data

        db_version = self.variables.get(self.USER_DB_VERSION, default=0)
        self.variables.set(self.USER_DB_VERSION, db_version + 1)
        log("%(class_name)s.__init__ USER %(uid)s LOAD db_version = %(db_version)s.", self,
                      {"db_version": str(db_version),
                       "uid": str(self.id)})

    @property
    def fields(self):
        return super(User, self).fields + [Field("forms", Forms, self.descriptions["forms"]),
                                           Field("last_fields", LastFields),
                                           Field("last_scenarios", LastScenarios, self.descriptions["last_scenarios"]),
                                           Field("scenario_models", ScenarioModels, self.descriptions["scenarios"]),
                                           Field("preprocessing_messages_for_scenarios", PreprocessingScenariosMessages,
                                                 self.descriptions["preprocessing_messages_for_scenarios"]),
                                           Field("behaviors", Behaviors, self.descriptions["behaviors"]),
                                           Field("history", History, self.descriptions["history"]),
                                           Field("gender_selector", ReplySelector)]

    @lazy
    def parametrizer(self):
        return self.__parametrizer_cls(self, {})

    def expire(self):
        super(User, self).expire()
        self.behaviors.expire()
        self.forms.expire()
        self.last_fields.expire()
        self.last_scenarios.expire()
        self.history.expire()

