import re
from nltk import word_tokenize
from core.text_preprocessing.grammem.grammem_constants import TOKEN_TYPE, TEXT
from .utils import DateConverter

SENTENCE_ENDPOINT_TOKEN = "SENTENCE_ENDPOINT_TOKEN"


class NLTKWordTokenizer:
    URL = re.compile(
        "(?:(?:https?|ftp)://)?(?:www)?[a-zA-Zа-яА-Я0-9_-]+(?:\\.[a-zA-Zа-яА-Я0-9_-]+)?\\.(?:com|ru|рф|org|bz|ua|ge|by|mp|net|cn)(?:/[a-zA-Zа-яА-Я0-9_\\-\\#\\&\\=\\?\\(\\)]+)*(?:\\.html|\\.xml)?/?")
    MAIL = re.compile(r"[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}")
    SPACES = re.compile("^\s+$")
    QUASIPUNCT = "=…№-——'"
    DATE_CHECKER = DateConverter()

    def __init__(self, stoppings_list, black_list):
        self.false_stoppings = stoppings_list
        self.black_list = black_list

    def url_mail_fix(self, text):
        urls = re.findall(NLTKWordTokenizer.URL, text)
        mails = re.findall(NLTKWordTokenizer.MAIL, text)
        hard_tokens = mails + urls
        return hard_tokens

    def _non_last_removal(self, cnt, tokens, bad_token, token):
        to_return = 0
        length = len(tokens)
        if cnt == length - 1:
            to_return = 2
        elif cnt < length - 1:
            next_token = tokens[cnt + 1]
            if next_token in bad_token and next_token not in bad_token[:len(token)]:
                to_return = 1
            else:
                to_return = 0
        return to_return

    def _tokens_resolution(self, list_of_tokens, list_of_urls_mails, dicti, final_tokens, flag_to_append):
        final_token = ""
        for i, token in enumerate(list_of_tokens):
            flag_not_change = False
            if not flag_to_append:
                for hard in list_of_urls_mails:
                    if token == hard[:len(token)] and dicti[hard] == 0:
                        dicti[hard] = 1
                        flag_to_append = True
                        flag_not_change = True
                        final_token = token
                        if i == len(list_of_tokens) - 1:
                            final_tokens.append(token)
                        break
                if not flag_not_change:
                    final_tokens.append(token)
            elif flag_to_append:
                if token in hard and token not in hard[:len(token)]:  # для отсечки дополнительных https://
                    final_token += token
                    returned = self._non_last_removal(i, list_of_tokens, hard, token)
                    if returned == 2:
                        final_tokens.append(final_token)
                    elif returned == 1:
                        continue
                    else:
                        flag_to_append = False
                        final_tokens.append(final_token)
                else:
                    flag_to_append = False
                    final_tokens.append(final_token)
        return final_tokens

    def web_postprocessing(self, text, all_tokens):
        url_mails = self.url_mail_fix(text)
        if len(url_mails) > 0:
            dicti = {key: 0 for key in url_mails}
            final_tokens = self._tokens_resolution(all_tokens, url_mails, dicti, [], False)
            return final_tokens
        return all_tokens

    def endwise_removal(self, token):
        i = len(token) - 1
        buffer = []
        while token[i] in NLTKWordTokenizer.QUASIPUNCT:
            buffer.insert(0, token[i])
            i -= 1
        return buffer

    def _quasipunct_removal(self, token, new_token, future_tokens):
        if len(new_token) != 0:
            i = 0
            while token[i] in NLTKWordTokenizer.QUASIPUNCT:
                future_tokens.append({TEXT: token[i]})
                i += 1
            else:
                future_tokens.append({TEXT: new_token})
                buffer = self.endwise_removal(token)
                for elem in buffer:
                    future_tokens.append({TEXT: elem})
        else:
            if token == "''" or token == '``':
                future_tokens.append({TEXT: '"'})
            else:
                future_tokens.append({TEXT: token})
        return future_tokens

    def _slash_splitting(self, token):
        is_url = re.search(NLTKWordTokenizer.URL, token)
        is_date = NLTKWordTokenizer.DATE_CHECKER(token) is not None
        if "/" in token and not is_date and not is_url:
            tokens = []
            split_tokens = token.split("/")
            for i, elem in enumerate(split_tokens):
                if elem:
                    tokens.append({TEXT: elem})
                    if i != len(split_tokens) - 1:
                        tokens.append({TEXT: "/"})
        elif "\\" in token and not is_date and not is_url:
            tokens = [{TEXT: elem} for elem in token.split("\\") if elem]
        else:
            tokens = [{TEXT: token}]
        return tokens

    def punct_postprocessing(self, arr_of_tokens):
        final_tokens = []
        skip = False
        for i, token in enumerate(arr_of_tokens):
            new_token = token.strip(NLTKWordTokenizer.QUASIPUNCT)
            if skip:
                skip = False
            elif len(new_token) != len(token):
                final_tokens = self._quasipunct_removal(token, new_token, final_tokens)
            elif len(token) == 0:
                continue
            elif re.match("\s+", token):
                continue
            elif "/" in token or "\\" in token:
                if token == "/":
                    final_tokens.append({TEXT: "/"})
                else:
                    final_tokens.extend(self._slash_splitting(token))
            elif token == '``':
                final_tokens.append({TEXT: '"'})
            elif token == "''":
                final_tokens.append({TEXT: '"'})
            elif token == "..":
                final_tokens.append({TEXT: "."})
                final_tokens.append({TEXT: "."})
            elif len(arr_of_tokens) > i + 1 and token in self.false_stoppings and arr_of_tokens[
                i + 1] == ".":
                final_tokens.append({TEXT: token + "."})
                skip = True
            elif "." in token and len(token) == 3 and len(arr_of_tokens) > i + 1 and arr_of_tokens[i + 1] == ".":
                final_tokens.append({TEXT: token + "."})
                skip = True
            else:
                final_tokens.append({TEXT: token})
        return final_tokens

    def _preprocess_check(self, token):
        final_list = []
        if not re.match(NLTKWordTokenizer.SPACES, token):
            token = token.strip()
        if "." in token:
            if re.search(NLTKWordTokenizer.MAIL, token):
                final_list.append(token + " ")
            elif re.search(NLTKWordTokenizer.URL, token):
                final_list.append(token + " ")
            elif re.match(NLTKWordTokenizer.DATE_CHECKER.regex, token):
                match_result = re.match(NLTKWordTokenizer.DATE_CHECKER.regex, token)
                result = match_result.group(0)
                finish = match_result.end()
                final_list.append(result + " ")
                final_list.append(token[finish:] + " ")
            else:
                mask_token = token.lower().replace(".", "")
                if mask_token.isdigit():
                    final_list.append(token + " ")
                elif mask_token in self.black_list:
                    final_list.append(token + " ")
                else:
                    new_tokens = token.split(".")
                    for new_token in new_tokens[:-1]:
                        new_string = new_token + ". "
                        final_list.append(new_string)
                    final_list.append(new_tokens[-1] + " ")
        else:
            final_list.append(token + " ")
        return "".join(final_list)

    def preprocess(self, sentence):
        final_list = []
        if " " in sentence:
            for token in sentence.split(" "):
                final_list.append(self._preprocess_check(token))
        else:
            final_list.append(self._preprocess_check(sentence))
        return "".join(final_list).strip()

    def _merge_hashtags(self, tokens):
        '''
        слепляем токен '#' с идущим за ним
        :param tokens: list of strings
        :return: list of strings
        '''
        merged_tokens = []
        i = 0
        while i < len(tokens):
            if tokens[i] == '#' and i + 1 < len(tokens):
                merged_tokens.append(tokens[i] + tokens[i + 1])
                i += 2
            else:
                merged_tokens.append(tokens[i])
                i += 1

        return merged_tokens

    def __call__(self, list_of_texts):
        """
        Класс предназначен для токенизации (т.е. разбиения на "слова" предложений).
        На вход принимается список предложений (строк)
        На выходе имеем список словарей, в котором в том месте, где была граница между предложениями,
        стоит специальная синтетическая точка с типом токена SENTENCE_ENDPOINT_TOKEN

        :param list_of_texts (list of strings)
        :return: final_list (list of dicts)
        """
        final_list = []
        for text in list_of_texts:
            text = self.preprocess(text)
            preliminary_tokens = word_tokenize(text)
            preliminary_tokens = self._merge_hashtags(preliminary_tokens)
            final_arr = self.web_postprocessing(text, preliminary_tokens)
            post_arr = self.punct_postprocessing(final_arr)
            final_list.extend(post_arr)
            final_list.append({TEXT: ".", TOKEN_TYPE: SENTENCE_ENDPOINT_TOKEN})
        return final_list
