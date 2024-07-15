import uuid
from http import HTTPStatus

from sqlalchemy import exc
from sqlalchemy.orm.session import Session

from src.core.api.responser import Responser
from src.core.app_error import AppError
from src.core.entity.task import Task
from src.core.helper import normalizer
from src.core.manager.key_mgr import KeyMgr
from src.core.manager.resource_mgr import ResourceMgr
from src.core.manager.task_mgr import TaskMgr
from src.core.model.task import TaskCreateIn, TaskGetIn, TaskGetOut
from src.utils.logger import logger


class TaskApi:
    def __init__(
        self,
        settings: dict,
        resource_mgr: ResourceMgr,
        key_mgr: KeyMgr,
        task_mgr: TaskMgr,
    ):
        self.settings = settings
        self.resource_mgr = resource_mgr
        self.key_mgr = key_mgr
        self.task_mgr = task_mgr

    def create_task(self, sess: Session, data: TaskCreateIn):
        data = normalizer.task(data)

        task = Task(
            uuid=str(uuid.uuid4()),
            value=data.value,
            return_url=data.return_url,
            lang=data.lang,
            maxdepth=data.max_depth if data.max_depth else 1,
            recheck=data.recheck,
        )

        try:
            requested_task = self.task_mgr.add_task(sess, task)
        except exc.SQLAlchemyError as e:
            logger.error(e)
            raise AppError.task_create()

        if not requested_task:
            # if the task is in pending or in-progress mode, has the same value and return_url,
            # don`t allow adding such a task again
            raise AppError.task_create_illegal_state()

        return Responser.create_task_creation_status(requested_task)

    def get_task(self, sess: Session, data: TaskGetIn) -> (TaskGetOut, HTTPStatus):
        task = self.task_mgr.get_task_by_uuid(sess, data.uuid)

        if not task or (task and self.task_mgr.is_deleted(task)):
            # if task is not found, or it is already set as 'deleted' by cron script
            raise AppError.task_not_found()

        # if task was asked, update stats 'used+1', therefore we know that someone tried to get the info
        self._update_task_usage_stats(sess, task)

        if self.task_mgr.is_declined(task):
            raise AppError.task_declined()

        if self.task_mgr.is_inprogress(task) or not self.task_mgr.is_checked(task):
            raise AppError.task_get_illegal_state()

        page_root_item, stats = self.task_mgr.run_checked_task(
            sess, task, data.top_features
        )

        return Responser.create_task_result(page_root_item, stats)

    @staticmethod
    def _update_task_usage_stats(sess: Session, task: Task):
        task.used = task.used + 1
        sess.add(task)
        sess.flush()

    def run_check_tasks(self, sess: Session):
        """
        Get all tasks with "check" status and extract features with a crawler.
        After extraction, the task is set in "extracted" status
        :param sess: Session
        :return: None
        """
        self.task_mgr.run_check_tasks(sess)

    def predict_tasks_resources(self, sess: Session):
        self.task_mgr.predict_tasks_resources(sess)

    def send_tasks_notifications(self, sess: Session):
        self.task_mgr.send_tasks_notifications(sess)

    def run_delete_tasks(self, sess: Session):
        self.task_mgr.run_delete_tasks(sess)
