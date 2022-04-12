import unittest
from unittest.mock import patch

from core.basic_models.actions.smartpay import SmartPayCreateAction, SmartPayPerformAction, SmartPayGetStatusAction, \
    SmartPayConfirmAction, SmartPayDeleteAction, SmartPayRefundAction
from smart_kit.utils.picklable_mock import PicklableMock
from tests.smart_kit_tests.action.test_base_http_action import BaseHttpRequestActionTest


class SmartPayActionTest(unittest.TestCase):
    def setUp(self):
        self.user = PicklableMock(
            parametrizer=PicklableMock(collect=lambda *args, **kwargs: {}),
            descriptions={
                "behaviors": {
                    "my_behavior": PicklableMock(timeout=PicklableMock(return_value=3))
                }
            },
            settings={
                "template_settings": {
                    "smartpay_url": "0.0.0.0"
                }
            }
        )

    @patch('requests.request')
    def test_create(self, request_mock: PicklableMock):
        items = {
            "behavior": "my_behavior",
            "smartpay_params": {
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

        BaseHttpRequestActionTest.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        action = SmartPayCreateAction(items)
        action.run(self.user, None, {})
        request_mock.assert_called_with(url="0.0.0.0/invoices", method="POST",
                                        timeout=3, json=items.get("smartpay_params"))
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("smartpay_create_answer", {'data': 'value'})

    @patch('requests.request')
    def test_perform(self, request_mock: PicklableMock):
        items = {
            "behavior": "my_behavior",
            "invoice_id": "0",
            "smartpay_params": {
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

        BaseHttpRequestActionTest.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        action = SmartPayPerformAction(items)
        action.run(self.user, None, {})
        request_mock.assert_called_with(url="0.0.0.0/invoices/0", method="POST",
                                        timeout=3, json=items.get("smartpay_params"))
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("smartpay_perform_answer", {'data': 'value'})

    @patch('requests.request')
    def test_get_status(self, request_mock: PicklableMock):
        items = {
            "behavior": "my_behavior",
            "invoice_id": "0",
            "inv_status": "executed",
            "wait": 50
        }

        BaseHttpRequestActionTest.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        action = SmartPayGetStatusAction(items)
        action.run(self.user, None, {})
        request_mock.assert_called_with(url="0.0.0.0/invoices/0", method="GET",
                                        timeout=3, params={"inv_status": "executed", "wait": 50})
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("smartpay_get_status_answer", {'data': 'value'})

    @patch('requests.request')
    def test_partial_confirm(self, request_mock: PicklableMock):
        items = {
            "behavior": "my_behavior",
            "invoice_id": "0",
            "smartpay_params": {
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

        BaseHttpRequestActionTest.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        action = SmartPayConfirmAction(items)
        action.run(self.user, None, {})
        request_mock.assert_called_with(url="0.0.0.0/invoices/0", method="PUT",
                                        timeout=3, json=items["smartpay_params"])
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("smartpay_confirm_answer", {'data': 'value'})

    @patch('requests.request')
    def test_full_confirm(self, request_mock: PicklableMock):
        items = {
            "behavior": "my_behavior",
            "invoice_id": "0",
        }

        BaseHttpRequestActionTest.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        action = SmartPayConfirmAction(items)
        action.run(self.user, None, {})
        request_mock.assert_called_with(url="0.0.0.0/invoices/0", method="PUT", timeout=3)
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("smartpay_confirm_answer", {'data': 'value'})

    @patch('requests.request')
    def test_delete(self, request_mock: PicklableMock):
        items = {
            "behavior": "my_behavior",
            "invoice_id": "0",
        }

        BaseHttpRequestActionTest.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        action = SmartPayDeleteAction(items)
        action.run(self.user, None, {})
        request_mock.assert_called_with(url="0.0.0.0/invoices/0", method="DELETE", timeout=3)
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("smartpay_delete_answer", {'data': 'value'})

    @patch('requests.request')
    def test_partial_refund(self, request_mock: PicklableMock):
        items = {
            "behavior": "my_behavior",
            "invoice_id": "0",
            "smartpay_params": {
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

        BaseHttpRequestActionTest.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        action = SmartPayRefundAction(items)
        action.run(self.user, None, {})
        request_mock.assert_called_with(url="0.0.0.0/invoices/0", method="PATCH",
                                        timeout=3, json=items["smartpay_params"])
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("smartpay_refund_answer", {'data': 'value'})

    @patch('requests.request')
    def test_full_refund(self, request_mock: PicklableMock):
        items = {
            "behavior": "my_behavior",
            "invoice_id": "0",
        }

        BaseHttpRequestActionTest.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        action = SmartPayRefundAction(items)
        action.run(self.user, None, {})
        request_mock.assert_called_with(url="0.0.0.0/invoices/0", method="PATCH", timeout=3)
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("smartpay_refund_answer", {'data': 'value'})
