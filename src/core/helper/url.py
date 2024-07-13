def get_domain_name_from_url(url: str):
    url_parts = url.split("://")
    i = (0, 1)[len(url_parts) > 1]
    dm = url_parts[i].split("?")[0].split("/")[0].split(":")[0].lower()
    if dm:
        dm = dm.replace("www.", "")
    return dm
