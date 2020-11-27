import re
import pymorphy2
import tensorflow as tf
from rnnmorph.predictor import RNNMorphPredictor
from core.text_preprocessing.grammem.grammem_constants import GRAMMEM_INFO, PART_OF_SPEECH, LEMMA, TEXT, TOKEN_TYPE, \
    LIST_OF_TOKEN_TYPES_DATA, TOKEN_VALUE, VALUE, RAW_GRAM_INFO, OTHER, TRANSITIVITY, ANIMACY, ASPECT

SENTENCE_ENDPOINT_TOKEN = "SENTENCE_ENDPOINT_TOKEN"


def token_list_to_sentences(token_desc_list: list) -> list:
    """
    Разбить список токенов на предложения
    :param token_desc_list: список токенов
    :return: Список из списков, где первый список содержит предложения, а второй токены
    """
    results = []
    k = 0
    more_than_one_sentence = False
    for i, token in enumerate(token_desc_list):
        if token.get(TOKEN_TYPE) == SENTENCE_ENDPOINT_TOKEN:
            more_than_one_sentence = True
            results.append(token_desc_list[k:i])
            k = i + 1
    if not more_than_one_sentence:
        results = [token_desc_list]
    return results


class RNNMorphWrapper:
    """
    Класс предназначен для получения граммемной информации о токенах.
    """

    def __init__(self):
        self._graph = tf.Graph()
        self._session = tf.Session(graph=self._graph)
        with self._session.as_default():
            with self._graph.as_default():
                self.rnnmorph = RNNMorphPredictor(language="ru")
        self.pymorphy_analyzer = pymorphy2.MorphAnalyzer()
        self.latin = re.compile("^[0-9]*[A-Za-z]+[0-9]*$")
        self.cyrillic = re.compile("[А-Яа-яЁе]+")

    def _choose_pymorphy_form(self, word, lemma, pos):
        hypotheses = self.pymorphy_analyzer.parse(word)
        hyp = None
        tags_to_add = {}
        other = ""
        for hyp in hypotheses:
            if hyp.normal_form == lemma:
                break
        changed_lemma = lemma.replace("ё", "е")
        if not hyp:
            return other, tags_to_add, changed_lemma
        str_tag = str(hyp.tag)
        if "Surn" in str_tag:
            other = "фам"
            changed_lemma = word.lower().replace("ё", "е")
        elif "Patr" in str_tag:
            other = "отч"
            changed_lemma = word.lower().replace("ё", "е")  # у Петрович лемма внезапно Пётр
        if hyp.tag.transitivity:
            tags_to_add[TRANSITIVITY] = str(hyp.tag.transitivity)
        if hyp.tag.animacy and pos == "NOUN":
            tags_to_add[ANIMACY] = str(hyp.tag.animacy)
        if hyp.tag.aspect:
            tags_to_add[ASPECT] = str(hyp.tag.aspect)
        return other, tags_to_add, changed_lemma

    def _change_pos(self, token, analysis):
        if re.match(self.latin, analysis.word):
            token[GRAMMEM_INFO][PART_OF_SPEECH] = "X"
        elif analysis.pos == "PUNCT" and re.search(self.cyrillic, analysis.word):
            token[GRAMMEM_INFO][PART_OF_SPEECH] = "X"
        else:
            token[GRAMMEM_INFO][PART_OF_SPEECH] = analysis.pos
        return token

    def _gram_info_processing(self, tags_to_add, analysis):
        gramme_info = {}
        raw_gram_data = []
        if analysis.tag != "_":
            for tag in analysis.tag.split("|"):
                gramme_info[tag.split("=")[0].lower()] = tag.split("=")[1].lower()
            gramme_info.update(tags_to_add)
        sorted_gramme_info = {key: gramme_info[key] for key in sorted(gramme_info.keys())}
        for key in sorted_gramme_info:
            raw_gram_data.append(key + "=" + sorted_gramme_info[key])
        raw_gram_info = "|".join(raw_gram_data)
        return sorted_gramme_info, raw_gram_info

    def _rnnmorph_to_token_dicti(self, token, analysis):
        additional_info, tags_to_add, changed_lemma = self._choose_pymorphy_form(analysis.word, analysis.normal_form,
                                                                                 analysis.pos)
        sorted_gramme_info, raw_gram_info = self._gram_info_processing(tags_to_add, analysis)
        token[GRAMMEM_INFO] = sorted_gramme_info
        token[GRAMMEM_INFO][RAW_GRAM_INFO] = raw_gram_info
        if additional_info:
            token[GRAMMEM_INFO][OTHER] = additional_info
        token = self._change_pos(token, analysis)
        token[LEMMA] = changed_lemma
        return token

    def token_desc_list_processing(self, token_desc_list):
        """
        Получить список токенов с описанием
        :param: Список из словарей
        :return: Список из словарей, обогащенный морфологической информацией
        """
        raw_token_list = [token[TEXT] for token in token_desc_list]
        with self._session.as_default():
            with self._graph.as_default():
                analyze_result = self.rnnmorph.predict(raw_token_list)

        res = []
        for i in range(len(token_desc_list)):
            analysis = analyze_result[i]
            tokenized_element = token_desc_list[i]
            final_tokenized_element = self._rnnmorph_to_token_dicti(tokenized_element, analysis)
            res.append(final_tokenized_element)
        return res

    def __call__(self, token_desc_list):
        """
        Класс предназначен для забора из RNNMorph + pymorphy2 граммемной информации.
        На вход принимается список токенов
        На выходе имеем список токенов с проставленными грамматическими атрибутами

        :param token_desc_list (list of dicts)
        :return: final_result (enriched list of dicts)
        """
        final_result = []
        sentences = token_list_to_sentences(token_desc_list)
        for sentence in sentences:
            final_result.extend(self.token_desc_list_processing(sentence))
            if final_result:
                final_result.append({TEXT: ".", LEMMA: ".", TOKEN_TYPE: SENTENCE_ENDPOINT_TOKEN,
                                     TOKEN_VALUE: {VALUE: "."},
                                     LIST_OF_TOKEN_TYPES_DATA:
                                         [{TOKEN_TYPE: SENTENCE_ENDPOINT_TOKEN, TOKEN_VALUE: {VALUE: "."}}]
                                     })
        return final_result
