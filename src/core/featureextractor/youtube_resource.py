from bs4 import BeautifulSoup

from src.core.featureextractor.default_resource import DefaultResource


class YoutubeResource(DefaultResource):
    def __init__(self):
        super().__init__()

    def collect_features(self, content: BeautifulSoup) -> list | None:
        super().collect_features(content)
        # [self.resource_features.append(feature) for feature in self.get_video_desc(content)]
        return self.resource_features

    @staticmethod
    def get_video_desc(content):
        features = []

        elements = content.find_all(id="meta-contents")

        [features.append(element.get_text()) for element in elements if element]

        return features
