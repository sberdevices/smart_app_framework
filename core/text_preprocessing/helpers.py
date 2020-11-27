from core.text_preprocessing.grammem.grammem_constants import (
    IS_STOP_WORD, LEMMA, PART_OF_SPEECH, GRAMMEM_INFO, TEXT, TOKEN_TYPE, LIST_OF_DEPENDENTS, AMBIGUOUS, TENSE, MOOD,
    COMPOSITE_TOKEN_TYPE, IS_BEGINNING_OF_COMPOSITE, COMPOSITE_TOKEN_LENGTH,
    W2V_STRING, DEPENDENT_ADPOSITIONS, IMPORTANT_SURNAME_VALUE,
    IS_BEGINNING_OF_ANAPHOR, ANTECEDENT_LEMMA)
from core.text_preprocessing.constants import SENTENCE_ENDPOINT_TOKEN, ANIMACY_TOKEN


class TokenizeHelper:
    @staticmethod
    def lemma_modification(lemma: str) -> str:
        if len(lemma) > 1 and "." in lemma:
            res = lemma.strip(".")
            if "." in res:
                res = res.replace(".", "_")
        else:
            res = lemma
        return res

    @staticmethod
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

    @staticmethod
    def get_tense(token):
        result = ''
        if token.get(GRAMMEM_INFO, {}).get(PART_OF_SPEECH) == 'V':
            if AMBIGUOUS in token[GRAMMEM_INFO]:
                result = '{}_{}'.format(result, token[GRAMMEM_INFO][AMBIGUOUS][0].get(TENSE, ''))
            else:
                result = '{}_{}'.format(result, token[GRAMMEM_INFO].get(TENSE, ''))
        return result

    @staticmethod
    def get_mood(token):
        result = ''
        if token.get(GRAMMEM_INFO, {}).get(PART_OF_SPEECH) == 'V':
            if AMBIGUOUS in token[GRAMMEM_INFO]:
                result = '{}_{}'.format(result, token[GRAMMEM_INFO][AMBIGUOUS][0].get(MOOD, ''))
            else:
                result = '{}_{}'.format(result, token[GRAMMEM_INFO].get(MOOD, ''))

        return result

    @staticmethod
    def return_lemmas_only(token_desc_list: list, include_sentence_endpoint: bool = True, show_verb_mood: bool =
    False, consider_stop_words: bool = False) -> str:
        """
        Конвертировать список токенов в строку без пунктуации, содержащую леммы и замены на тип токена.
        Предложения разделяются точкой. Если перед этим нет грамматической инфо - возвращается поле токена TEXT
        :param token_desc_list: Список токенов (дикты), include_sentence_endpoint -- принтить ли фейковую точку, bool
        :return: Строка, содержащую леммы и замены на тип токена.
        """
        final_line = []
        for token in token_desc_list:
            if COMPOSITE_TOKEN_TYPE in token:
                if token[IS_BEGINNING_OF_COMPOSITE]:
                    if token.get(IMPORTANT_SURNAME_VALUE):
                        token_type = token[IMPORTANT_SURNAME_VALUE]
                    else:
                        token_type = token[COMPOSITE_TOKEN_TYPE]
                else:
                    continue
            else:
                token_type = token.get(TOKEN_TYPE)
            if token_type != SENTENCE_ENDPOINT_TOKEN:
                grammem_info = token.get(GRAMMEM_INFO)
                if grammem_info is not None:
                    pos = grammem_info.get(PART_OF_SPEECH)
                    if pos != "PUNCT":
                        if token_type is not None and token_type != ANIMACY_TOKEN:
                            final_line.append(token_type)
                        elif not token.get(IS_STOP_WORD) or (token.get(IS_STOP_WORD) and consider_stop_words):
                            lemma = TokenizeHelper.lemma_modification(token.get(LEMMA))
                            if show_verb_mood:
                                lemma = '{}{}{}'.format(lemma, TokenizeHelper.get_tense(token),
                                                        TokenizeHelper.get_mood(token))
                            final_line.append(lemma)
                else:
                    final_line.append(token[TEXT])
            elif include_sentence_endpoint:
                final_line.append(token[TEXT])
        return " ".join(final_line)

    @staticmethod
    def return_lemmas_only_from_TNR(text_normalization_result) -> str:
        """
        Конвертировать список токенов в строку без пунктуации, содержащую леммы и замены на тип токена.
        Предложения разделяются точкой
        :param text_normalization_result: TextNormalizationResult
        :return: Строка, содержащую леммы и замены на тип токена.
        """
        tokens = text_normalization_result.tokenized_elements_list
        return TokenizeHelper.return_lemmas_only(tokens)

    @staticmethod
    def num_tokens(text_normalization_result) -> int:
        """
         Вернуть количество токенов в textnormalizationresult'е за вычетом фейковых точек
         Стоп-слова при этом считаются, решили, что правильно их считать
         :param text_normalization_ result: TextNormalizationResult
         :return: Int -- количество токенов
         """
        tokens_number = 0
        for token in text_normalization_result.tokenized_elements_list:
            if COMPOSITE_TOKEN_TYPE in token:
                if token[IS_BEGINNING_OF_COMPOSITE]:
                    tokens_number += 1
            elif token.get(TOKEN_TYPE) != SENTENCE_ENDPOINT_TOKEN:
                tokens_number += 1
        return tokens_number

    @staticmethod
    def get_adpositions_from_dependents(list_of_tokens: list, token: dict, list_of_adpositions: list) -> list:
        """
         Вернуть все предлоги, зависящие от данного токеноа
         :param list_of_tokens: list, token: dict, list_of_adpositions: list
         :return: list_of_adpositions -- массив зависимых предлогов
         """
        list_of_dependent_adpositions = []
        for dependent_token_idx in token.get(LIST_OF_DEPENDENTS, []):
            dependent_token = list_of_tokens[dependent_token_idx - 1]
            dependent_lemma = dependent_token.get(LEMMA, '')
            dependent_is_part_of_hypertoken = dependent_token.get(COMPOSITE_TOKEN_TYPE, '')
            if dependent_lemma in list_of_adpositions and not dependent_is_part_of_hypertoken:
                list_of_dependent_adpositions.append(dependent_lemma)
        return list_of_dependent_adpositions

    @staticmethod
    def tokens_to_w2v(list_of_tokens: list, list_of_adpositions: list, include_sentence_endpoint: bool = True) -> list:
        """
         Вернуть упрощенный список токенов, только w2v-представление и наличие предлога
         для глаголов добавляется время и наклонение(глагол_время_наклонение)
         :param list_of_tokens: list
         :return: list_of_tokens: list
         """
        short_list = []
        composite_beginning_index = 0
        composite_dependent_adpositions = False
        for i, token in enumerate(list_of_tokens):
            string_for_w2v = ""
            dependent_adpositions = TokenizeHelper.get_adpositions_from_dependents(list_of_tokens, token,
                                                                                   list_of_adpositions)
            if COMPOSITE_TOKEN_TYPE in token:
                if token[IS_BEGINNING_OF_COMPOSITE]:
                    composite_beginning_index = i
                    has_length_one = token[COMPOSITE_TOKEN_LENGTH] == 1
                    final_dependent_adpositions = []  ##надо не потерять у гипертокенов
                    final_dependent_adpositions.extend(dependent_adpositions)
                    if not has_length_one:  ##не проскипать кейс, когда этот же токен и есть последний
                        continue
                if i - composite_beginning_index != token[COMPOSITE_TOKEN_LENGTH] - 1:  ##кладем последний токен,
                    ##когда есть только первый компонент гипертокена, мы еще не знаем всех зависимых предлогов
                    final_dependent_adpositions.extend(dependent_adpositions)
                    continue
                else:
                    final_dependent_adpositions.extend(dependent_adpositions)
                    composite_dependent_adpositions = True
                    if token.get(IMPORTANT_SURNAME_VALUE):
                        token_type = token[IMPORTANT_SURNAME_VALUE]
                    else:
                        token_type = token[COMPOSITE_TOKEN_TYPE]
            else:
                token_type = token.get(TOKEN_TYPE)
            if token_type != SENTENCE_ENDPOINT_TOKEN:
                grammem_info = token.get(GRAMMEM_INFO, {})
                pos = grammem_info.get(PART_OF_SPEECH)
                if pos != "PUNCT":
                    if token_type is not None and token_type != ANIMACY_TOKEN:
                        string_for_w2v = token_type
                    elif not token.get(IS_STOP_WORD):
                        lemma = TokenizeHelper.lemma_modification(token.get(LEMMA))
                        lemma = '{}{}{}'.format(lemma, TokenizeHelper.get_tense(token), TokenizeHelper.get_mood(token))
                        string_for_w2v = lemma
            elif include_sentence_endpoint:
                string_for_w2v = token[TEXT]
            if composite_dependent_adpositions:
                composite_dependent_adpositions = False
                final_token = {W2V_STRING: string_for_w2v, DEPENDENT_ADPOSITIONS: final_dependent_adpositions}
                short_list.append(final_token)
            elif string_for_w2v:
                final_token = {W2V_STRING: string_for_w2v, DEPENDENT_ADPOSITIONS: dependent_adpositions}
                short_list.append(final_token)
        return short_list

    @staticmethod
    def return_indices_of_the_dependents(list_of_tokens: list, index: int) -> list:
        """
         Вернуть индексы зависимых от токена, где токен представлен индексом
         :param list_of_tokens: list, index: int
         :return: list_of_dependent_indices: list of ints
         """
        converted_elem = list_of_tokens[index]
        preliminary_list = converted_elem.get(LIST_OF_DEPENDENTS, [])
        list_of_dependent_indices = [index - 1 for index in preliminary_list]
        return list_of_dependent_indices

    @staticmethod
    def get_human_normalized_text(list_of_tokens: list):
        return " ".join([t[LEMMA] for t in list_of_tokens if t.get(TOKEN_TYPE) != SENTENCE_ENDPOINT_TOKEN
                         and LEMMA in t])

    @staticmethod
    def get_human_normalized_text_with_anaphora(list_of_tokens: list):
        list_of_lemmas = []
        for t in list_of_tokens:
            if t.get(IS_BEGINNING_OF_ANAPHOR):
                list_of_lemmas.append(t[ANTECEDENT_LEMMA])
            elif t.get(IS_BEGINNING_OF_ANAPHOR) == False:
                continue
            elif t.get(TOKEN_TYPE) != SENTENCE_ENDPOINT_TOKEN:
                list_of_lemmas.append(t[LEMMA])
        return " ".join(list_of_lemmas)
