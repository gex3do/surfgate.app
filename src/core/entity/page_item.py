import json
from typing import Union


class PageItem:
    def __init__(
        self,
        link: str = None,
        json_data: Union[None, str, dict] = None,
    ):
        if json_data is not None:
            if isinstance(json_data, str):
                page_item_data = json.loads(json_data)
            elif isinstance(json_data, dict):
                page_item_data = json_data
            else:
                raise Exception(
                    "The json_data type is unknown. It should be dict or str."
                )

            self.link = page_item_data["link"]
            self.rate = page_item_data["rate"]

            # this field will be removed while giving back as a result
            self.resource_id = page_item_data["resource_id"]

            if "top_features" in page_item_data:
                if isinstance(page_item_data["top_features"], str):
                    self.top_features = json.loads(page_item_data["top_features"])
                else:
                    self.top_features = page_item_data["top_features"]

            if "pages" in page_item_data:
                self.pages = [
                    PageItem(json_data=page) for page in page_item_data["pages"]
                ]

        else:
            self.link = link

            self.rate = None

            # this field will be removed while giving back as a result
            self.resource_id = None

            self.top_features = []

            self.pages = []

    def create_pages_by_links(self, links):
        for link in links:
            self.pages.append(PageItem(link=link))

    def clean_fields(self, show_top_features=False):
        delattr(self, "resource_id")

        if not self.pages:
            delattr(self, "pages")

        if not show_top_features:
            delattr(self, "top_features")
