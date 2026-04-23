"""class for testing the regsiter_project method"""
import unittest
import csv
import os.path
from unittest import TestCase
from os import remove
from freezegun import freeze_time
from uc3m_consulting import (JSON_FILES_PATH,
                             PROJECTS_STORE_FILE,
                             EnterpriseProject,
                             EnterpriseManager,
                             EnterpriseManagementException)
from uc3m_consulting.test_support import read_json_file, get_file_signature


class TestRegisterProjectTest(TestCase):
    """Class for testing register_project"""

    def setUp(self):
        """ inicializo el entorno de prueba """
        if os.path.exists(PROJECTS_STORE_FILE):
            remove(PROJECTS_STORE_FILE)

    # pylint: disable=too-many-locals
    @freeze_time("2024/12/31 13:00:00")
    def test_parametrized_cases_tests(self):
        """Parametrized cases read from testingCases_RF1.csv"""
        my_cases = JSON_FILES_PATH + "test_cases_2026_method1.csv"
        with open(my_cases, newline='', encoding='utf-8') as csvfile:
            param_test_cases = csv.DictReader(csvfile, delimiter=';')
            mngr = EnterpriseManager()
            for row in param_test_cases:
                test_id = row['ID_TEST']
                enterprise_cif = row["CIF"]
                project_acronym = row["ACRONYM"]
                project_department = row["DEPARTMENT"]
                project_budget = row["BUDGET"]
                try:
                    number_budget = float(project_budget)
                except ValueError:
                    number_budget = row["BUDGET"]
                result = row["RESULT"]
                valid = row["VALID"]
                project_date = row["STARTING_DATE"]
                project_description = row["DESCRIPTION"]

                if valid == "VALID":
                    with self.subTest(test_id + valid):
                        valor = mngr.register_project(company_cif=enterprise_cif,
                                                      project_acronym=project_acronym,
                                                      department=project_department,
                                                      budget=number_budget,
                                                      date=project_date,
                                                      project_description=project_description)
                        self.assertEqual(result, valor)
                        my_data = read_json_file(PROJECTS_STORE_FILE)
                        my_request = EnterpriseProject(company_cif=enterprise_cif,
                                                       project_acronym=project_acronym,
                                                       project_description=project_description,
                                                       starting_date=project_date,
                                                       project_budget=number_budget,
                                                       department=project_department)
                        found = False
                        for k in my_data:
                            if k["project_id"] == valor:
                                found = True
                                self.assertDictEqual(k, my_request.to_json())
                        self.assertTrue(found)
                else:
                    with self.subTest(test_id + valid):
                        hash_original = get_file_signature(PROJECTS_STORE_FILE)

                        with self.assertRaises(EnterpriseManagementException) as c_m:
                            valor = mngr.register_project(company_cif=enterprise_cif,
                                                          project_acronym=project_acronym,
                                                          department=project_department,
                                                          budget=number_budget,
                                                          date=project_date,
                                                          project_description=project_description)
                        self.assertEqual(c_m.exception.message, result)

                        hash_new = get_file_signature(PROJECTS_STORE_FILE)
                        self.assertEqual(hash_new, hash_original)

    @freeze_time("2026/03/22 13:00:00")
    def test_duplicated_project_test(self):
        """tets method for duplicated projects"""
        enterprise_cif = "A12345674"
        project_acronym = "TEST5"
        project_department = "HR"
        project_date = "22/03/2026"
        project_description = "Testing duplicated projects"
        number_budget = 50000.00

        mngr = EnterpriseManager()
        mngr.register_project(company_cif=enterprise_cif,
                              project_acronym=project_acronym,
                              project_description=project_description,
                              date=project_date,
                              budget=number_budget,
                              department=project_department)

        hash_original = get_file_signature(PROJECTS_STORE_FILE)

        with self.assertRaises(EnterpriseManagementException) as c_m:
            mngr.register_project(company_cif=enterprise_cif,
                                  project_acronym=project_acronym,
                                  project_description=project_description,
                                  date=project_date,
                                  budget=number_budget,
                                  department=project_department)
        self.assertEqual(c_m.exception.message, "Duplicated project in projects list")

        hash_new = get_file_signature(PROJECTS_STORE_FILE)
        self.assertEqual(hash_new, hash_original)

    @freeze_time("2026/03/22 13:00:00")
    def test_project_for_today(self):
        """test for a project today (using freezetime)"""
        enterprise_cif = "A12345674"
        project_acronym = "TEST5"
        project_department = "HR"
        project_date = "22/03/2026"
        project_description = "Testing today's project"
        number_budget = 50000.00
        mngr = EnterpriseManager()
        my_request = mngr.register_project(company_cif=enterprise_cif,
                                           project_acronym=project_acronym,
                                           project_description=project_description,
                                           date=project_date,
                                           budget=number_budget,
                                           department=project_department)
        self.assertEqual("6ad10748f3c9137c0f22ff7d4eed8d19", my_request)
        my_data = read_json_file(PROJECTS_STORE_FILE)
        my_project = EnterpriseProject(company_cif=enterprise_cif,
                                       project_acronym=project_acronym,
                                       project_description=project_description,
                                       starting_date=project_date,
                                       project_budget=number_budget,
                                       department=project_department)
        found = False
        for k in my_data:
            if k["project_id"] == my_request:
                found = True
                self.assertDictEqual(k, my_project.to_json())
        self.assertTrue(found)

    @freeze_time("2025/03/22 13:00:00")
    def test_project_for_tomorrow(self):
        """test for a tomorrow's project (using freezetime)"""
        enterprise_cif = "A12345674"
        project_acronym = "TEST5"
        project_department = "HR"
        project_date = "23/03/2026"
        project_description = "Testing tomorrow's project"
        number_budget = 50000.00
        mngr = EnterpriseManager()
        my_request = mngr.register_project(company_cif=enterprise_cif,
                                           project_acronym=project_acronym,
                                           project_description=project_description,
                                           date=project_date,
                                           budget=number_budget,
                                           department=project_department)
        self.assertEqual("8aab556991e7b0f1361b72e3ab17fa81", my_request)
        my_data = read_json_file(PROJECTS_STORE_FILE)
        my_project = EnterpriseProject(company_cif=enterprise_cif,
                                       project_acronym=project_acronym,
                                       project_description=project_description,
                                       starting_date=project_date,
                                       project_budget=number_budget,
                                       department=project_department)
        found = False
        for k in my_data:
            if k["project_id"] == my_request:
                found = True
                self.assertDictEqual(k, my_project.to_json())
        self.assertTrue(found)

    @freeze_time("2026/03/26 13:00:00")
    def test_project_yesterday_test(self):
        """test for a yesterday's project (using freezetime)"""
        enterprise_cif = "A12345674"
        project_acronym = "TEST5"
        project_department = "HR"
        project_date = "23/03/2026"
        project_description = "Testing yesteday's project"
        number_budget = 50000.00
        mngr = EnterpriseManager()

        hash_original = get_file_signature(PROJECTS_STORE_FILE)

        with self.assertRaises(EnterpriseManagementException) as c_m:
            mngr.register_project(company_cif=enterprise_cif,
                                  project_acronym=project_acronym,
                                  project_description=project_description,
                                  date=project_date,
                                  budget=number_budget,
                                  department=project_department)
        self.assertEqual(c_m.exception.message, "Project's date must be today or later.")

        hash_new = get_file_signature(PROJECTS_STORE_FILE)
        self.assertEqual(hash_new, hash_original)


if __name__ == '__main__':
    unittest.main()
