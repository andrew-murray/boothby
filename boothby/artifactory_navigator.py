import requests
from urlparse import urljoin
import abc
import bs4
import getpass
import keyring

class navigator(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def list_available_versions(self, module):
        pass

    @abc.abstractmethod
    def list_available_modules(self):
        pass


class artifactory_parser(object):

    def parse_links(self, response_text):
        soup = bs4.BeautifulSoup(response_text, "lxml")
        def exclude_back(k):
            return ".." not in k["href"]

        links = filter(exclude_back, soup.find("body").find_all("a"))
        module_names = [x.text.replace(u"/", u"") for x in links]
        return module_names

    def parse_versions(self, response_text):
        return self.parse_links(response_text)

    def parse_modules(self, response_text):
        return self.parse_links(response_text)

def refresh_auth(msg, override = True):
    user = getpass.getuser()
    # if override, we don't trust the cache
    password = keyring.get_password("art_nav", user) if not override else None
    if not password:
        password = getpass.getpass(msg)
        keyring.set_password("art_nav", user, password)
    return (user,password)

DEFAULT_PASS_MSG = "Please supply password for artifactory :"

def error_pass_msg(status):
    return "Encountered status code " + str(status) + ". Password incorrect?\n" + DEFAULT_PASS_MSG

class artifactory_navigator(navigator):

    def __init__(self, repository_list, auth = None):
        self.repository_list = repository_list
        if not auth:
            self.auth = refresh_auth(DEFAULT_PASS_MSG, False)
        else:
            self.auth = auth

    def list_available_versions(self, org, module):
        parser = artifactory_parser()
        available_versions = []
        for repo in self.repository_list:
            response = requests.get(urljoin(repo, org) + "/" + module, auth = self.auth)
            if response.status_code == 401:
                self.auth = refresh_auth( error_pass_msg( response.status_code ) )
                response = requests.get(urljoin(repo, org) + "/" + module, auth = self.auth)
                # just throw, if still error
                response.raise_for_status()
                
            available_versions.extend(parser.parse_versions(response.text))
        return available_versions

    def list_available_modules(self, org):
        parser = artifactory_parser()
        available_modules = []
        for repo in self.repository_list:
            response = requests.get(urljoin(repo, org), auth = self.auth)
            if response.status_code == 401:
                self.auth = refresh_auth( error_pass_msg( response.status_code ) )
                response = requests.get(urljoin(repo, org), auth = self.auth)
                # just throw, if still error
                response.raise_for_status()
            available_modules.extend(parser.parse_modules(response.text))
        return available_modules
    
    def list_available_publications(self, org, module, version):
        parser = artifactory_parser()
        last_exception = None
        pubs = []
        for repo in self.repository_list:
            response = requests.get(urljoin(repo, org) + "/" + module + "/" + version, auth = self.auth)
            if response.status_code == 401:
                self.auth = refresh_auth( error_pass_msg( response.status_code ) )
                response = requests.get(urljoin(repo, org) + "/" + module + "/" + version, auth = self.auth)
                # just throw, if still error
                response.raise_for_status()
            pubs.extend(parser.parse_links( response.text ))
        return pubs
    
    def get_ivy_file(self, org, module, version):
        #FIXME The could not find module case is not very correct
        parser = artifactory_parser()
        last_exception = None
        for repo in self.repository_list:
            try:
                response = requests.get(urljoin(repo, org) + "/" + module + "/" + version + "/ivy-" + version + ".xml", auth = self.auth)
                if response.status_code == 401:
                    self.auth = refresh_auth( error_pass_msg( response.status_code ) )
                    response = requests.get(urljoin(repo, org) + "/" + module + "/" + version + "/ivy-" + version + ".xml", auth = self.auth)
                    # just throw, if still error
                    response.raise_for_status()
                return response.text
            except Exception as e:
                last_exception = e
                continue
        raise Exception( "Couldn't find ivy file with last error being \'" + last_exception + "\'" )
