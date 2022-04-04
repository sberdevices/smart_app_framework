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
            user.settings["template_settings"]["smart_pay_url"] + self.http_action.method_params["url"]
        return super().run(user, text_preprocessing_result, params)


class SmartPayCreateAction(SmartPayAction):
    def __init__(self, items, id=None):
        self.url = "/invoices"
        self.method = self.POST
        self.store = "smartpay_create_answer"
        super().__init__(items, id)


class SmartPayPerformAction(SmartPayAction):
    def __init__(self, items, id=None):
        self.url = f"/invoices/{items['invoice_id']}"
        self.method = self.POST
        self.store = "smartpay_perform_answer"
        super().__init__(items, id)


class SmartPayGetStatusAction(SmartPayAction):
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
    def __init__(self, items, id=None):
        self.url = f"/invoices/{items['invoice_id']}"
        self.method = self.PUT
        self.store = "smartpay_confirm_answer"
        super().__init__(items, id)


class SmartPayDeleteAction(SmartPayAction):
    def __init__(self, items, id=None):
        self.url = f"/invoices/{items['invoice_id']}"
        self.method = self.DELETE
        self.store = "smartpay_delete_answer"
        super().__init__(items, id)


class SmartPayRefundAction(SmartPayAction):
    def __init__(self, items, id=None):
        self.url = f"/invoices/{items['invoice_id']}"
        self.method = self.PATCH
        self.store = "smartpay_refund_answer"
        super().__init__(items, id)
