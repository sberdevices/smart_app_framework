from abc import ABCMeta, abstractmethod
from typing import Optional, Type, TypeVar, Iterable, Dict, Any, Union, List

from attr import dataclass

from core.basic_models.actions.basic_actions import Action
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.basic_models.actions.command import Command
from core.message.message_constants import MSG_USERID_KEY
from core.message.message_constants import MSG_USERCHANNEL_KEY

TComponent = TypeVar('TComponent')


class ISession(metaclass=ABCMeta):
    """ `ISession` - объект-сессия, представленный в виде набора компонентов.

    Обычно создается одна сессия на одного пользователя (ключом является userId).
    Управление жизненным циклом сессии обеспечивается через `SessionManager`.
    """

    @abstractmethod
    def get_key(self) -> str: ...

    @abstractmethod
    def add_component(self, component: TComponent):
        """ Добавляет компонент

        :param component: Экземпляр компонента
        :return: None
        """

    @abstractmethod
    def get_component(self, typ: Type[TComponent]) -> TComponent:
        """ Получить компонент сессии по типу. Если компонента с определенным типов в сессии
        не обнаружено - отбрасывается KeyError исключение.

        :param typ: Тип запрашиваемого компонента
        :raises KeyError: Исключение в случае когда компонент запрашиваемого типа не обнаружен
        :return: Объект компонента
        """

    def __iter__(self) -> Iterable[TComponent]:
        """ Итератор компонентов

        :return: TComponent
        """


@dataclass(slots=True)
class RtdmService:
    http_adapter: Union[RtdmHttpAdapter, MockHttpAdapter]
    transport_sender: ITransportSender
    direct_transport_sender: ITransportSender
    session_manager: ISessionManager
    callback_dispatcher: ICallbackDispatcher

    rtdm_system_name: str = "nlpSystem"

    # Задаем Engine в run-time во избежание рекурсивных зависимостей при DI resolve
    _engine: Optional[IEngine] = attrib(init=False, default=None)

    def set_engine(self, engine: IEngine):
        self._engine = engine

    async def send_notifications(
            self,
            device: Device,
            request: IRequest,
            notifications_data: RtdmNotificationsDataLegacy
    ):
        body = RtdmViewedEventsMessage(
            messageId=request.get_data().message_id,
            uuid=request.get_data().uuid,
            payload=RtdmViewedEventsPayload(
                notifications=notifications_data.notifications,
                device=device
            ),
            sessionId=request.get_data().session_id
        )
        transport_message = TransportMessage(
            key=request.get_data().key,
            body=body
        )
        await self.transport_sender.send(transport_message)

    async def send_notification_direct(
            self,
            request: IRequest,
            notification_id,
            notification_code,
            feedback_status,
            description
    ):
        body = RtdmEventMessage(
            messageId=request.get_data().message_id,
            userId=request.get_data().uuid.userId,
            userChannel=request.get_data().uuid.userChannel,
            notificationId=notification_id,
            notificationCode=notification_code,
            feedbackStatus=feedback_status,
            description=description
        )
        transport_message = TransportMessage(
            key=request.get_data().key,
            body=body
        )
        await self.direct_transport_sender.send(transport_message)

    async def request_rtdm_info(self, session: ISession, callback: Callback):
        request = session.get_component(IRequest)
        device = session.get_component(Device)
        callbacks_data = session.get_component(CallbacksData)

        token = request.get_data().erib_token
        if not token:
            _logger.warning(f"Can not request RTDM info, missing ERIB token")
            await self.callback_dispatcher.dispatch_error(
                error=MissingEribToken(),
                callback=callback,
                session=session
            )
            return

        callbacks_data.add(callback)

        body = RtdmInfoRequestMessage(
            messageId=request.get_data().message_id,
            uuid=request.get_data().uuid,
            payload=RtdmInfoRequestPayload(
                token=token,
                epkId=request.get_data().epk_id,
                device=device
            ),
            sessionId=request.get_data().session_id
        )
        transport_message = TransportMessage(
            key=request.get_data().key,
            body=body
        )

        await request.suspend()

        asyncio.ensure_future(
            deferred_callback_timeout_check(
                callback=callback,
                session_manager=self.session_manager,
                engine=self._engine
            )
        )

        await self.transport_sender.send(transport_message)

    async def request_rtdm_info_http(
            self, session: ISession
    ) -> Optional[RtdmInfoResponse]:

        dp_request = session.get_component(IRequest)

        if not self.http_adapter.is_enabled():
            _logger.warning("RTDM integration is disabled.")
            return None

        if not dp_request.get_data().epk_id:
            _logger.warning("Could not request RTDM without epkId.")
            return None

        response = await self.http_adapter.request(
            url=self.http_adapter.url,
            timeout=self.http_adapter.timeout,
            method=self.http_adapter.http_method,
            json=asdict(
                RtdmRequest(
                    epkId=dp_request.get_data().epk_id,
                    systemName=self.rtdm_system_name
                )
            ),
            session=session
        )

        if response["status"] != 200:
            return None

        return spec.load(RtdmInfoResponse, response["data"])


