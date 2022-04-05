import typing
import os

import asyncio
import aiohttp
import aiohttp.web

import scenarios.logging.logger_constants as log_const
from core.db_adapter.db_adapter import DBAdapterException, db_adapter_factory
from core.logging.logger_utils import log
from core.message.from_message import SmartAppFromMessage
from core.utils.stats_timer import StatsTimer
from smart_kit.message.smartapp_to_message import SmartAppToMessage
from smart_kit.start_points.main_loop_http import BaseHttpMainLoop
from smart_kit.utils.monitoring import smart_kit_metrics


class AIOHttpMainLoop(BaseHttpMainLoop):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = aiohttp.web.Application()
        self.app.add_routes([aiohttp.web.route('*', '/health', self.get_health_check)])
        self.app.add_routes([aiohttp.web.route('*', '/{tail:.*}', self.iterate)])

    async def async_init(self):await self.db_adapter.connect()

    def get_db(self):
        db_adapter = db_adapter_factory(self.settings["template_settings"].get("db_adapter", {}))
        self.app.on_cleanup.append(self.close_db)
        return db_adapter

    # noinspection PyMethodMayBeStatic
    async def close_db(self, app):
        app["database"].cancel()
        await app["database"]

    async def load_user(self, db_uid, message):
        db_data = None
        load_error = False
        try:
            if self.db_adapter.IS_ASYNC:
                db_data = await self.db_adapter.get(db_uid)
            else:
                db_data = self.db_adapter.get(db_uid)
        except (DBAdapterException, ValueError):
            log("Failed to get user data", params={log_const.KEY_NAME: log_const.FAILED_DB_INTERACTION,
                                                   log_const.REQUEST_VALUE: str(message.value)}, level="ERROR")
            load_error = True
            smart_kit_metrics.counter_load_error(self.app_name)
        return self.user_cls(
            message.uid,
            message=message,
            db_data=db_data,
            settings=self.settings,
            descriptions=self.model.scenario_descriptions,
            parametrizer_cls=self.parametrizer_cls,
            load_error=load_error
        )

    async def save_user(self, db_uid, user, message):
        no_collisions = True
        if user.do_not_save:
            log("User %(uid)s will not saved", user=user, params={"uid": user.id,
                                                                  log_const.KEY_NAME: "user_will_not_saved"})
        else:

            no_collisions = True
            try:
                str_data = user.raw_str

                if self.db_adapter.IS_ASYNC:
                    if user.initial_db_data and self.user_save_check_for_collisions:
                        no_collisions = await self.db_adapter.replace_if_equals(
                            db_uid,
                            sample=user.initial_db_data,
                            data=str_data
                        )
                    else:
                        await self.db_adapter.save(db_uid, str_data)
                else:
                    if user.initial_db_data and self.user_save_check_for_collisions:
                        no_collisions = await self.db_adapter.replace_if_equals(
                            db_uid,
                            sample=user.initial_db_data,
                            data=str_data
                        )
                    else:
                        await self.db_adapter.save(db_uid, str_data)
            except (DBAdapterException, ValueError):
                log("Failed to set user data", params={log_const.KEY_NAME: log_const.FAILED_DB_INTERACTION,
                                                       log_const.REQUEST_VALUE: str(message.value)}, level="ERROR")
                smart_kit_metrics.counter_save_error(self.app_name)
            if not no_collisions:
                smart_kit_metrics.counter_save_collision(self.app_name)
        return no_collisions

    def run(self):
        aiohttp_config = self.settings["aiohttp"]
        if not aiohttp_config:
            log("aiohttp.yml is empty or missing. Server will be started with default parameters", level="WARN")
        asyncio.get_event_loop().run_until_complete(self.async_init())
        aiohttp.web.run_app(app=self.app, **aiohttp_config)

    def stop(self, signum, frame):
        pass

    async def handle_message(self, message: SmartAppFromMessage) -> typing.Tuple[int, str, SmartAppToMessage]:
        if not message.validate():
            answer = SmartAppToMessage(self.BAD_REQUEST_COMMAND, message=message, request=None)
            code = 400
            log(f"OUTGOING DATA: {answer.value} with code: {code}",
                params={log_const.KEY_NAME: "outgoing_policy_message", "msg_id": message.incremental_id})
            return code, "BAD REQUEST", answer

        answer, stats, user = await self.process_message(message)
        if not answer:
            answer = SmartAppToMessage(self.NO_ANSWER_COMMAND, message=message, request=None)
            code = 204
            log(f"OUTGOING DATA: {answer.value} with code: {code}",
                params={log_const.KEY_NAME: "outgoing_policy_message"}, user=user)
            return code, "NO CONTENT", answer

        answer_message = SmartAppToMessage(answer, message, request=None, validators=self.to_msg_validators)
        if answer_message.validate():
            code = 200
            log_answer = str(answer_message.value).replace("%", "%%")
            log(f"OUTGOING DATA: {log_answer} with code: {code}",
                params={log_const.KEY_NAME: "outgoing_policy_message"}, user=user)
            return code, "OK", answer_message
        else:
            code = 500
            answer = SmartAppToMessage(self.BAD_ANSWER_COMMAND, message=message, request=None)
            log(f"OUTGOING DATA: {answer.value} with code: {code}",
                params={log_const.KEY_NAME: "outgoing_policy_message"}, user=user)
            return code, "BAD ANSWER", answer

    async def process_message(self, message: SmartAppFromMessage, *args, **kwargs):
        stats = ""
        log("INCOMING DATA: %(masked_message)s",
            params={log_const.KEY_NAME: "incoming_policy_message", "masked_message": message.masked_value})
        db_uid = message.db_uid

        with StatsTimer() as load_timer:
            user = await self.load_user(db_uid, message)
        stats += "Loading time: {} msecs\n".format(load_timer.msecs)
        with StatsTimer() as script_timer:
            commands = await self.model.answer(message, user)
            if commands:
                answer = self._generate_answers(user, commands, message)
            else:
                answer = None

        stats += "Script time: {} msecs\n".format(script_timer.msecs)
        with StatsTimer() as save_timer:
            await self.save_user(db_uid, user, message)
        stats += "Saving time: {} msecs\n".format(save_timer.msecs)
        log(stats, params={log_const.KEY_NAME: "timings"})
        await self.postprocessor.postprocess(user, message)
        return answer, stats, user

    async def get_health_check(self, request: aiohttp.web.Request):
        status, reason, answer = 200, "OK", "ok"
        return aiohttp.web.json_response(
            status=status, reason=reason, data=answer,
        )

    async def iterate(self, request: aiohttp.web.Request):
        headers = self._get_headers(request.headers)
        body = await request.text()
        message = SmartAppFromMessage(body, headers=headers, headers_required=False,
                                      validators=self.from_msg_validators)

        status, reason, answer = await self.handle_message(message)

        return aiohttp.web.json_response(
            status=status, reason=reason, data=answer.as_dict,
            headers=self._get_outgoing_headers(headers, answer.command)
        )
