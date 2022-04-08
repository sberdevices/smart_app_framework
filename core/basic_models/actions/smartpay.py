from typing import Optional, Dict, Union, List

from core.basic_models.actions.command import Command
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult
from smart_kit.action.http import HTTPRequestAction


class SmartPayAction(HTTPRequestAction):
    url = None
    method = None
    store = None

    def __init__(self, items, id=None):
        request_params = items.get("request_params")
        smartpay_params = items.get("smartpay_params")

        items = {
            "params": {"method": self.method, "url": self.url},
            "store": self.store,
            "behavior": items["behavior"]
        }
        if request_params:
            items["params"]["params"] = request_params
        if smartpay_params:
            items["params"]["json"] = smartpay_params

        super().__init__(items, id)

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self.http_action.method_params["url"] = \
            user.settings["template_settings"]["smartpay_url"] + self.http_action.method_params["url"]
        return super().run(user, text_preprocessing_result, params)


class SmartPayCreateAction(SmartPayAction):

    """
    Example::
        {
            "type": "smartpay_create",
            "behavior": "some_behavior", // обязательный параметр
            "smartpay_params": { // обязательноый параметр
                "ptype": 1,
                "invoice": {
                    "purchaser": {
                        "email": "test@test.ru",
                        "phone": "71111111111",
                        "contact": "phone"
                    },
                    "delivery_info": {
                        "address": {
                            "country": "RU",
                            "city": "Москва",
                            "address": "Кутузовский проспект, 32"
                        },
                        "delivery_type": "courier",
                        "description": "Спросить '\''Где тут Сбердевайсы?'\''"
                    },
                    "invoice_params": [
                        {
                            "key": "packageName",
                            "value": "SbERdeVICEs"
                        },
                        {
                            "key": "packageKey",
                            "value": "ru.sberdevices.test"
                        }
                    ],
                    "order": {
                        "order_id": "a952b7ee-c928-4586-bd05-d932c21f749",
                        "order_number": "1952",
                        "order_date": "2021-04-07T08:24:37.729Z",
                        "service_id": "13",
                        "amount": 79900,
                        "currency": "RUB",
                        "purpose": "Покупка продуктов",
                        "description": "Заказ № 22-1952. Покупка продуктов",
                        "language": "ru-RU",
                        "tax_system": 0,
                        "order_bundle": [
                            {
                                "position_id": 1,
                                "name": "Транзистор",
                                "item_params": [
                                    {
                                        "key": "_itemAttributes_supplier_info.name",
                                        "value": "ООО Ромашка"
                                    },
                                    {
                                        "key": "_itemAttributes_supplier_info.inn",
                                        "value": "5009053292"
                                    },
                                    {
                                        "key": "_itemAttributes_nomenclature",
                                        "value": "Å\u001e13622200005881"
                                    },
                                    {
                                        "key": "_itemAttributes_agent_info.type",
                                        "value": "7"
                                    }

                                ],
                                "quantity": {
                                    "value": 1,
                                    "measure": "шт."
                                },
                                "item_amount": 79801,
                                "currency": "RUB",
                                "item_code": "21ff407a-fa98-11e8-80c5-0cc47a817926",
                                "item_price": 79801,
                                "discount_type": "amount",
                                "discount_value": 17687,
                                "tax_type": 6
                            },
                            {
                                "position_id": 2,
                                "name": "Тиристор",
                                "item_params": [
                                    {
                                        "key": "code",
                                        "value": "123значение321"
                                    },
                                    {
                                        "key": "pack",
                                        "value": "100"
                                    },
                                    {
                                        "key": "_itemAttributes_supplier_info.name",
                                        "value": "ООО Платежи"
                                    },
                                    {
                                        "key": "_itemAttributes_supplier_info.inn",
                                        "value": "7730253720"
                                    }
                                ],
                                "quantity": {
                                    "value": 1,
                                    "measure": "шт."
                                },
                                "item_amount": 99,
                                "currency": "RUB",
                                "item_code": "21ff407c-fa98-11e8-80c5-0cc47a817926",
                                "item_price": 99,
                                "discount_type": "amount",
                                "discount_value": 21,
                                "tax_type": 6,
                            }
                        ]
                    }
                }
            }
        }
    """

    def __init__(self, items, id=None):
        self.url = "/invoices"
        self.method = self.POST
        self.store = "smartpay_create_answer"
        super().__init__(items, id)


