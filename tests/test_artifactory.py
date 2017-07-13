from .import_context import boothby
from boothby.artifactory_navigator import artifactory_parser
import unittest

TEST_MODULE_RESPONSE = "tests/data/artifactory_module_response.txt"

TEST_ORG_RESPONSE = "tests/data/artifactory_org_response.txt"


def test_list_modules():
    parser = artifactory_parser()
    modules = parser.parse_modules(open(TEST_ORG_RESPONSE))
    expected_modules = [
        u"python",
        u"jdk"
    ]
    assert modules == expected_modules


def test_list_versions():
    parser = artifactory_parser()
    versions = parser.parse_versions(open(TEST_MODULE_RESPONSE))
    expected_versions = [
        u"1.0.223",
        u"1.0.227",
        u"1.0.228",
        u"1.0.231",
        u"1.0.233",
        u"1.0.238",
        u"1.0.240",
        u"1.0.260",
        u"1.2.48",
        u"15.1.4",
        u"154.1.4",
        u"171.2.1"
    ]
    assert versions == expected_versions
