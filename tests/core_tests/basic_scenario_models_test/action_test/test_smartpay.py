import unittest

from core.basic_models.actions.smartpay import SmartPayCreateAction
from smart_kit.utils.picklable_mock import PicklableMagicMock


class SmartPayCreateActionTest(unittest.TestCase):
    def test_run(self):
        items = {
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
        user = PicklableMagicMock()
        action = SmartPayCreateAction(items)
        result = action.run(user, None)
        print(result)