class SmartPayPerformAction(SmartPayAction):

    """
    Example::
        {
            "type": "smartpay_perform",
            "behavior": "some_behavior", // обязательный параметр
            "invoice_id": "0", // обязательный параметр
            "smartpay_params": { // обязательынй параметр
                "user_id": {
                    "partner_client_id": "2223"
                },
                "operations": [
                    {
                        "operation": "payment",
                        "code": "invoice",
                        "value": "167900"
                    }
                ],
                "device_info": {
                    "device_platform_type": "iOS",
                    "device_platform_version": "13.6.1",
                    "device_model": "iPhone 7",
                    "device_manufacturer": "Apple",
                    "device_id": "83c3f257-46d8-41fe-951b-f79d04e288c2",
                    "surface": "SBOL",
                    "surface_version": "11.5.0"
                },
                "return_url": "https://ok",
                "fail_url": "https://fail"
            }
        }
    """

    def __init__(self, items, id=None):
        self.url = f"/invoices/{items['invoice_id']}"
        self.method = self.POST
        self.store = "smartpay_perform_answer"
        super().__init__(items, id)


class SmartPayGetStatusAction(SmartPayAction):

    """
    Example::
        {
            "type": "smartpay_get_status",
            "behavior": "some_behavior", // обязательный параметр
            "invoice_id": "0", // обязательный параметр
            "inv_status": "executed", // опциональный параметр
            "wait": 50 // опциональный параметр
        }
    """

    def __init__(self, items, id=None):
        items["request_params"] = {}
        inv_status = items.get("inv_status")
        wait = items.get("wait")
        if inv_status:
            del items["inv_status"]
            items["request_params"]["inv_status"] = inv_status
        if wait:
            del items["wait"]
            items["request_params"]["wait"] = wait

        self.url = f"/invoices/{items['invoice_id']}"
        self.method = self.GET
        self.store = "smartpay_get_status_answer"
        super().__init__(items, id)


class SmartPayConfirmAction(SmartPayAction):

    """
    Example::
        {
            "type": "smartpay_confirm",
            "invoice_id": "0", // обязательный параметр
            "smartpay_params": { // опциональный параметр, задаётся для неполной суммы (см. доку SmartPay API)
                "invoice": {
                    "order": {
                        "amount": 79801,
                        "currency": "RUB",
                        "order_bundle": [
                            {
                                "position_id": 1,
                                "name": "Транзистор",
                                "quantity": {
                                    "value": 1,
                                    "measure": "шт."
                                },
                                "item_amount": 79801,
                                "currency": "RUB",
                                "item_code": "21ff407a-fa98-11e8-80c5-0cc47a817926",
                                "item_price": 79801
                            }
                        ]
                    }
                }
            }
        }
    """

    def __init__(self, items, id=None):
        self.url = f"/invoices/{items['invoice_id']}"
        self.method = self.PUT
        self.store = "smartpay_confirm_answer"
        super().__init__(items, id)


class SmartPayDeleteAction(SmartPayAction):

    """
    Example::
        {
            "type": "smartpay_delete",
            "behavior": "my_behavior", // обязательынй параметр
            "invoice_id": "0" // обязательынй параметр
        }
    """

    def __init__(self, items, id=None):
        self.url = f"/invoices/{items['invoice_id']}"
        self.method = self.DELETE
        self.store = "smartpay_delete_answer"
        super().__init__(items, id)


class SmartPayRefundAction(SmartPayAction):

    """
    Example::
        {
            "type": "smartpay_refund",
            "behavior": "some_behavior", // обязательный параметр
            "invoice_id": "0", // обязательный параметр
            "smartpay_params": { // опциональный параметр, задаётся при частичном возврате (см. доку SmartPay API)
                "invoice": {
                    "order": {
                        "current_amount": 79900,
                        "refund_amount": 79801,
                        "currency": "RUB",
                        "order_bundle": [
                            {
                                "position_id": 1,
                                "name": "Транзистор",
                                "quantity": {
                                    "value": 1
                                },
                                "item_amount": 79801,
                                "item_code": "21ff407a-fa98-11e8-80c5-0cc47a817926"
                            }
                        ]
                    }
                }
            }
        }
    """

    def __init__(self, items, id=None):
        self.url = f"/invoices/{items['invoice_id']}"
        self.method = self.PATCH
        self.store = "smartpay_refund_answer"
        super().__init__(items, id)
