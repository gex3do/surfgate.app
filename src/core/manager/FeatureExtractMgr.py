import http
import os
import typing
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.core import debug_log_entry_exit
from src.core.AppEnum import ResourceStatus, ResourceType
from src.core.entity.Feature import Feature
from src.core.entity.Resource import Resource
from src.core.featureextractor.DefaultResource import DefaultResource
from src.core.featureextractor.YoutubeResource import YoutubeResource
from src.core.helper.url import get_domain_name_from_url
from src.core.manager import TokenizationMgr
from src.core.webscrapper import parse
from src.core.webscrapper.RequestsScrapper import RequestsScrapper
from src.core.webscrapper.WebDriveScrapper import WebDriveScrapper
from src.utils.logger import logger

"""
- features are [headers, meta, title] of document (page)
- tokens are extracted from features
- features can be text sentences, and tokens are 'words' which are joined after cleanup together
"""

fetchers = [
    {
        "name": "RequestsScrapper",
        "fetch": RequestsScrapper().fetch,
    },
    {
        "name": "WebDriveScrapper",
        "fetch": WebDriveScrapper().fetch,
    },
]


class FeatureExtractMgr:
    data_path_dir: typing.Final[str] = "data"

    def __init__(
        self,
        settings: dict,
        token_mgr: TokenizationMgr,
    ):
        self.settings = settings
        self.token_mgr = token_mgr

    @staticmethod
    @debug_log_entry_exit(__name__)
    def delete_features_by_resource_id(sess: Session, res_id: int) -> None:
        sess.query(Feature).filter_by(resource_id=res_id).delete()
        sess.flush()

    @debug_log_entry_exit(__name__)
    def extract(self, sess: Session, res: Resource) -> Resource:
        self.delete_features_by_resource_id(sess, res.id)

        # set status to 'extracting' to avoid race-conditions
        res.status = ResourceStatus.EXTRACTING
        sess.flush()

        if res.type == ResourceType.TEXT:
            self._txt_to_keywords(sess, res)
        elif res.type == ResourceType.URL:
            self._url_to_keywords(sess, res)
        elif res.type == ResourceType.FILE:
            self._file_to_keywords(sess, res)
        else:
            logger.error("Unknown type of resource %s", res.type)
            raise NotImplementedError

        sess.flush()
        return res

    @debug_log_entry_exit(__name__)
    def _txt_to_keywords(self, sess: Session, res: Resource) -> None:
        if tokenized := self.token_mgr.tokenize(res.value, res.lang):
            self.add_feature(sess, res, tokenized)

        self._set_resource_status(res, ResourceStatus.EXTRACTED)

    @debug_log_entry_exit(__name__)
    def _file_to_keywords(self, sess, res: Resource) -> None:
        file = os.sep.join([self.data_path_dir, res.value])
        file_path = Path(file)

        if file_path.is_file():
            with open(file, "r") as f:
                if tokenized := self.token_mgr.tokenize(f.read(), res.lang):
                    self.add_feature(sess, res, tokenized)
            self._set_resource_status(res, ResourceStatus.EXTRACTED)
        else:
            self._set_resource_status(
                res,
                ResourceStatus.DECLINED,
                http.HTTPStatus.NOT_FOUND,
                "File not exists",
            )

    @debug_log_entry_exit(__name__)
    def _url_to_keywords(self, sess: Session, res: Resource) -> None:
        res_features = None
        for fetcher in fetchers:
            res_features = self.get_features(res, fetcher["fetch"])
            if res.status == ResourceStatus.DECLINED:
                return

            if res_features:
                logger.info("features are extracted by %s", fetcher["name"])
                break

        if res_features is None or len(res_features) == 0:
            self._set_resource_status(
                res,
                ResourceStatus.DECLINED,
                http.HTTPStatus.INTERNAL_SERVER_ERROR,
                f"There are no features extracted for this resource {res.value}",
            )
            return

        for feature in res_features:
            if tokenized := self.token_mgr.tokenize(feature, res.lang):
                self.add_feature(sess, res, tokenized)

        self._set_resource_status(res, ResourceStatus.EXTRACTED)

    @staticmethod
    def _set_resource_status(
        res: Resource,
        status: ResourceStatus,
        code: http.HTTPStatus | int = None,
        msg: str = "",
    ) -> None:
        res.status = status
        res.status_reason_code = code
        res.status_reason_msg = msg

    def get_features(self, res: Resource, fetch: typing.Callable) -> list | None:
        try:
            logger.info("start parsing resource: %s", res.value)
            content = parse(res.value, fetch)
            logger.info("end parsing resource: %s", res.value)
        except HTTPException as e:
            self._set_resource_status(
                res, ResourceStatus.DECLINED, e.status_code, e.detail
            )
            logger.info("end parsing resource: %s with an error %s", res.value, str(e))
            return None

        feature_extractor = self.get_feature_extractor(res.value)

        if res.lang is None:
            res.lang = feature_extractor.get_lang_from_content(content)

        # collect important features (array) as string values
        # if it`s webpage, it is parsed (title, body, h1 etc. and we take strings of these tags
        # and pack them as features.
        features = feature_extractor.collect_features(content)

        return features

    @staticmethod
    @debug_log_entry_exit(__name__)
    def add_feature(sess: Session, res: Resource, token: str) -> None:
        feature = Feature(resource_id=res.id, token=token)
        sess.add(feature)

    @staticmethod
    @debug_log_entry_exit(__name__)
    def get_feature_extractor(url: str) -> DefaultResource | YoutubeResource:
        domain_name = get_domain_name_from_url(url)
        if "youtube." in domain_name or "youtub." in domain_name:
            return YoutubeResource()

        return DefaultResource()
