import http

from fastapi import HTTPException


class AppError:
    SUPPORT_TEXT = "Please contact surfgate.app support team to get more information"

    @staticmethod
    def resource_not_found() -> HTTPException:
        return HTTPException(http.HTTPStatus.NOT_FOUND, "No such resource")

    @staticmethod
    def resource_prediction_illegal_state() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.CONFLICT,
            "The resource cannot be evaluated. It is currently in progress",
        )

    @staticmethod
    def resource_declined() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.BAD_REQUEST,
            f"The resource is declined. {AppError.SUPPORT_TEXT}",
        )

    @staticmethod
    def resource_not_reachable() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.BAD_REQUEST,
            f"The resource is not reachable. {AppError.SUPPORT_TEXT}",
        )

    @staticmethod
    def resource_not_fetchable(msg: str) -> HTTPException:
        return HTTPException(
            http.HTTPStatus.UNPROCESSABLE_ENTITY,
            msg,
        )

    @staticmethod
    def prediction_illegal_state() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "The model or the vectorizer is not set",
        )

    @staticmethod
    def key_not_found() -> HTTPException:
        return HTTPException(http.HTTPStatus.NOT_FOUND, "The license key is invalid")

    @staticmethod
    def key_expired() -> HTTPException:
        return HTTPException(http.HTTPStatus.NOT_FOUND, "The license key has expired")

    @staticmethod
    def key_already_exists() -> HTTPException:
        return HTTPException(http.HTTPStatus.CONFLICT, "The license key already exists")

    @staticmethod
    def key_create() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "An error occurred while creating a license key",
        )

    @staticmethod
    def key_update() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "An error occurred while updating the license key",
        )

    @staticmethod
    def key_no_permissions() -> HTTPException:
        return HTTPException(http.HTTPStatus.FORBIDDEN, "Not enough permissions")

    @staticmethod
    def key_delete() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "An error occurred while deleting the license key",
        )

    @staticmethod
    def user_email_already_exists() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.CONFLICT,
            "This customer email already exists",
        )

    @staticmethod
    def user_create() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "An error occurred while creating a user",
        )

    @staticmethod
    def user_not_found() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.NOT_FOUND,
            "The user does not exist",
        )

    @staticmethod
    def task_create() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "An error occurred while creating a task",
        )

    @staticmethod
    def task_create_illegal_state() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "The task is currently in progress",
        )

    @staticmethod
    def task_not_found() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.NOT_FOUND,
            "Such a task has not been found",
        )

    @staticmethod
    def task_get_illegal_state() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "The task is still in progress. Please check again later or wait for a notification "
            "message on the provided `return_url` endpoint",
        )

    @staticmethod
    def task_declined() -> HTTPException:
        return HTTPException(
            http.HTTPStatus.BAD_REQUEST,
            f"The task is declined. {AppError.SUPPORT_TEXT}",
        )

    @staticmethod
    def too_many_requests() -> HTTPException:
        return HTTPException(http.HTTPStatus.TOO_MANY_REQUESTS, "You have sent too many requests, please try again "
                                                                "later")
