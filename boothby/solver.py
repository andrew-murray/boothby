import re
from ivy_module import ivy_module
import logging
from IPython.core.debugger import Tracer

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
        (c in mod) for c in "[]()+*"
    )

def make_constraint_functor(constraint):
    if rev_fixed(constraint):
        return lambda k : k == constraint
    else:
        raise Exception("Unsupported constraint \'" + constraint + "\'")

# we make our nodes in the graph classes
# such that they can yield specific versions
class graph_module(object):
    # we can't ... unfortunately put configurations in here
    # .... because .... well ... the configurations can change over time
    def __init__(self, org, module, nav):
        self.id = org + "/" + module
        self.org = org
        self.module = module
        # initialize all our versions with nothing, so that
        # we know to initialize later
        self.all_versions = {
            x : None for x in nav.list_available_versions(org, module)
        }

        self.constrained_versions = list( self.all_versions.keys() )

        self.constraints = {}

        self.nav = nav

    def versions(self):
        return self.all_versions.keys()

    def refresh_constrained_versions(self):
        self.constrained_versions = []
        for k in self.all_versions.keys():
            if all( f(k) for f in self.constraints.values() ):
                self.constrained_versions.append( k )

    def add_constraint(self, constraint):
        self.constraints[ constraint ] = make_constraint_functor( constraint )
        self.refresh_constrained_versions()

    def remove_constraint(self, constraint):
        del self.contraints[ constraint ]
        self.refresh_constrained_versions()

    def satisfied_versions(self, constraint):
        if type(constraint) is str:
            c = make_constraint_functor(constraint)
        else:
            c = constraint
        return [
            ver for ver in self.all_versions.keys() if c(ver)
        ]

    def get_latest_module():
        version_to_module = self.constrained_versions.iteritems()[-1]
        if version_to_module[1] is None:
            version_to_module[1] = nav.get_ivy_module(self.org,self.module, version_to_module[0])
        return version_to_module[1]

    def get(self, version):
        if self.all_versions[version] is None:
            self.all_versions[version] = ivy_module.from_string(self.nav.get_ivy_file(
                self.org,
                self.module,
                version
            ))
        return self.all_versions[version]

def build_initial_graph_from_module(nav, module, graph_modules):
    # module.revConstraint = module.rev
    for dep in module.dependencies:
        dep_id = dep.org + "/" + dep.name
        print dep_id
        if dep_id not in graph_modules:
            graph_modules[dep_id] = graph_module(dep.org, dep.name, nav)

        graph_modules[dep_id].add_constraint(dep.rev)
        satisfied_versions = graph_modules[dep_id].satisfied_versions(dep.rev)
        while(satisfied_versions):
            best_candidate = satisfied_versions[-1]
            print "candidate : " + dep_id + " " + best_candidate
            try:
                best_module = graph_modules[dep_id].get(best_candidate)
                build_initial_graph_from_module(
                    nav,
                    best_module,
                    graph_modules
                )
                break
            except Exception as e:
                # TODO: error message needs work
                print str(e)
                satisfied_versions.pop()
        if len(satisfied_versions) == 0:
            raise Exception(
                "Exhausted all satisfied versions when building initial graph "
                + " for \'" + dep_id + "\'. Tried versions:\n"
                + "\n".join(graph_modules[dep_id].versions())
            )
        else:
            # everything went okay
            pass
        print dep_id + " suggested as " + best_candidate

def build_initial_graph(filename, nav):
    root = ivy_module.from_file(filename)
    root_graph_module = graph_module( root.info.organisation, root.info.module, nav )
    return build_initial_graph_from_module(
        nav,
        root,
        {root_graph_module.id : root_graph_module}
    )
