import random
from typing import Dict, Any
from core.model.base_user import BaseUser as User


class ReplySelector:
    __gender_male = ["1", "male", "м"]

    def get_user_gender(self) -> str:
        if self._user_gender.lower() in self.__gender_male:
            return "male"
        else:
            return "female"

    def __init__(self, items: Dict[str, Any], user: User):
        self._bundles: dict = user.descriptions["bundles"]
        self._user_gender: str = str(user.message.payload.get("client_profile", {}).get("gender") or "")
        self.user_gender: str = self.get_user_gender()
        self.character_gender: str = str(user.message.payload.get("character", {}).get("gender") or "")
        self.character_key: str = str(user.message.payload.get("character", {}).get("name") or "")
        self.__suffix = [
            f".{self.character_key}.{self.character_gender}_to_{self.user_gender}",
            f".{self.character_gender}_to_{self.user_gender}",
            f".{self.character_key}.{self.user_gender}",
            f".{self.character_key}",
            ""
        ]

    def get_text_by_key(self, bundle_name: str, reply_key="") -> str:
        result = ""
        bundle = self._bundles[bundle_name]
        if bundle:
            reply_list = None
            for suffix in self.__suffix:
                target_key = f"{reply_key}{suffix}"
                reply_list = bundle.get(target_key)
                if reply_list:
                    break
            if reply_list:
                result = random.choice(reply_list)
            else:
                raise KeyError("Key not found")
        return result

    @property
    def raw(self) -> None:
        return None
