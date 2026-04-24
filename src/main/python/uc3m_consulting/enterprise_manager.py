"""Module """
import re
import json

from datetime import datetime, timezone
from freezegun import freeze_time
from uc3m_consulting.enterprise_project import EnterpriseProject
from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException
from uc3m_consulting.enterprise_manager_config import (PROJECTS_STORE_FILE,
                                                       TEST_DOCUMENTS_STORE_FILE,
                                                       TEST_NUMDOCS_STORE_FILE)
from uc3m_consulting.project_document import ProjectDocument

class EnterpriseManager:
    """Class for providing the methods for managing the orders"""
    def __init__(self):
        pass

    @staticmethod
    def _calculate_cif_control_digit(cif_digits: str) -> int:
        """Calculates the control digit for a CIF."""
        even_position_sum = 0
        odd_position_sum = 0

        for index, digit in enumerate(cif_digits):
            if index % 2 == 0:
                doubled_value = int(digit) * 2
                if doubled_value > 9:
                    even_position_sum = (
                            even_position_sum
                            + (doubled_value // 10)
                            + (doubled_value % 10)
                    )
                else:
                    even_position_sum = even_position_sum + doubled_value
            else:
                odd_position_sum = odd_position_sum + int(digit)

        total_sum = even_position_sum + odd_position_sum
        remainder = total_sum % 10
        control_digit = 10 - remainder

        if control_digit == 10:
            control_digit = 0

        return control_digit

    @staticmethod
    def validate_cif(cif_code: str):
        """Validate a CIF number."""
        if not isinstance(cif_code, str):
            raise EnterpriseManagementException("CIF code must be a string")

        cif_pattern = re.compile(r"^[ABCDEFGHJKNPQRSUVW]\d{7}[0-9A-J]$")
        if not cif_pattern.fullmatch(cif_code):
            raise EnterpriseManagementException("Invalid CIF format")

        cif_letter = cif_code[0]
        cif_digits = cif_code[1:8]
        control_character = cif_code[8]

        # Call the newly extracted helper method
        control_digit = EnterpriseManager._calculate_cif_control_digit(cif_digits)

        control_letters = "JABCDEFGHI"

        if cif_letter in ('A', 'B', 'E', 'H'):
            if str(control_digit) != control_character:
                raise EnterpriseManagementException("Invalid CIF character control number")
        elif cif_letter in ('P', 'Q', 'S', 'K'):
            if control_letters[control_digit] != control_character:
                raise EnterpriseManagementException("Invalid CIF character control letter")
        else:
            raise EnterpriseManagementException("CIF type not supported")

        return True

    def validate_starting_date(self, starting_date: str):
        """Validate the starting date format and value."""
        date_pattern = re.compile(r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$")
        match = date_pattern.fullmatch(starting_date)
        if not match:
            raise EnterpriseManagementException("Invalid date format")

        try:
            parsed_date = datetime.strptime(starting_date, "%d/%m/%Y").date()
        except ValueError as ex:
            raise EnterpriseManagementException("Invalid date format") from ex

        if parsed_date < datetime.now(timezone.utc).date():
            raise EnterpriseManagementException("Project's date must be today or later.")

        if parsed_date.year < 2025 or parsed_date.year > 2050:
            raise EnterpriseManagementException("Invalid date format")

        return starting_date

    def _validate_project_acronym(self, project_acronym: str):
        """Validates the project acronym."""
        acronym_pattern = re.compile(r"^[a-zA-Z0-9]{5,10}")
        if not acronym_pattern.fullmatch(project_acronym):
            raise EnterpriseManagementException("Invalid acronym")

    def _validate_project_description(self, project_description: str):
        """Validates the project description."""
        description_pattern = re.compile(r"^.{10,30}$")
        if not description_pattern.fullmatch(project_description):
            raise EnterpriseManagementException("Invalid description format")

    def _validate_department(self, department: str):
        """Validates the department."""
        department_pattern = re.compile(r"(HR|FINANCE|LEGAL|LOGISTICS)")
        if not department_pattern.fullmatch(department):
            raise EnterpriseManagementException("Invalid department")

    def _validate_budget(self, budget: str):
        """Validates the budget format and limits."""
        try:
            budget_amount = float(budget)
        except ValueError as exc:
            raise EnterpriseManagementException("Invalid budget amount") from exc

        budget_text = str(budget_amount)
        if '.' in budget_text:
            decimal_places = len(budget_text.split('.')[1])
            if decimal_places > 2:
                raise EnterpriseManagementException("Invalid budget amount")

        if budget_amount < 50000 or budget_amount > 1000000:
            raise EnterpriseManagementException("Invalid budget amount")

    def _load_projects(self):
        """Loads projects from the JSON store."""
        try:
            with open(PROJECTS_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                return json.load(file)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as ex:
            raise EnterpriseManagementException("JSON Decode Error - Wrong JSON Format") from ex

    def _save_projects(self, projects_list):
        """Saves projects to the JSON store."""
        try:
            with open(PROJECTS_STORE_FILE, "w", encoding="utf-8", newline="") as file:
                json.dump(projects_list, file, indent=2)
        except FileNotFoundError as ex:
            raise EnterpriseManagementException("Wrong file  or file path") from ex
        except json.JSONDecodeError as ex:
            raise EnterpriseManagementException("JSON Decode Error - Wrong JSON Format") from ex

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def register_project(self,
                         company_cif: str,
                         project_acronym: str,
                         project_description: str,
                         department: str,
                         date: str,
                         budget: str):
        """registers a new project"""
        self.validate_cif(company_cif)
        self._validate_project_acronym(project_acronym)
        self._validate_project_description(project_description)
        self._validate_department(department)
        self.validate_starting_date(date)
        self._validate_budget(budget)

        new_project = EnterpriseProject(company_cif=company_cif,
                                        project_acronym=project_acronym,
                                        project_description=project_description,
                                        department=department,
                                        starting_date=date,
                                        project_budget=budget)

        projects_list = self._load_projects()

        for stored_project in projects_list:
            if stored_project == new_project.to_json():
                raise EnterpriseManagementException("Duplicated project in projects list")

        projects_list.append(new_project.to_json())
        self._save_projects(projects_list)

        return new_project.project_id

    def _validate_query_date(self, date_str: str):
        """Validate the query date format and return the parsed date."""
        date_pattern = re.compile(r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$")
        match = date_pattern.fullmatch(date_str)
        if not match:
            raise EnterpriseManagementException("Invalid date format")

        try:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError as ex:
            raise EnterpriseManagementException("Invalid date format") from ex

    def _store_documents_report(self, date_str: str, documents_found: int):
        """Store the documents report in the JSON report file."""
        report_timestamp = datetime.now(timezone.utc).timestamp()
        report_entry = {
            "Querydate": date_str,
            "ReportDate": report_timestamp,
            "Numfiles": documents_found
        }

        try:
            with open(TEST_NUMDOCS_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                reports_list = json.load(file)
        except FileNotFoundError:
            reports_list = []
        except json.JSONDecodeError as ex:
            raise EnterpriseManagementException("JSON Decode Error - Wrong JSON Format") from ex

        reports_list.append(report_entry)

        try:
            with open(TEST_NUMDOCS_STORE_FILE, "w", encoding="utf-8", newline="") as file:
                json.dump(reports_list, file, indent=2)
        except FileNotFoundError as ex:
            raise EnterpriseManagementException("Wrong file  or file path") from ex

    def find_docs(self, date_str):
        """
        Generates a JSON report counting valid documents for a specific date.

        Checks cryptographic hashes and timestamps to ensure historical data integrity.
        Saves the output to 'resultado.json'.

        Args:
            date_str (str): date to query.

        Returns:
            number of documents found if report is successfully generated and saved.

        Raises:
            EnterpriseManagementException: On invalid date, file IO errors,
                missing data, or cryptographic integrity failure.
        """
        self._validate_query_date(date_str)

        try:
            with open(TEST_DOCUMENTS_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                documents_list = json.load(file)
        except FileNotFoundError as ex:
            raise EnterpriseManagementException("Wrong file  or file path") from ex

        documents_found = 0

        for stored_document in documents_list:
            register_timestamp = stored_document["register_date"]
            document_date_str = datetime.fromtimestamp(register_timestamp).strftime("%d/%m/%Y")

            if document_date_str == date_str:
                frozen_datetime = datetime.fromtimestamp(register_timestamp, tz=timezone.utc)
                with freeze_time(frozen_datetime):
                    project_document = ProjectDocument(
                        stored_document["project_id"],
                        stored_document["file_name"]
                    )
                    if project_document.document_signature == stored_document["document_signature"]:
                        documents_found = documents_found + 1
                    else:
                        raise EnterpriseManagementException("Inconsistent document signature")

        if documents_found == 0:
            raise EnterpriseManagementException("No documents found")

        self._store_documents_report(date_str, documents_found)
        return documents_found
