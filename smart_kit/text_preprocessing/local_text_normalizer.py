from typing import List, Sequence

import nltk
from rusenttokenize import ru_sent_tokenize

from core.repositories.file_repository import FileRepository
from core.utils.loader import ordered_json

from smart_kit.text_preprocessing.base_text_normalizer import BaseTextNormalizer
from smart_kit.text_preprocessing.nltk_tokenizer_binding import NLTKWordTokenizer
from smart_kit.text_preprocessing.rnnmorph_wrapper import RNNMorphWrapper
from smart_kit.text_preprocessing.text2num import Text2Num, NumbersUnionAfterSTT
from smart_kit.text_preprocessing.utils import replace_yo_to_e, unmerge_numbers_and_letters, merge_numbers, \
    replace_currencies_symbols, AdditionalMathSplitter, MergeCardNumbersVoice, MergeCardNumbers, \
    NormalizePhoneNumbersVoice, NormalizePhoneNumbers, UnicodeSymbolsConverter, ReplaceSynonyms, \
    CurrencyTokensOneIterationMerger, reverse_json_dict, return_lemmas_only, Singleton


class LocalTextNormalizer(BaseTextNormalizer, metaclass=Singleton):
    """
    Упрощённая предобработка, соответствующая первым шагам платформенной
    Разбиение на слова, замена числительных и валют, морфология. Извлечение сущностей отсутствует
    При вызове нужно передавать параметр message_type="voice" или ="text" - для голоса и текста разный пайплайн
    """

    def __init__(self):
        self.__ready_to_use = False

    def get_token_list(self, text):
        sentences = self.sentence_tokenizer(text.strip())
        words = self.word_tokenizer(sentences)
        return words

    def __load_everything(self):
        nltk.download('punkt')

        from smart_kit.configs import get_app_config
        app_config = get_app_config()
        text_normalizer_params = FileRepository(
            f"{app_config.STATIC_PATH}/.text_normalizer_resources/static_workdata.json",
            loader=ordered_json,
        )
        text_normalizer_params.load()

        synonyms = FileRepository(
            f"{app_config.STATIC_PATH}/.text_normalizer_resources/dict_synonyms.json",
            loader=reverse_json_dict,
        )
        synonyms.load()
        text_normalizer_params.data["synonyms"] = synonyms.data

        text2num_dict = FileRepository(
            f"{app_config.STATIC_PATH}/.text_normalizer_resources/text2num_dict.json",
            loader=ordered_json,
        )
        text2num_dict.load()
        text_normalizer_params.data["text2num_dict"] = text2num_dict.data

        text_normalizer_params = text_normalizer_params.data or {}
        self.convert_plan = text_normalizer_params["convert_plan"]
        self.processor_pipeline = text_normalizer_params["processor_pipeline"]

        word_false_stoppings = text_normalizer_params.get("word_false_stoppings", [])
        words_without_splitting_point = text_normalizer_params.get("word_no_splitting_point", [])
        synonyms = text_normalizer_params.get("synonyms", {})
        text2num = text_normalizer_params.get("text2num_dict", {})
        sberbank_phones = text_normalizer_params.get("sberbank_phones", [])
        unicode_symbols = text_normalizer_params.get("unicode_symbols", {})

        self.sentence_tokenizer = ru_sent_tokenize
        self.word_tokenizer = NLTKWordTokenizer(word_false_stoppings, words_without_splitting_point)
        self.morph = RNNMorphWrapper()

        skip_func = lambda x: x
        self.converter_pipeline = {
            'Объединение цифр после stt': NumbersUnionAfterSTT(text2num),
            'Конверсия юникодовых символов': UnicodeSymbolsConverter(unicode_symbols),
            'Цифры и буквы отдельно': unmerge_numbers_and_letters,
            'Ё на Е': replace_yo_to_e,
            'Номера телефонов': NormalizePhoneNumbers(),
            'Номера телефонов из голоса': NormalizePhoneNumbersVoice(),
            'Номера карт': MergeCardNumbers(),
            'Номера карт из голоса': MergeCardNumbersVoice(),
            'Объединение сумм': merge_numbers,
            'Символы валют': replace_currencies_symbols,
            "Претокенизация математических операций": AdditionalMathSplitter()
        }
        self.tokens_processor = {
            "Synonyms": ReplaceSynonyms(synonyms) if synonyms else skip_func,
            "Text2Num": Text2Num(text2num, sberbank_phones) if text2num else skip_func,
            "Currency": CurrencyTokensOneIterationMerger(),
            "Grammemes": self.morph,
        }

        self.__ready_to_use = True

    def load_everything(self):
        if not self.__ready_to_use:
            self.__load_everything()

    def __call__(self, text, message_type="voice"):
        self.load_everything()
        normalized_text = text
        convert_processor = self.convert_plan[message_type]
        for converter_name in convert_processor:
            converter = self.converter_pipeline[converter_name]
            normalized_text = converter(normalized_text)
        token_list = self.get_token_list(text)
        for converter_step in self.processor_pipeline:
            converter_name = converter_step["name"]
            converter = self.tokens_processor[converter_name]
            token_list = converter(token_list)
        return {
            "original_text": text,
            "normalized_text": return_lemmas_only(token_list),
            "tokenized_elements_list": token_list
        }

    @classmethod
    def with_cache(cls, app_config, **kwargs):
        return cls()

    def normalize_sequence(self, texts: Sequence, batch_size=None) -> List:
        normalized_texts = []
        for text in texts:
            normalized_texts.append(self(text))
        return normalized_texts
