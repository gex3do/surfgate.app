import http
import json
import os
from pathlib import Path
from typing import Any, Type

from sqlalchemy import or_
from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session

from src.core import debug_log_entry_exit
from src.core.AppEnum import ResourceStatus, ResourceType
from src.core.AppError import AppError
from src.core.entity.Resource import Resource
from src.core.helper import url
from src.core.manager.DomainQueryMgr import DomainQueryMgr
from src.core.manager.FeatureExtractMgr import FeatureExtractMgr
from src.core.model.resource import Lang
from src.utils.logger import logger


class ResourceMgr:

    def __init__(
        self,
        settings: dict,
        feature_extract_mgr: FeatureExtractMgr,
        domainquery_mgr: DomainQueryMgr,
    ):
        self.settings = settings
        self.feature_extract_mgr = feature_extract_mgr
        self.domainquery_mgr = domainquery_mgr
        self.classifier = None

    @staticmethod
    def is_declined(resource) -> bool:
        return resource.status in [ResourceStatus.DECLINED]

    @staticmethod
    def add_or_get_exist_resource(sess: Session, resource: Resource) -> Resource:
        row = sess.query(Resource).filter(Resource.value == resource.value).first()
        if row:
            return row

        sess.add(resource)
        sess.flush()
        return resource

    @staticmethod
    def get_resources_by_status(
        sess: Session, status: str
    ) -> Query[Resource] | Query[Any]:
        return sess.query(Resource).filter_by(status=status)

    @staticmethod
    def get_resource_by_id(sess: Session, resource_id) -> Type[Resource] | None:
        return sess.query(Resource).filter_by(id=resource_id).first()

    @staticmethod
    def get_checked_resource_by_value(
        sess: Session, value: str
    ) -> Type[Resource] | None:
        return (
            sess.query(Resource)
            .filter_by(value=value, status=ResourceStatus.CHECKED)
            .first()
        )

    @staticmethod
    def get_resource_by_value(sess: Session, value: str) -> Type[Resource] | None:
        return sess.query(Resource).filter_by(value=value).first()

    @staticmethod
    def get_checked_propogated_resource_by_value(
        sess: Session, domain_name: str
    ) -> Type[Resource] | None:
        return (
            sess.query(Resource)
            .filter(
                or_(
                    Resource.value.like("%//" + domain_name + "%"),
                    Resource.value.like("%." + domain_name + "%"),
                ),
                Resource.status == ResourceStatus.CHECKED,
                # noqa
                Resource.is_propog == True,
            )
            .first()
        )

    @staticmethod
    def get_checked_with_truerate_resources(
        sess: Session,
    ) -> Query[Type[Resource]] | Query[Any]:
        return (
            sess.query(Resource)
            .filter(Resource.status == ResourceStatus.CHECKED)
            .filter(Resource.true_rate >= 0)
        )

    @staticmethod
    def get_checked_with_predictionrate_resources(
        sess: Session,
    ) -> Query[Type[Resource]] | Query[Any]:
        return (
            sess.query(Resource)
            .filter(Resource.status == ResourceStatus.CHECKED)
            .filter(Resource.prediction_rate >= 0)
        )

    @staticmethod
    def prepare_domain_name_for_search(
        domain_name: str, domain_endings_langs: list, character: str
    ) -> str:
        # TODO check this function and make it more clear what it does
        domain_parts = domain_name.split(".")

        has_many_domain_parts = len(domain_parts) == 2

        domain_replaced_part = domain_name

        if has_many_domain_parts:
            domain_replace_part = domain_parts[1]
        else:
            domain_replace_part = domain_name

        for domain_endings_lang in domain_endings_langs:
            domain_replaced_part = domain_replace_part.replace(
                domain_endings_lang, character
            )
            if domain_replaced_part == character:
                break

        # TODO here is something to fix

        if has_many_domain_parts:
            # Restore domain with % and return back it for the search
            domain_replaced_part = f"{domain_parts[0]}.{domain_replaced_part}"

        return domain_replaced_part

    @debug_log_entry_exit(__name__)
    def _get_requested_checked_resource(
        self, sess: Session, resource: Resource
    ) -> Type[Resource] | None:
        domain_name = None

        # Rebuild  query-search to make it similar and remove unnecessary parts from search
        if resource.type == ResourceType.URL:
            # Get only domain name if it`s url resource and build general domain+query
            domain_name = url.get_domain_name_from_url(resource.value)

            # Here the domain_name should be replaced with % to search with like
            prepared_domain_name = self.prepare_domain_name_for_search(
                domain_name, DomainQueryMgr.domain_endings_langs, "%"
            )

            # Get domain query entity if such a domain exists in database
            domainquery = self.domainquery_mgr.get_domainquery_by_domainname(
                sess, prepared_domain_name
            )

            if domainquery:
                # build new resource value by extracting searching value from query-get-string
                resource_value_new = (
                    self.domainquery_mgr.build_resource_val_by_domain_query_string(
                        domainquery, resource.value
                    )
                )

                if resource_value_new:
                    # overwrite old value with a new one
                    resource.value = resource_value_new

        # first of all, check if such resource exists in the system
        requested_resource = self.get_checked_resource_by_value(sess, resource.value)

        if not requested_resource and resource.type == ResourceType.URL and domain_name:
            # check if such resource with is_propog exists and use like sql to check using domain_name
            requested_resource = self.get_checked_propogated_resource_by_value(
                sess, domain_name
            )

        return requested_resource

    @debug_log_entry_exit(__name__)
    def get(self, sess: Session, resource: Resource) -> Type[Resource] | None:
        return self._get_requested_checked_resource(sess, resource)

    @debug_log_entry_exit(__name__)
    def get_and_predict(
        self,
        sess: Session,
        resource: Resource,
        recheck: bool = False,
        show_top_features: bool = False,
    ):
        # if requested resource is not found
        #   1. add resource as check, then start feature extraction
        #   2. predict directly if process_requested_resource is asked for that
        #   3. otherwise the resource is set as extracted and wait before the resource is going to be predicted

        # check if the resource with such a val exists
        requested_resource = self._get_requested_checked_resource(sess, resource)

        # if the requested resource was not found or recheck is given or top features are requested, and we don't
        # have them
        has_top_features = (
            requested_resource
            and show_top_features
            and not requested_resource.top_features
        )

        if requested_resource is None or recheck or has_top_features:
            # this one we need if the resource was not found with checked status,
            # but it can be already in any other statuses,
            # so we need to get it to avoid duplicated resources
            if requested_resource:
                resource_potential = requested_resource
            else:
                resource_potential = ResourceMgr.get_resource_by_value(
                    sess, resource.value
                )

            if resource_potential:
                # CHECKED status should be also be there, otherwise when recheck is true, it does not take it
                if resource_potential.status in [
                    ResourceStatus.CHECK,
                    ResourceStatus.CHECKED,
                    ResourceStatus.DECLINED,
                    ResourceStatus.EXTRACTED,
                ]:
                    # if the found resource has these statuses, it can be given further to be again checked
                    resource = resource_potential
                else:
                    # if the found resource has any other statuses than above, say it's in progress
                    raise AppError.resource_prediction_illegal_state()

            # if the resource has any other statuses, it can be in progress of extracting, predicting or just
            # deleted, and we should avoid duplicating resources or giving not "checked" resources
            # we need to inform the user
            requested_resource = self.process_requested_resource(
                sess,
                resource,
                analyse_resource=True,
                predict_resource=True,
                show_top_features=show_top_features,
            )
            sess.flush()

        return requested_resource

    @debug_log_entry_exit(__name__)
    def process_requested_resource(
        self,
        sess: Session,
        res: Resource,
        analyse_resource=True,
        predict_resource=True,
        show_top_features=False,
    ):
        res.status = ResourceStatus.CHECK

        if res.id is None:
            res = self.add_or_get_exist_resource(sess, res)

        # commit to database the status of the resource to avoid race-conditions
        sess.flush()

        if analyse_resource and res.status == ResourceStatus.CHECK:
            res = self.feature_extract_mgr.extract(sess, res)

        if predict_resource and res.status == ResourceStatus.EXTRACTED:
            res = self.predict_resource(sess, res, show_top_features)

        return res

    @debug_log_entry_exit(__name__)
    def analyse_resources(self, sess: Session) -> None:
        resources = self.get_resources_by_status(sess, ResourceStatus.CHECK)
        # TODO maybe take outside???
        find_cmd = "find ./src/data -name '*.txt' -type f"

        for res in resources:
            try:
                res = self.feature_extract_mgr.extract(sess, res)
                if ResourceStatus.DECLINED == res.status:
                    val = res.value.replace("/", "\\/")
                    sed = f"sed -i -e '/{val}/Id'"
                    cmd = f"{find_cmd} | xargs {sed}"
                    os.system(cmd)
                    sess.delete(res)
                else:
                    res.status = ResourceStatus.CHECKED

                sess.commit()
            except Exception as e:
                logger.error("error occurred while analysing resources: {}", str(e))
                sess.rollback()

    @debug_log_entry_exit(__name__)
    def predict_resource(
        self, sess: Session, resource: Resource, show_top_features: bool = False
    ):
        if self.classifier is None:
            raise ValueError("The classifier is not set")

        if resource.id is None:
            raise ValueError("The resource is not set")

        resource.status = ResourceStatus.PREDICTING
        sess.flush()

        prediction_result, top_features = self.classifier.predict_resource(
            resource, show_top_features
        )

        if prediction_result is None:
            resource.prediction_rate = None
            resource.top_features = None
            resource.status = ResourceStatus.DECLINED
            resource.status_reason_code = http.HTTPStatus.UNPROCESSABLE_ENTITY
            resource.status_reason_msg = (
                "Cannot predict the resource. Please check the logs"
            )
        else:
            resource.prediction_rate = int(prediction_result[0])
            resource.top_features = json.dumps(top_features)
            resource.status = ResourceStatus.CHECKED
            resource.status_reason_code = ""
            resource.status_reason_msg = ""

        sess.flush()

        return resource

    @debug_log_entry_exit(__name__)
    def read_resources_from_file(
        self, sess: Session, absolute_file_path: str, update_resource: bool = False
    ):
        # TODO: poor code, needs refactoring
        file_path = Path(absolute_file_path)
        if file_path.is_file():
            with open(absolute_file_path, encoding="utf-8") as f:
                lines = [x.strip() for x in f.readlines()]
                for line in lines:
                    line = line.split(",")
                    line = [x.strip() for x in line]

                    if len(line) > 1:
                        res_new_pred = int(line[0])
                        res_new_value = line[1]
                        res_new_type = line[2]

                        # optional parameters
                        res_new_ispropog = False
                        res_new_lang = Lang.english

                        if len(line) > 3:
                            if line[3].lower() == "true":
                                res_new_ispropog = True

                        if len(line) > 4:
                            if line[4]:
                                res_new_lang = line[4]

                        if update_resource:
                            resource = self.get_resource_by_value(sess, res_new_value)
                            if resource:
                                resource.type = res_new_type
                                resource.lang = res_new_lang
                                resource.is_propog = res_new_ispropog
                                resource.true_rate = res_new_pred
                                resource.prediction_rate = res_new_pred
                                sess.add(resource)
                        else:
                            resource = Resource(
                                value=res_new_value,
                                type=res_new_type,
                                status="check",
                                lang=res_new_lang,
                                is_propog=res_new_ispropog,
                                true_rate=res_new_pred,
                                prediction_rate=res_new_pred,
                            )
                            self.add_or_get_exist_resource(sess, resource)
