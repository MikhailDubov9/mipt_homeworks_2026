import json
import re
from collections.abc import Iterable


def _validate_parsing_args(json_str: str, keyword_callback, required_fields, keywords):
    """Checks arguments of method for parsing"""
    if not json_str:
        raise ValueError("Empty json is not valid!")
    if required_fields is None:
        raise TypeError("Required fields should be not None!")
    if keywords is None:
        raise TypeError("keywords should be not None!")
    if keyword_callback is None or not callable(keyword_callback):
        raise TypeError("Callback FUNCTION is obligatory!")


def parse_json(json_str: str, keyword_callback, required_fields: Iterable | None = None, keywords=None):
    """Parse json string, search special words and execute callback."""
    _validate_parsing_args(json_str, keyword_callback, required_fields, keywords)
    try:
        json_doc = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError("Corrupted JSON!") from exc
    for field in required_fields:
        for keyword in keywords:
            if field in json_doc.keys():
                for _ in range(re.split(" |\.|,|!|\?|:", json_doc[field]).count(keyword)):
                    keyword_callback(field, keyword)
