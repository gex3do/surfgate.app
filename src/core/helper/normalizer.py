from src.core.AppEnum import ResourceType
from src.core.model.resource import ResourcePredictGetIn, ResourcePredictRateIn
from src.core.model.task import TaskCreateIn


def resource(
    data: ResourcePredictRateIn | ResourcePredictGetIn,
) -> ResourcePredictRateIn | ResourcePredictGetIn:
    """
    On the other hand, Wikipedia is case-sensitive except the first character of the title.
    The URLs https://en.wikipedia.org/wiki/Case_sensitivity and https://en.wikipedia.org/wiki/case_sensitivity
    leads to the same article, but https://en.wikipedia.org/wiki/CASE_SENSITIVITY returns 404.
    """
    if data.type == ResourceType.URL:
        data.value = data.value.rstrip("/")
    elif data.type == ResourceType.TEXT:
        data.value = data.value.lower().strip()
    return data


def task(data: TaskCreateIn) -> TaskCreateIn:
    data.return_url = data.return_url.rstrip("/")
    return data
