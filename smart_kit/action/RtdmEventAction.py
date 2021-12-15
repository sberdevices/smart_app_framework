from core.basic_models.actions.string_actions import NodeAction
from abc import ABCMeta, abstractmethod
from typing import Optional, Type, TypeVar, Iterable

from attr import dataclass


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



class IAction(metaclass=ABCMeta):

    @abstractmethod
    async def run(self, session: ISession): ...


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


@dataclass(slots=True)
class RtdmEventAction(IAction):
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

    class Meta:
        name = "rtdm_info_event_action"

    ALLOWED_FEEDBACK_STATUSES = {"FS", "QS", "FA", "QA", "FI", "QI"}

    service: RtdmService

    notification_id: UnifiedTemplate
    feedback_status: UnifiedTemplate
    description: Optional[UnifiedTemplate] = None

    async def run(self, session: ISession):
        rtdm_info = session.get_component(RtdmData)
        params = collect_template_params(session)
        notification_id = self.notification_id.render(params)
        offer_or_service = rtdm_info.get_item(notification_id=notification_id)
        if offer_or_service:
            description = self.description.render(params) if self.description else None
            feedback_status = self.feedback_status.render(params)
            if feedback_status not in RtdmEventAction.ALLOWED_FEEDBACK_STATUSES:
                raise ValueError(
                    f'Invalid RTDM event response. '
                    f'Feedback status should be one of '
                    f'{RtdmEventAction.ALLOWED_FEEDBACK_STATUSES}'
                )
            request = session.get_component(IRequest)
            await self.service.send_notification_direct(
                request=request,
                notification_id=notification_id,
                notification_code=offer_or_service.get_notification_code(),
                feedback_status=feedback_status,
                description=description
            )