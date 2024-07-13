import re

import nltk

from src.core.featureextractor.DefaultResource import DefaultResource
from src.utils.logger import logger

nltk.download("stopwords")
nltk.download("wordnet")


class TokenizationMgr:
    min_token_len = 2
    max_token_len = 40

    # bound with entity Feature (token length)
    max_tokens_len = 2000

    useless_words = ["http", "www"]

    stemmer = nltk.stem.LancasterStemmer()
    lemmatizer = nltk.stem.WordNetLemmatizer()

    # TODO config???
    do_lemmating = True
    default_lemmating_speach_rule = "v"

    do_stemming = False

    specialchars = r"[“„!\"#$%&\\'()*+,-./:;<=>?@\[\]^_`{}\|~«»£—’‘…”™°]"

    def __init__(self, settings: dict):
        self.settings = settings

    def tokenize(self, value: str, lang: str) -> str:
        value = self._cleanup_and_simplify(value)

        # remove stop words like 'is' or 'von'
        value = self._tokenize_values(value, lang)
        value = value[: self.max_tokens_len]
        value = value.strip()
        return value

    def _allow_token(self, token: str):
        if (
            not token
            or len(token) <= self.min_token_len
            or len(token) > self.max_token_len
            or token.isdigit()
        ):
            return False

        # check if useless word is part of token or token is part of useless word
        if any(
            [
                token in useless_word or useless_word in token
                for useless_word in self.useless_words
            ]
        ):
            return False

        # otherwise allow token
        return True

    def _tokenize_values(self, val: str, lang: str) -> str:
        tokens = val.split(" ")

        # remove stop words
        tokens = TokenizationMgr.remove_stop_words(tokens, lang)

        if self.do_lemmating is True:
            tokens = self._lemmatization(tokens, self.default_lemmating_speach_rule)

        if self.do_stemming is True:
            tokens = self._stemming(tokens)

        # filter empty or small words
        allowed_tokens = [token for token in tokens if self._allow_token(token)]
        return " ".join(allowed_tokens)

    def _stemming(self, values):
        return [self.stemmer.stem(value) for value in values]

    def _lemmatization(self, values, speach_rule="n"):
        return [self.lemmatizer.lemmatize(value, speach_rule) for value in values]

    @staticmethod
    def remove_stop_words(values, lang):
        # usage example (will remove "von" tokens):
        try:
            stopwords = nltk.corpus.stopwords.words(lang)
        except IOError as e:
            logger.error(
                "nltk stopwords don`t support the language {}: Error: {}".format(
                    lang, str(e)
                )
            )
            stopwords = nltk.corpus.stopwords.words(DefaultResource.default_lang)

        filtered_tokens = [value for value in values if value not in stopwords]
        return filtered_tokens

    @staticmethod
    def _cleanup_and_simplify(value: str) -> str:
        """
        remove special chars and change font register to lower case

        :param value: cleaning value
        :return: cleaned value
        """
        value = TokenizationMgr.remove_special(value)
        value = TokenizationMgr.case_conversion(value)
        return value

    @staticmethod
    def case_conversion(str_val):
        return str_val.lower()

    @classmethod
    def remove_special(cls, str_val) -> str:
        """
        Change to whitespace instead just removing. because if we remove, then we create a long tokens
            which are connected together
        :param str_val: String which should be cleaned up
        :return: clean string
        """
        str_val = re.sub(cls.specialchars, " ", str_val)

        # remove multiple spaces
        str_val = re.sub(r"\s+", " ", str_val)

        # FIX: postgres issue: A string literal cannot contain NUL (0x00) characters
        str_val = str_val.replace("\x00", "")

        return str_val
