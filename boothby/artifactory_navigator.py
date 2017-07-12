import requests
from urlparse import urljoin
import abc
import bs4

class navigator(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def list_available_versions(self, module):
        pass

    @abc.abstractmethod
    def list_available_modules(self):
        pass


class artifactory_parser(object):
    def parse_versions_response(self, response):
        pass

    def parse_modules_response(self, response):
        soup = bs4.BeautifulSoup(response, "lxml")
        exclude_back = lambda k: ".." not in k["href"]
        links = filter(exclude_back, soup.find("body").find_all("a"))
        module_names = [ x.text.replace(u"/",u"") for x in links ]
        return module_names

class artifactory_navigator(navigator):

    def __init__(self, repository_list):
        self.repository_list = repository_list

    def list_available_versions(self, org, module):
        parser = artifactory_parser()
        available_versions = []
        for repo in self.repository_list:
            response = requests.get(urljoin(repo, org, module))
            available_versions.extend(parser.parse_versions_response(response))
        return available_versions

    def list_available_modules(self, org=None):
        parser = artifactory_parser()
        available_modules = []
        for repo in repo_list(self):
            response = requests.get(urljoin(repo, org))
            available_modules.extend(parser.parse_modules_response(response))
        return available_modules
