import os
import requests
import json

'''
пример bundles.json

{
  "bundle_name": {
    "key.male_to_male": "Ты любил меня, а я тебя ненавидел",
    "key.male_to_female": "Ты любила меня, а я тебя ненавидел",
    "key.female_to_male": "Ты любил меня, а я тебя ненавидела",
    "key.female_to_female": "Ты любила меня, а я тебя ненавидела"
  }
}

пример scenarios.json с использовнаием bundle-ов

{
  "scenario_name": {
    "actions": [
      {
        "nodes": {
          "answer": [
            [
              "{{ gender_sensetive_text(bundle_name, key) }}"
            ]
          ]
        }
      }
    ]
  }
}

'''


class GetBundleCommand:
    def __init__(self, app_config):
        static_path = app_config.STATIC_PATH
        self.url = app_config.PPS_URL
        self.bundle_path = os.path.join(static_path, "references/bundles")
        self.file_path = os.path.join(self.bundle_path, "bundles.json")

    @staticmethod
    def get_default_items(text, key, bundle_name):
        return {
            bundle_name: {
                key: text
            }
        }

    @staticmethod
    def get_data(text, key, bundle_name):
        return json.dumps(
            {
                "payload": {
                    "items_to_pps": {
                        bundle_name: {
                            "type": "text",
                            "key": key,
                            "text": text,
                            "params": {}
                        }
                    }
                }
            }
        )

    def execute(self):
        print("insert text")
        text = input(">")
        print("insert key")
        key = input(">")
        print("insert bundle_name")
        bundle_name = input(">")
        if text and key and bundle_name:
            data = self.get_data(text, key, bundle_name)
            try:
                r = requests.post(url=self.url, data=data)
                if r.status_code == 200:
                    data = json.loads(r.content)
                    payload = data.get("payload")
                    items_from_pps = payload.get("items_from_pps")
                else:
                    items_from_pps = self.get_default_items(text, key, bundle_name)
            except:
                items_from_pps = self.get_default_items(text, key, bundle_name)
            if items_from_pps:
                if not os.path.exists(self.bundle_path):
                    os.makedirs(self.bundle_path)
                if os.path.exists(self.file_path):
                    with open(self.file_path, "r") as json_file:
                        file_data = json.load(json_file)
                        file_data.update(items_from_pps)
                else:
                    file_data = items_from_pps

                with open(self.file_path, "w") as json_file:
                    json.dump(file_data, json_file, ensure_ascii=False)
