__all__ = [
    "HistoryConstants"
]


class HistoryEventTypes:
    FIELD_EVENT = "field_event"
    END_SCENARIO = "end_scenario"

class HistoryContentFields:
    FIELD = "field"


class HistoryEventResults:
    FILLED = "filled"
    ASK_QUESTION = "ask_question"
    SUCCESS = "success"


class HistoryConstants:
    types = HistoryEventTypes
    event_results = HistoryEventResults
    content_fields = HistoryContentFields
