"""Shared helpers for unit tests."""
import json
import os.path
import hashlib

from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException


def read_json_file(file_path: str):
    """Read a JSON file and return its contents."""
    try:
        with open(file_path, "r", encoding="utf-8", newline="") as file:
            data = json.load(file)
    except FileNotFoundError as ex:
        raise EnterpriseManagementException("Wrong file or file path") from ex
    except json.JSONDecodeError as ex:
        raise EnterpriseManagementException("JSON Decode Error - Wrong JSON Format") from ex
    return data


def get_file_signature(file_path: str):
    """Return a signature for a file or an empty string if it does not exist."""
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8", newline="") as file:
            return hashlib.md5(str(file).encode()).hexdigest()
    return ""
