from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

from sqlalchemy.orm import Session

from src.core.entity.domain_query import DomainQuery


class DomainQueryMgr:
    domain_mask = "https://{}?{}"

    domain_endings_langs = [
        "com",
        "org",
        "net",
        "info",
        "co",
        "edu",
        "gov",
        "be",
        "el",
        "lt",
        "pt",
        "bg",
        "es",
        "lu",
        "ro",
        "cz",
        "fr",
        "hu",
        "si",
        "dk",
        "hr",
        "mt",
        "sk",
        "de",
        "it",
        "nl",
        "fi",
        "ee",
        "cy",
        "at",
        "se",
        "ie",
        "lv",
        "pl",
        "uk",
        "am",
        "ge",
        "us",
        "en",
        "cn",
        "nl",
        "ru",
    ]

    def __init__(self, settings: dict):
        self.settings = settings

    @staticmethod
    def add_domainquery(sess: Session, domain_query: DomainQuery) -> None:
        # TODO check if we can replace
        #  row = DomainQuery.query.filter(DomainQuery.name == domain_query.name).first()
        q = sess.query(DomainQuery).filter(DomainQuery.name == domain_query.name)
        if sess.query(q.exists()).scalar() is False:
            sess.add(domain_query)

    @staticmethod
    def get_domainquery_by_domainname(sess: Session, domain_name: str):
        # noinspection PyUnresolvedReferences
        return (
            sess.query(DomainQuery)
            .filter(DomainQuery.name.like("%" + domain_name + "%"))
            .first()
        )

    @staticmethod
    def _get_query_search_val(domain_query: DomainQuery, val: str):
        parsed = urlparse(val)
        if not parsed:
            return None

        qs = parse_qs(parsed.query)

        return (
            qs[domain_query.query_key][0]
            if qs and domain_query.query_key in qs
            else None
        )

    def build_resource_val_by_domain_query_string(
        self, domain_query: DomainQuery, val: str
    ):
        query_search_val = self._get_query_search_val(domain_query, val)
        if not query_search_val:
            return None

        query_str = domain_query.query_key + "=" + quote_plus(query_search_val)

        return self.domain_mask.format(domain_query.value, query_str)

    def read_domainquery_from_file(
        self, sess: Session, absolute_file_path: str
    ) -> None:
        file_path = Path(absolute_file_path)

        if not file_path.is_file():
            ValueError("DomainQuery file is not a file: %s", file_path)

        with open(absolute_file_path, "r") as f:
            lines = [x.strip() for x in f.readlines()]

            for line in lines:
                line = line.split(",")
                line = [x.strip() for x in line]

                if len(line) == 3:
                    domain_name = line[0]
                    query_key = line[1]
                    value = line[2]

                    self.add_domainquery(
                        sess,
                        DomainQuery(name=domain_name, query_key=query_key, value=value),
                    )
