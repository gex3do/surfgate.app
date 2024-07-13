from bs4 import BeautifulSoup

from src.core.model.resource import Lang


class DefaultResource:
    lang_codes = {
        "nl": "dutch",
        "fi": "finnish",
        "de": "german",
        "it": "italian",
        "pt": "portuguese",
        "es": "spanish",
        "tr": "turkish",
        "da": "danish",
        "en": "english",
        "fr": "french",
        "hu": "hungarian",
        "nb": "norwegian",
        "ru": "russian",
        "sv": "swedish",
    }

    default_lang = Lang.english

    limit_ahref = 300
    skip_ahref = 1

    def __init__(self):
        self.resource_features = []

    def collect_features(self, content: BeautifulSoup) -> list:
        for feature in self.get_title(content):
            self.resource_features.append(feature)

        for feature in self.get_meta(content):
            self.resource_features.append(feature)

        for feature in self.get_headers(content):
            self.resource_features.append(feature)

        for feature in self.get_ahrefs(content):
            self.resource_features.append(feature)

        return self.resource_features

    def get_lang_from_content(self, content: BeautifulSoup) -> str:
        # first check head tag
        lang = None
        checked_lang = None
        element = content.find("html")

        if element and element.get("lang"):
            lang = element.get("lang")
        else:
            # continue finding language
            elements = content.find_all("meta")

            if elements:
                for element in elements:
                    if (
                        element.get("property")
                        and element.get("property") == "og:locale"
                    ):
                        lang = element.get("content")
                        break

        if lang:
            if lang.find("_") != -1:
                lang = lang.split("_")[0]
            elif content.find("-") != -1:
                lang = lang.split("-")[0]

            if lang in self.lang_codes.keys():
                checked_lang = self.lang_codes[lang]

        return checked_lang if checked_lang else self.default_lang

    @staticmethod
    def get_title(content: BeautifulSoup) -> list:
        if elements := content.find_all("title"):
            return [elements[0].get_text()]
        return []

    @staticmethod
    def get_meta(content: BeautifulSoup) -> list:
        features = []

        important_metas_name = ["description", "keywords"]
        important_metas_properties = ["og:description", "og:title"]

        elements = content.find_all("meta")

        if elements:
            for element in elements:
                if (
                    element.get("name") is not None
                    and element.get("name") in important_metas_name
                ):
                    content = element.get("content")
                    if content:
                        features.append(content)

                if (
                    element.get("property") is not None
                    and element.get("property") in important_metas_properties
                ):
                    content = element.get("content")
                    if content:
                        features.append(content)

        return features

    @staticmethod
    def get_headers(content: BeautifulSoup) -> list:
        features = []

        for num in range(1, 4):
            elements = content.find_all("h" + str(num))
            # TODO should be checked
            features += [element.get_text() for element in elements if element]

        return features

    @classmethod
    def get_ahrefs(cls, content: BeautifulSoup) -> list:
        elements = content.find_all("a")

        ahrefs = [
            element.text
            for element in elements
            if element.text and element.text.strip()
        ]

        if not ahrefs:
            return []

        ahrefs = ahrefs[: cls.limit_ahref]
        return [" ".join(ahrefs)]
