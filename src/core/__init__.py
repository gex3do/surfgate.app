from traceback import format_exc

from src.utils.logger import logger


def debug_log_entry_exit(scope_name: str):
    """
    Write debug log and register start and end of the method call.

    Args:
        scope_name: describes the scope of called method/function.
            As an example can be given module name or __name__ of the file

    Returns: None
    """
    def wrap(func: callable):
        def wrapped_f(*args, **kwargs):
            logger.info("Method started %s - %s", scope_name, func.__name__)

            stacktrace = None
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                stacktrace = format_exc()
                raise e
            finally:
                if stacktrace is not None:
                    logger.info(
                        "Method ended %s - %s with error: %s",
                        scope_name,
                        func.__name__,
                        stacktrace,
                    )
                else:
                    logger.info("Method ended %s - %s", scope_name, func.__name__)
            return result

        return wrapped_f

    return wrap
