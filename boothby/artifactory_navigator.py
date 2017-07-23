import logging
import warnings
import requests
from urlparse import urljoin
import abc
import bs4
import getpass
import keyring
import os

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
        self.module_map = {}


    def __get_with_401_retry(self, url):
        response = requests.get(
            url,
            auth = self.auth
        )
        if response.status_code == 401:
            self.auth = refresh_auth( error_pass_msg( response.status_code ) )
            response = requests.get(
                url,
                auth = self.auth
            )
            # just throw, if still error
            response.raise_for_status()
        return response

    def __ivy_url_factory(self, repo, org, module, version):
        return urljoin(repo, org) + "/" + module + "/" + version + "/ivy-" + version + ".xml"

    def list_available_versions(self, org, module):
        parser = artifactory_parser()
        available_versions = []
        for repo in self.repository_list:
            response = self.__get_with_401_retry(
                urljoin(repo, org) + "/" + module
            )
            # success!
            versions_in_repo = parser.parse_versions(response.text)
            for ver in versions_in_repo:
                self.module_map[ (org, module, version) ]= self.__ivy_url_factory(
                    repo,
                    org,
                    module,
                    ver
                )
            available_versions.extend(versions_in_repo)
        return available_versions

    def list_available_modules(self, org):
        parser = artifactory_parser()
        available_modules = []
        for repo in self.repository_list:
            response = self.__get_with_401_retry(
                urljoin(repo, org)
            )
            available_modules.extend(parser.parse_modules(response.text))
        return available_modules

    def list_available_publications(self, org, module, version):
        parser = artifactory_parser()
        last_exception = None
        pubs = []
        for repo in self.repository_list:
            response = self.__get_with_401_retry(
                urljoin(repo, org) + "/" + module + "/" + version
            )
            pubs.extend(parser.parse_links(response.text))
        return pubs

    def get_ivy_file(self, org, module, version):
        #FIXME The could not find module case is not very correct
        parser = artifactory_parser()
        last_exception = None
        if (org, module, version) in self.module_map:
            return self.__get_ivy_file( self.module_map[ (org, module, version) ] )
        for repo in self.repository_list:
            try:
                ivy_url = self.__ivy_url_factory(repo, org, module, version)
                response = self.__get_with_401_retry( ivy_url )
                response.raise_for_status()
                return response.text
            except Exception as e:
                last_exception = e
                continue
        raise Exception( "Couldn't find ivy file with last error being \'" + last_exception + "\'" )


class fileset_navigator(navigator):

    def __init__(self, directory_or_function):
        if type(directory_or_function) is str:
            self.directory = directory_or_function
        else:
            self.custom_path_former = directory_or_function

    def path_to_ivy(self,org,module,ver):
        return os.path.join(
            self.directory,
            "ivy-" + module + "-" + version + ".xml"
        )

    def contains(self,org,module,ver):
        return os.path.exists(
            self.path_to_ivy(org,module,ver)
        )

    def list_available_versions(self, org, module):
        """
            ignores org
        """
        # so we're going to lie a bit right now,
        # because the set of ivy files I have, has the module in the filename,
        # but not the org
        warnings.warn(
            "fileset_navigator.list_available_versions ignores provided org"
        )
        available_versions = []
        sw = "ivy-" + module + "-"
        # ivy-module-ver.xml
        # we presume our version has no dashes,
        # though it's fine in the module
        available_versions.extend([
            os.path.splitext(k)[0].split("-")[-1]
            for k in os.listdir(self.directory)
            if k.startswith(sw) and os.path.isfile(os.path.join(d,k))
        ])
        return available_versions

    def list_available_modules(self, org = None):
        """
            ignores org
        """
        warnings.warn(
            "fileset_navigator.list_available_modules ignores provided org"
        )

        available_modules = set()
        ivy_starter = "ivy-"
        all_things = os.listdir(d)
        available_modules.update(
            # this syntax is necessary, because the module can have
            # dashes, but we disallow it in the version
            "-".join( os.path.splitext(k)[0].split("-")[1:-1] )
            for k in os.listdir(self.directory)
            if k.startswith(ivy_starter) and os.path.isfile(os.path.join(d,k))
        )
        return available_modules

    def list_available_publications(self, org, module, version):
        raise Exception("Unimplemented")

    def get_ivy_file(self, org, module, version):
        """
            ignores org
        """
        warnings.warn(
            "fileset_navigator.get_ivy_file ignores provided org"
        )
        #FIXME The could not find module case is not very correct
        filename = path_to_ivy(org, module, version)
        if os.path.exists(filename):
            return open(filename).read()
        raise Exception( "Couldn't find ivy file \'" + filename + "\'." )

    def store_ivy_file(self,org,module,version,mod):
        """
            ignores org
        """
        warnings.warn(
            "fileset_navigator.get_ivy_file ignores provided org"
        )
        filename = path_to_ivy(org, module, version)
        with open(filename,'w') as op:
            op.write(mod)

def cached_artifactory_parser(navigator):
    def __init__(self, directory, repository_list):
        self.local = fileset_navigator(directory)
        self.art = artifactory_navigator(repository_list)
    def list_available_versions(self, org, module):
        return self.art.list_available_versions(org,module)
    def list_available_modules(self, org = None):
        return self.art.list_available_modules(org)
    def get_ivy_file(self, org, module, version):
        if not self.local.contains(org,module,version):
            module_file = self.art.get_ivy_file(org,module,version)
            self.local.store_ivy_file(org,module,version,module_file)
        return self.local.get_ivy_file(org,module,version)
