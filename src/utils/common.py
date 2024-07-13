from src.core.manager.DomainQueryMgr import DomainQueryMgr
from src.core.manager.FeatureExtractMgr import FeatureExtractMgr
from src.core.manager.ResourceMgr import ResourceMgr
from src.core.manager.TokenizationMgr import TokenizationMgr


def instantiate(settings: dict) -> dict:
    token_mgr = TokenizationMgr(settings)
    domainquery_mgr = DomainQueryMgr(settings)
    feature_extract_mgr = FeatureExtractMgr(settings, token_mgr)
    resource_mgr = ResourceMgr(settings, feature_extract_mgr, domainquery_mgr)
    return {
        "token_mgr": token_mgr,
        "domainquery_mgr": domainquery_mgr,
        "feature_extract_mgr": feature_extract_mgr,
        "resource_mgr": resource_mgr
    }
