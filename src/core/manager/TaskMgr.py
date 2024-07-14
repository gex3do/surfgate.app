import json
import zlib
from datetime import date
from typing import Any, Type
from uuid import UUID

import datedelta
import requests
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from src.core.api.Responser import Responser
from src.core.AppEnum import (
    PredictionRate,
    ResourceType,
    TaskNotificationResponse,
    TaskStatus,
)
from src.core.entity.PageItem import PageItem
from src.core.entity.Resource import Resource
from src.core.entity.Task import Task
from src.core.helper.rate import prediction_to_violation
from src.core.manager.FeatureExtractMgr import fetchers
from src.core.webscrapper import get_content_by_val_and_collect_links
from src.utils.logger import logger


class TaskMgr:
    delete_in_days_default = 30

    def __init__(self, settings, resource_mgr):
        self.settings = settings
        self.resource_mgr = resource_mgr
        self.task_notification_tries = settings["main"]["task"][
            "task_notification_tries"
        ]

    @staticmethod
    def get_task_by_uuid(sess: Session, uuid: UUID) -> Type[Task] | None:
        return sess.query(Task).filter(Task.uuid == str(uuid)).first()

    @staticmethod
    def get_tasks_by_status(
        sess: Session, status: str
    ) -> Query[Task] | Query[Any]:
        return sess.query(Task).filter(Task.status == status)

    def get_tasks_for_deletion(self, sess: Session) -> Query[Type[Task]] | Query[Any]:
        delete_in_days = self.delete_in_days_default

        if self.settings["main"]["task"]["delete_in_days"]:
            delete_in_days = self.settings["main"]["task"]["delete_in_days"]

        today = date.today()
        diff_date = today - datedelta.datedelta(days=delete_in_days)

        return sess.query(Task).filter(
            Task.status != TaskStatus.DELETED, Task.creation_date < diff_date
        )

    # noinspection PyPep8
    def get_tasks_to_be_notified(self, sess: Session) -> Query[Type[Task]] | Query[Any]:
        return sess.query(Task).filter(
            or_(
                Task.status == TaskStatus.CHECKED,
                Task.status == TaskStatus.DECLINED,
            ),
            # noqa
            Task.notification_done == False,
            Task.notified <= self.task_notification_tries,
        )

    @staticmethod
    def is_inprogress(task) -> bool:
        return task.status in [
            TaskStatus.CHECK,
            TaskStatus.EXTRACTING,
            TaskStatus.EXTRACTED,
            TaskStatus.PREDICTING,
        ]

    @staticmethod
    def is_declined(task: Type[Task]) -> bool:
        return task.status in [TaskStatus.DECLINED]

    @staticmethod
    def is_checked(task: Type[Task]) -> bool:
        return task.status in [TaskStatus.CHECKED]

    @staticmethod
    def is_deleted(task: Type[Task]) -> bool:
        return task.status in [TaskStatus.DELETED]

    @staticmethod
    def add_task(sess: Session, task: Task) -> Task | None:
        """
        add new task, in case if there is no such a task already with the status:
            check || extracting || extracted || predicting

        Args:
            sess: SQLAlchemy Session
            task: task object

        Returns: Task or None
        """

        task_found = (
            sess.query(Task)
            .filter(
                Task.value == task.value,
                Task.return_url == task.return_url,
                Task.status.in_(
                    [
                        TaskStatus.CHECK,
                        TaskStatus.EXTRACTING,
                        TaskStatus.EXTRACTED,
                        TaskStatus.PREDICTING,
                    ]
                ),
            )
            .first()
        )

        if task_found:
            return None

        sess.add(task)
        sess.flush()
        return task

    def run_delete_tasks(self, sess):
        """
        Delete tasks older than given days

        Args:
            sess: SQLAlchemy Session

        Returns: None
        """
        tasks = self.get_tasks_for_deletion(sess)
        for task in tasks:
            if task.status != TaskStatus.DELETED:
                task.data = "".encode()
                task.status = TaskStatus.DELETED
                sess.flush()
        sess.commit()

    def run_check_tasks(self, sess: Session):
        """
        Get `check` tasks, collects links, creates json_data from page_items and saves
            it to 'task.data' for future needs.

        Args:
            sess: SQLAlchemy Session

        Returns: None
        """
        tasks = self.get_tasks_by_status(sess, TaskStatus.CHECK)

        for task in tasks:
            try:
                if task.status == TaskStatus.CHECK:
                    # change to 'extracting' task before continue
                    task.status = TaskStatus.EXTRACTING
                    sess.flush()

                    # create first root page item which contains all subpage items after if needed
                    root_page_item = PageItem(link=task.value)

                    # collect links pro depth and get page content.
                    # Start from 0. Even if max_depth is 0, content will be taken
                    self._run_check_task(0, task.maxdepth, [root_page_item])

                    # extract resources and attach them to task
                    self._create_resources_and_attach_to_task(
                        sess, root_page_item, task
                    )

                    task.status = TaskStatus.EXTRACTED

                    task.status_reason_msg = ""
                    task.data = self._to_json_and_zip(root_page_item)

                    sess.flush()
            except Exception as e:
                task.status = TaskStatus.DECLINED
                task.status_reason_msg = str(e) + " while run_check_tasks"
                task.data = "".encode()
            finally:
                sess.flush()

    def predict_tasks_resources(self, sess: Session):
        """
        Predict tasks resources

        Args:
            sess: SQLAlchemy Session

        Returns: None
        """

        tasks = self.get_tasks_by_status(sess, TaskStatus.EXTRACTED)
        for task in tasks:
            try:
                # check again if the task is EXTRACTED in case if parallel jobs has also the same task and already
                # started it to do
                if task.status == TaskStatus.EXTRACTED:
                    # change to 'predicting' task before continue
                    task.status = TaskStatus.PREDICTING
                    sess.flush()

                    json_unzipped = self._unzip_and_to_json(task.data)

                    page_item = PageItem(json_data=json_unzipped)

                    # predict resource and set rate to page_item
                    self._predict_resources(sess, page_item, task)

                    task.status = TaskStatus.CHECKED
                    task.status_reason_msg = ""
                    task.data = self._to_json_and_zip(page_item)
            except Exception as e:
                task.status = TaskStatus.DECLINED
                task.status_reason_msg = str(e) + " while predict_tasks_resources"
                task.data = "".encode()
            sess.commit()

    def send_tasks_notifications(self, sess):
        """
        Send tasks notifications

        Args:
            sess: SQLAlchemy Session

        Returns: None
        """
        tasks = self.get_tasks_to_be_notified(sess)
        for task in tasks:
            self._send_notification(sess, task)
        sess.commit()

    def run_checked_task(self, sess, task, show_top_features: bool = False):
        # start collecting stats
        stats = {
            PredictionRate.UNDETERMINED: 0,
            PredictionRate.LOW: 0,
            PredictionRate.MEDIUM: 0,
            PredictionRate.HIGH: 0,
        }

        # this method has 2 possibilities:
        # 1. save rate while prediction and here just get the task.data (but it will be not actual)
        # 2. unzip the task.data , get again all resources with their rate, and convert back to json_str
        json_unzipped = self._unzip_and_to_json(task.data)

        # convert json back to page-item objects
        page_root_item = PageItem(json_data=json_unzipped)

        # collect resource rates for the task and remove unnecessary fields
        self._collect_resources_rates(
            sess,
            page_root_item,
            stats=stats,
            latest_resource_rate=self.settings["main"]["task"]["latest_resource_rate"],
            show_top_features=show_top_features,
        )

        page_item_in_dicts = TaskMgr.to_dicts(page_root_item.__dict__)

        return page_item_in_dicts, stats

    @staticmethod
    def to_dicts(page_item: dict) -> dict:
        if "pages" in page_item:
            for x in range(len(page_item["pages"])):
                page_item["pages"][x] = TaskMgr.to_dicts(page_item["pages"][x].__dict__)

        return page_item

    @staticmethod
    def jdefault(o):
        return o.__dict__

    def _run_check_task(self, current_depth, max_depth, pages):
        # go through all links and get another links
        next_pages = []

        for page_item in pages:
            local_links = None
            for fetcher in fetchers:
                local_links = get_content_by_val_and_collect_links(
                    fetcher["fetch"], page_item.link, max_depth > 0
                )
                if local_links is not None:
                    break

            if local_links is None:
                logger.warn(
                    "cannot collect any link, something wrong went here: {}",
                    page_item.link,
                )

            if len(local_links) > 0:
                # creates new page-items from getting links
                page_item.create_pages_by_links(local_links)
                next_pages.extend(page_item.pages)

        if (current_depth + 1) < max_depth:
            self._run_check_task(current_depth + 1, max_depth, next_pages)

    def _create_resources_and_attach_to_task(self, sess: Session, page_item: PageItem, task: Task):
        """
        Create resources if needed and attach resource_id to page_item

        Args:
            sess: current session
            page_item: page object
            task: current task

        Returns: None
        """
        resource = Resource(
            value=page_item.link,
            type=ResourceType.URL,
            status="check",
            is_propog=False,
            lang=task.lang,
        )

        # create a new resource if the resource does not exist, otherwise use already created
        resource = self.resource_mgr.add_or_get_exist_resource(sess, resource)

        # set resource-id for future needs
        page_item.resource_id = resource.id

        # set top-features for future needs
        page_item.top_features = resource.top_features

        # next subpage
        for page_item_new in page_item.pages:
            self._create_resources_and_attach_to_task(sess, page_item_new, task)

    def _predict_resources(self, sess, page_item: PageItem, task: Task):
        """
        Predict task resources and link

        Args:
            sess: SQLAlchemy Session
            page_item: Page Item
            task: Task

        Returns: None

        Raises:
            ValueError
        """
        resource_id = page_item.resource_id

        if resource_id:
            requested_resource = self.resource_mgr.get_resource_by_id(sess, resource_id)

            if requested_resource:
                try:
                    if task.recheck:
                        # if re-check, then re-predict the resource
                        requested_resource = self.resource_mgr.get_and_predict(
                            sess,
                            requested_resource,
                            recheck=task.recheck,
                            show_top_features=True,
                        )
                    elif (
                        requested_resource
                        and requested_resource.prediction_rate is None
                    ):
                        # if resource is not yet predicted, predict it
                        requested_resource = self.resource_mgr.get_and_predict(
                            sess, requested_resource
                        )
                except HTTPException as e:
                    logger.info(
                        "While task prediction, the resource is not predicted because it`s already in "
                        "progress: %s",
                        str(e),
                    )

                page_item.top_features = requested_resource.top_features
                page_item.rate = prediction_to_violation(requested_resource.prediction_rate)
            else:
                raise ValueError(
                    f"There is no resource created for the value {page_item.link}"
                )
        else:
            raise ValueError(
                f"There is no resource created for the value {page_item.link}"
            )

        # next subpage
        for page_item_new in page_item.pages:
            self._predict_resources(sess, page_item_new, task)

    def _collect_resources_rates(
        self,
        sess,
        page_item,
        stats=None,
        latest_resource_rate=False,
        show_top_features: bool = False,
    ):
        """
        Collects latest resource rates and clean up fields

        Args:
            sess: SQLAlchemy Session
            page_item: Page item
            stats: collects stats
            latest_resource_rate: if `true` then collect latest resource rates,
                otherwise use the one while prediction
            show_top_features: show top features

        Returns: None

        Raises:
            ValueError
        """
        if latest_resource_rate:
            resource_id = page_item.resource_id

            if resource_id:
                resource = self.resource_mgr.get_resource_by_id(sess, resource_id)

                if resource:
                    # get latest resource rate
                    page_item.rate = prediction_to_violation(resource.prediction_rate)
                else:
                    raise ValueError(
                        "There is no resource created for the value {}".format(
                            page_item.link
                        )
                    )
            else:
                raise ValueError(
                    "There is no resource created for the value {}".format(
                        page_item.link
                    )
                )

        stats[page_item.rate] = stats[page_item.rate] + 1

        # clean up unnecessary fields for the response
        page_item.clean_fields(show_top_features=show_top_features)

        # go to next subpage
        if hasattr(page_item, "pages"):
            for pg in page_item.pages:
                self._collect_resources_rates(
                    sess,
                    pg,
                    stats=stats,
                    latest_resource_rate=latest_resource_rate,
                    show_top_features=show_top_features,
                )

    def _to_json_and_zip(self, page_item):
        # save created tree with a dumps to data of the task
        json_str = self._to_json(page_item)
        # encode json_str to byte, then compress and then back to str
        return zlib.compress(json_str.encode(), 9)

    @staticmethod
    def _unzip_and_to_json(zip_json):
        """
        unzip and decode from byte string str

        :param zip_json: zipped and encoded str
        :return: unzipped and decoded str (json-str)
        """
        return zlib.decompress(zip_json).decode()

    @staticmethod
    def _to_json(page_item):
        """
        Save created tree with a dumps to data of the task

        Args:
            page_item: Page item

        Returns: json string
        """
        return json.dumps(page_item, default=TaskMgr.jdefault)

    @staticmethod
    def _send_notification(sess, task):
        payload, json_status = Responser.create_task_notification(task)
        payload_json = json.dumps(payload.to_dict())

        try:
            headers = {"Content-type": "application/json", "Accept": "text/plain"}
            task.notified = task.notified + 1
            response = requests.get(task.return_url, data=payload_json, headers=headers)

            # Consider any status other than 2xx an error
            if response.status_code // 100 == 2:
                json_obj = response.json()

                if (
                    "status" in json_obj
                    and json_obj["status"] == TaskNotificationResponse.RECEIVED
                ):
                    task.notification_done = True
            else:
                logger.error(
                    "Task %s request-notification send but response is not 200 but %s",
                    task.uuid,
                    response.status_code,
                )
        except requests.exceptions.RequestException as e:
            # A serious problem happened, like an SSLError or InvalidURL
            logger.error(
                "Task %s failed while sending request-notification with an error: %s",
                task.uuid,
                e,
            )
        finally:
            sess.flush()
