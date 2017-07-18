import re
from ivy_module import ivy_module

# let's assume for now, I've been given a file


def pkey(mod):
    return mod.org + "/" + mod.name


# X.Y.Z
# X.Y.Z_N
# This regex, only matches fixed revisions of the above format
# .... how do you turn it into a regex which also matches
# supported dynamic revisions?
ivy_regex = re.compile(r"^([0-9]+\.)+[0-9]+(?:_[0-9]+)?$")

def rev_fixed(mod):
    # the characters being checked, are those associated with dynamic
    #  revisions in ivy
    return ivy_regex.match(mod) or not any(
        (c in chars) for c in "[]()+*"
    )

node_properties = {
    id : org + "/" + module_name,
    version: "",
    url : "",
    configurations :
}

# we make our nodes in the graph classes
# such that they can yield specific versions
class graph_module(object):
    id = "com.tmvse.vis/Origami"
    available_versions = {
        "version" : "ivy_module"
    }
    # we can't ... unfortunately put configurations in here
    # .... because .... well ... the configurations can change over time
    def __init__(self, org, module, nav):
        self.id = org + "/" + module
        self.org = org
        self.module = module
        # initialize all our versions with nothing, so that
        # we know to initialize later
        self.all_versions = {
            x : None for x in nav.get_available_versions(org, module)
        }

    def versions(self):
        return self.all_versions.keys()

def build_initial_graph(filename, nav):
    root_module = ivy_module.from_file(filename)
    resolved_modules = {}
    unresolved_modules = [root_module]

    while unresolved_modules:
        next_module = unresolved_modules.pop()
        dependencies = next_module.dependencies

        # fixme, this is network IO, ... and parsing ...
        # should really be parallel....
        # or at least the api should 'allow' the navigator to parallelise

        deps_to_resolve = [
            dep
            for dep in dependencies
            if pkey(dep) not in resolved_modules.keys()
        ]

        all_versions = [
            nav.list_available_versions(dep.org, dep.name)
            for dep in deps_to_resolve
        ]

        for available_versions, dep in zip(all_versions,deps_to_resolve):
            print dep.org + "/" + dep.name
            print available_versions
