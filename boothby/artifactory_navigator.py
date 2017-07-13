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

    def parse_links(self, response):
        soup = bs4.BeautifulSoup(response, "lxml")

        def exclude_back(k):
            return ".." not in k["href"]

        links = filter(exclude_back, soup.find("body").find_all("a"))
        module_names = [x.text.replace(u"/", u"") for x in links]
        return module_names

    def parse_versions(self, response):
        return self.parse_links(response)

    def parse_modules(self, response):
        return self.parse_links(response)


class artifactory_navigator(navigator):

    def __init__(self, repository_list):
        self.repository_list = repository_list

    def list_available_versions(self, org, module):
        parser = artifactory_parser()
        available_versions = []
        for repo in self.repository_list:
            response = requests.get(urljoin(repo, org, module))
            available_versions.extend(parser.parse_versions(response))
        return available_versions

    def list_available_modules(self, org):
        parser = artifactory_parser()
        available_modules = []
        for repo in self.repository_list:
            response = requests.get(urljoin(repo, org))
            available_modules.extend(parser.parse_modules(response))
        return available_modules

    def get_ivy_file(self, org, module, version):
        for repo in self.repository_list:
            try:
                return requests.get(urljoin(repo, org, module, version))
            except Exception as e:
                continue
        raise Exception("Failed to find module")
