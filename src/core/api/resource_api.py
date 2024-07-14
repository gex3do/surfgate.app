from http import HTTPStatus

from sqlalchemy.orm.session import Session

from src.core.api.responser import Responser
from src.core.app_error import AppError
from src.core.entity.resource import Resource
from src.core.helper import normalizer
from src.core.manager.key_mgr import KeyMgr
from src.core.manager.resource_mgr import ResourceMgr
from src.core.model.resource import (
    ResourcePredictGetIn,
    ResourcePredictGetOrRateOut,
    ResourcePredictRateIn,
)


class ResourceApi:
    def __init__(self, settings: dict, resource_mgr: ResourceMgr, key_mgr: KeyMgr):
        self.settings = settings
        self.resource_mgr = resource_mgr
        self.key_mgr = key_mgr

    def get_resource_rate_else_predict(
        self, sess: Session, data: ResourcePredictRateIn
    ) -> (ResourcePredictGetOrRateOut, HTTPStatus):
        data = normalizer.resource(data)

        # create a resource placeholder with predefined data
        # and fill out it in next steps
        resource = Resource(value=data.value, type=data.type, lang=data.lang)

        # if recheck is true, then start prediction of the resource again, instead of getting already predicted PVR
        requested_resource = self.resource_mgr.get_and_predict(
            sess, resource, data.recheck, data.top_features
        )

        if not requested_resource:
            raise AppError.resource_not_found()

        if self.resource_mgr.is_declined(requested_resource):
            raise AppError.resource_declined()

        response = Responser.create_resource_rate_status(
            requested_resource, data.top_features
        )
        return response

    def get_resource_rate(
        self, sess: Session, data: ResourcePredictGetIn
    ) -> (ResourcePredictGetOrRateOut, HTTPStatus):
        data = normalizer.resource(data)

        resource = Resource(value=data.value, type=data.type)
        requested_resource = self.resource_mgr.get(sess, resource)

        if not requested_resource:
            raise AppError.resource_not_found()

        if self.resource_mgr.is_declined(requested_resource):
            raise AppError.resource_declined()

        return Responser.create_resource_rate_status(
            requested_resource, data.top_features
        )
