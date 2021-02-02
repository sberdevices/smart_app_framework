KEY_NAME = "key_name"

STARTUP_VALUE = "app_startup"
RUNNING_VALUE = "app_running"
STATS_VALUE = "stats"
ANSWER_VALUE = "answer"
UPDATE_CONTENT_VALUE = "app_update_content"
SERVICE_MANAGEMENT_VALUE = "service_management"
SERVICE_MANAGEMENT_TIME_VALUE = "service_management_time_ms"
SKIP_INCOMING_MESSAGE_VALUE = "skip_incoming_message"
FAILED_DB_INTERACTION = "failed_db_interaction"

GREENFIELD_VALUE = "greenfiels"
AB_GROUPS_VALUE = "ab_groups"
REQUEST_VALUE = "request"
SERVICE_REQUEST_VALUE = "service_request"
REPLY_VALUE = "reply"
CHOSEN_SCENARIO_VALUE = "chosen_scenario"
CHOSEN_ACTION_VALUE = "chosen_action"
CHOSEN_SUB_SCENARIO_VALUE = "chosen_sub_scenario"
DISTANCE_VALUE = "distance"
SCENARIO_DESCRIPTION_VALUE = "scenario_description"
ROOT_ID_VALUE = "root_id"
INTENT_ID_VALUE = "intent_id"
FILLER_EXTRACT_VALUE = "filler_extract"
SCENARIO_RESULT_VALUE = "scenario_result"
REQUIREMENT_CHECK_VALUE = "requirement_check"
CHECKING_NODE_ID_VALUE = "checking_node_id"
NORMALIZED_TEXT_VALUE = "normalized_text"
PREPROCESSING_TIME_VALUE = "preprocessing_time_ms"
TIME_FROM_KAFKA_MSG_CREATION = "time_from_kafka_msg_creation"
ACTION_BEFORE_VALUE = "action_before"
DIALOG_ERROR_VALUE = "dialog_error"
FILLER_RESULT_VALUE = "filler_result"
CHOSEN_NODE_ID_VALUE = "chosen_node_id"
BEGIN_RECORD_VALUE = "BEGIN_RECORD"
END_RECORD_VALUE = "END_RECORD"
SCENARIO_VALUE = "scenario"
CLASSIFIER_VALUE = "classifier"
SELF_SERVICE_RUN_VALUE = "self_service_run"
SELF_SERVICE_MISSTATE_VALUE = "self_service_misstate"
SELF_SERVICE_SUCCESS_VALUE = "self_service_success"
SELF_SERVICE_FAIL_VALUE = "self_service_fail"

BEHAVIOR_ADD_VALUE = "behavior_add"
BEHAVIOR_MISSTATE_VALUE = "behavior_misstate"
BEHAVIOR_CHECK_MISSTATE_VALUE = "behavior_check_misstate"
BEHAVIOR_DATA_VALUE = "behavior_data"
BEHAVIOR_GOT_SAVED_VALUE = "behavior_got_saved"
BEHAVIOR_SUCCESS_VALUE = "behavior_success"
BEHAVIOR_FAIL_VALUE = "behavior_fail"
BEHAVIOR_TIMEOUT_VALUE = "behavior_timeout"
BEHAVIOR_CALLBACK_ID_VALUE = "behavior_callback_id"
BEHAVIOR_ID_VALUE = "behavior_id"

NORMALIZE_INTENT_VALUE = "normalize_intent"
SKIPPED_INTENT_VALUE = 'skipped_intent'
INVALID_INTENT_VALUE = 'invalid_intent'
CONTAINER_NAME_VALUE = 'container_name'
CONTAINER_REQUIREMENT_CHECK_VALUE = 'container_requirement_check_value'


AB_GROUPS_MESSAGE = "%(key_name)s=%(ab_groups)s"
REPLY_MESSAGE = "%(key_name)s=%(reply)s"
LAST_SCENARIO_MESSAGE = "Dialog manager run chosen scenario info: %(key_name)s=%(chosen_scenario)s, " \
                        "scenario_description=%(scenario_description)s"
DIALOG_SCENARIO_MESSAGE = "Dialog manager run last scenario info: %(key_name)s=%(chosen_scenario)s, " \
                          "distance=%(distance)s, scenario_description=%(scenario_description)s, " \
                          "root_id=%(root_id)s"
INVALID_INTENT_MESSAGE = 'Invalid intent, intent=%(intent_id)s'
CLASSIFIER_MESSAGE = "classifier:%(classifier_name)s, result: %(result)s, " \
                     "weights: %(score)s, time: %(time)s ms"
CHOSEN_SCENARIO_MESSAGE = "%(key_name)s=%(chosen_scenario)s"
CHOSEN_ACTION_MESSAGE = "%(key_name)s=%(chosen_action)s"
CHOSEN_SUB_SCENARIO_MESSAGE = "%(key_name)s=%(chosen_sub_scenario)s"
DISTANCE_MESSAGE = "%(key_name)s=%(distance)s"
INTENT_ID_MESSAGE = "%(key_name)s=%(intent_id)s"
FILLER_EXTRACT_MESSAGE = "%(key_name)s=%(filler_extract)s"
SCENARIO_RESULT_MESSAGE = "%(key_name)s=%(scenario_result)s"
REQUIREMENT_CHECK_MESSAGE = "%(key_name)s=%(requirement_check)s"
CHECKING_NODE_ID_MESSAGE = "%(key_name)s=%(checking_node_id)s"
NORMALIZED_TEXT_MESSAGE = "%(key_name)s=%(normalized_text)s"
ACTION_BEFORE_MESSAGE = "%(key_name)s=%(action_before)s"
DIALOG_ERROR_MESSAGE = "%(key_name)s=%(dialog_error)s"
FILLER_RESULT_MESSAGE = "%(key_name)s=%(filler_result)s"
CHOSEN_NODE_ID_MESSAGE = "%(key_name)s=%(chosen_node_id)s"
SKIPPED_INTENT_MESSAGE = "Skipped intent %(intent_id)s, scenario is not available"
CONTAINER_REQUIREMENT_CHECK_MESSAGE = 'Classifier container requirement check: result: ' \
                                      '%(requirement_check)s, container: %(container_name)s'

CALLBACK_ID_HEADER = "app_callback_id"
