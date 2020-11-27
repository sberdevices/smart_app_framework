import threading
from wsgiref.simple_server import make_server

import scenarios.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.utils.stats_timer import StatsTimer
from core.message.from_message import SmartAppFromMessage

from smart_kit.compatibility.commands import combine_commands
from smart_kit.message.smartapp_to_message import SmartAppToMessage
from smart_kit.start_points.base_main_loop import BaseMainLoop
from core.configs.global_constants import CALLBACK_ID_HEADER


class HttpMainLoop(BaseMainLoop):
    HEADER_START_WITH = "HTTP_SMART_APP_"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._server = None

    def __call__(self, environ, start_response):
        return self.iterate(environ, start_response)

    def _generate_answers(self, user, commands, message, **kwargs):
        commands = combine_commands(commands, user)
        if len(commands) > 1:
            raise ValueError
        answer = commands.pop() if commands else None

        return answer

    # noinspection PyMethodMayBeStatic
    def _get_outgoing_headers(self, incoming_headers, command=None):
        headers = {"CONTENT_TYPE": "application/json"}
        headers.update(incoming_headers)

        if command:
            callback_id = command.request_data.get(CALLBACK_ID_HEADER)
            if callback_id:
                headers[CALLBACK_ID_HEADER] = callback_id

        return list(headers.items())

    def handle_message(self, message: SmartAppFromMessage, stats, *args, **kwargs):
        log("INCOMING DATA: {}".format(message.masked_value),
                      params={log_const.KEY_NAME: "incoming_policy_message"})
        db_uid = message.db_uid

        with StatsTimer() as load_timer:
            user = self.load_user(db_uid, message)
        stats += "Loading time: {} msecs\n".format(load_timer.msecs)
        with StatsTimer() as script_timer:
            commands = self.model.answer(message, user)
            answer = self._generate_answers(user, commands, message)

        stats += "Script time: {} msecs\n".format(script_timer.msecs)
        with StatsTimer() as save_timer:
            self.save_user(db_uid, user, message)
        stats += "Saving time: {} msecs\n".format(save_timer.msecs)

        return answer, stats

    def _get_headers(self, environ):
        return [(key, value) for key, value in environ.items() if key.startswith(self.HEADER_START_WITH)]

    def iterate(self, environ, start_response):
        stats = ""
        with StatsTimer() as poll_timer:
            try:
                content_length = int(environ.get('CONTENT_LENGTH', '0'))
                request = environ["wsgi.input"].read(content_length).decode()
                headers = self._get_headers(environ)
            except KeyError:
                log("Error in request data", level="ERROR")
                raise Exception("Error in request data")

        stats += "Polling time: {} msecs\n".format(poll_timer.msecs)

        message = SmartAppFromMessage(request, headers=headers, headers_required=False)
        if not message.validate():
            start_response("400 BAD REQUEST", self._get_outgoing_headers(headers))
            return [b'{"message": "invalid message"}']

        answer, stats = self.handle_message(message, stats)
        with StatsTimer() as publish_timer:
            if not answer:
                start_response("204 NO CONTENT", self._get_outgoing_headers(headers))
                return [b'{"message": "no answer"}']
            start_response("200 OK", self._get_outgoing_headers(headers, answer))
            answer = SmartAppToMessage(answer, message, request=None)

        stats += "Publishing time: {} msecs".format(publish_timer.msecs)
        log(stats, params={log_const.KEY_NAME: "timings"})
        return [answer.value.encode()]

    def run(self):
        self._server = make_server('localhost', 8000, self.iterate)
        log(
            '''
                Application start via "python manage.py run_app" recommended only for local testing. 
                For production it is recommended to start using "gunicorn --config wsgi_config.py 'wsgi:create_app()'
            ''',
            level="WARNING")
        self._server.serve_forever()

    def stop(self, signum, frame):
        if self._server:
            self._server.server_close()
        exit(0)