class RtdmEventAction(Action):
    """
    Экшен обратного потока, для отправки пользовательских событий в RTDM.

    Пример::

        {
            "type": "rtdm_info_event_action",
            "notification_id": "{{ rtdm.offers[0].notificationId }}",
            "feedback_status": "FS",
            "description": "Вклад ВА ПП"
        }
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(RtdmEventAction, self).__init__(items, id)
        self.notification_id: str = items["notification_id"]
        self.feedback_status: str = items["feedback_status"]
        self.description: str = items.get("description")

    ALLOWED_FEEDBACK_STATUSES = {"FS", "QS", "FA", "QA", "FI", "QI"}

    service: RtdmService

    notification_id: UnifiedTemplate
    feedback_status: UnifiedTemplate
    description: Optional[UnifiedTemplate] = None

    @preprocess_fields(self, user, text_preprocessing_result, params)
    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        """
        Получ
        До этого принимались аргументы self, session: ISession

        :param user:
        :param text_preprocessing_result:
        :param params:
        :return:
        """
        rtdm_info = session.get_component(RtdmData)  # получить объект с offers: List[RtdmInfoOffer], services:
        # List[RtdmInfoService], last_updated: float, lifetime: float
        # params = collect_template_params(session)  # получить все компоненты сессии типа ITemplateParametersProvider
        if params is None:
            params = user.parametrizer.collect(text_preprocessing_result)
        else:
            params.update(user.parametrizer.collect(text_preprocessing_result))
        notification_id = self.notification_id.render(params)  # вставить невставленные Jinja-вставки в notification_id
        offer_or_service = rtdm_info.get_item(notification_id=notification_id)  # получить оффер или сервис по айди
        if offer_or_service:  # если оффер или сервис был получен
            description = self.description.render(params) if self.description else None  # сформировать описание акшна
            feedback_status = self.feedback_status.render(params)  # срендерить джинджу фидбек статуса  |  все ли акшны во фрейме рендрят аргументы?
            if feedback_status not in RtdmEventAction.ALLOWED_FEEDBACK_STATUSES:  # проверить валидность фидбек статуса
                raise ValueError(
                    f'Invalid RTDM event response. '
                    f'Feedback status should be one of '
                    f'{RtdmEventAction.ALLOWED_FEEDBACK_STATUSES}'
                )  # кинуть ошибку если фидбек не валиден
            # request = session.get_component(IRequest)  # получить запрос из сессии
            # сформировать сообщение (нотификейшн) и отправить в Real-Time Decision Manager
            # original type: RtdmEventMessage
            body = {
                "messageId": user.message.as_dict[user.message.MESSAGE_ID],  # original: request.get_data().message_id
                "userId": user.message.as_dict.uuid[MSG_USERID_KEY],  # original: request.get_data().uuid.userId
                "userChannel": user.message.as_dict.uuid[MSG_USERCHANNEL_KEY],  # original: request.get_data().uuid.userChannel
                "notificationId": notification_id,
                "notificationCode": offer_or_service.get_notification_code(),
                "feedbackStatus": feedback_status,
                "description": description
            }
            # original type: TransportMessage
            transport_message = {
                "key": user.message.as_dict[user.message.MESSAGE_NAME],  # original: request.get_data().key  |  correct replacement?
                "body": body
            }
            await self.direct_transport_sender.send(transport_message)  # could be KafkaSender.send
