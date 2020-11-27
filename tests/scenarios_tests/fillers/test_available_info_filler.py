from unittest import TestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.field_filler_description import AvailableInfoFiller


class MockParametrizer:
    def __init__(self, user, items=None):
        self.items = items or {}
        self.user = user
        self.filter = items.get("filter") or False

    def collect(self, text_preprocessing_result=None, filter_params=None):
        data = {
            "person_info": self.user.person_info.raw,
            "payload": self.user.message.payload,
            "uuid": self.user.message.uuid

        }
        if self.filter:
            data.update({"filter": "filter_out"})
        return data


class TestAvailableInfoFiller(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.address = "Address!"
        payload_items = {'value': '{{payload.sf_answer.address}}'}
        cls.payload_filler = AvailableInfoFiller(payload_items)

    def setUp(self):
        template = Mock()
        template.get_template = Mock(return_value=[])
        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = Mock()
        user.person_info = Mock()
        user.descriptions = {"render_templates": template}
        self.user = user

    def test_getting_person_info_value(self):
        name = "Name!"
        surname = "Surname!"
        self.user.person_info.raw = Mock()
        self.user.person_info.raw.full_name = {"name": name, "surname": surname}
        person_info_items = {'value': '{{person_info.full_name.surname}}'}
        person_info_filler = AvailableInfoFiller(person_info_items)

        result = person_info_filler.extract(None, self.user)
        self.assertEqual(result, surname)

    def test_getting_payload_value(self):
        self.user.message.payload = {"sf_answer": {"address": self.address}}
        result = self.payload_filler.extract(None, self.user)
        self.assertEqual(result, self.address)

    def test_getting_uuid_value(self):
        uuid = "15"
        self.user.message.uuid = {"chatId": uuid}
        uuid_items = {'value': '{{uuid.chatId}}'}
        uuid_filler = AvailableInfoFiller(uuid_items)

        result = uuid_filler.extract(None, self.user)
        self.assertEqual(result, uuid)

    def test_not_failing_on_wrong_path(self):
        self.user.message.payload = {"other_answer": {"address": self.address}}
        result = self.payload_filler.extract(None, self.user)
        self.assertIsNone(result)

    def test_return_empty_value(self):
        self.user.message.payload = {"sf_answer": '1'}
        result = self.payload_filler.extract(None, self.user)
        self.assertEqual("", result)

    def test_filter(self):
        template = Mock()
        template.get_template = Mock(return_value=["payload.personInfo.identityCard"])
        self.user.parametrizer = MockParametrizer(self.user, {"filter": True})
        self.user.message.payload = {"personInfo": {"identityCard": "my_pass"}}
        self.user.descriptions = {"render_templates": template}
        payload_items = {'value': '{{filter}}'}
        filler = AvailableInfoFiller(payload_items)
        result = filler.extract(None, self.user)
        self.assertEqual("filter_out", result)

    def test_getting_payload_parsed_value(self):
        data = [
            {
                "id": 1,
                "surname": "Иванов",
                "name": "Иван",
                "patronimic": "Иванович",
                "tn": "1258838",
                "short_oe": "Д/О 8623/0302",
                "id_oe": "12344321",
                "count_tmc": 10,
                "actual_mol": True,
                "email": "user@omega.sbrf.ru",
                "uname": "IVANOV-II1",
                "position": "инженер"
            },
            {
                "id": 2,
                "surname": "Сидоров",
                "name": "Сидр",
                "patronimic": "Сидорович",
                "tn": "1258838",
                "short_oe": "Д/О 8623/0302",
                "id_oe": "12345678",
                "count_tmc": 5,
                "actual_mol": True,
                "email": "user@omega.sbrf.ru",
                "uname": "IVANOV-II1",
                "position": "инженер"
            },
            {
                "id": 3,
                "surname": "Петров",
                "name": "Петр",
                "patronimic": "Петрович",
                "tn": "144264",
                "short_oe": "Д/О 8623/030233",
                "id_oe": "12345678",
                "count_tmc": 5,
                "actual_mol": True,
                "email": "user@omega.sbrf.ru",
                "uname": "IVANOV-II1",
                "position": "инженер"
            }
        ]
        payload_items = {'value': '{{payload.data|tojson}}',
                         'loader': 'json'}
        payload_filler = AvailableInfoFiller(payload_items)

        self.user.message.payload = {
            "error_code": 200,
            "error_text": "OK",
            "skip": 1,
            "top": 20,
            "total_count": 125,
            "cacheGuid": "FHGDDASDHDAKSGFLAK",
            "data": data
        }
        result = payload_filler.extract(None, self.user)
        self.assertEqual(result, data)
