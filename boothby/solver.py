from ivy import module_descriptor
import logging
import revision_constraint

# we make our nodes in the graph classes
# such that they can yield specific versions
class module(object):
    # we can't ... unfortunately put configurations in here
    # .... because .... well ... the configurations can change over time
    def __init__(self, org, name, nav):
        self.id = org + "/" + name
        self.org = org
        self.name = name
        # initialize all our versions with nothing, so that
        # we know to initialize later
        self.all_versions = {
            x : None for x in nav.list_available_versions(org, name)
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
        self.constraints[ constraint ] = revision_constraint.make_constraint_functor(
            constraint
        )
        self.refresh_constrained_versions()

    def remove_constraint(self, constraint):
        del self.contraints[ constraint ]
        self.refresh_constrained_versions()

    def satisfied_versions(self, constraint):
        if type(constraint) is str:
            c = revision_constraint.make_constraint_functor(constraint)
        else:
            c = constraint
        return [
            ver for ver in self.all_versions.keys() if c(ver)
        ]

    def get_latest_module():
        version_to_module = self.constrained_versions.iteritems()[-1]
        if version_to_module[1] is None:
            version_to_module[1] = nav.get_module_descriptor(
                self.org,
                self.name,
                version_to_module[0]
            )
        return version_to_module[1]

    def get(self, version):
        if self.all_versions[version] is None:
            self.all_versions[version] = module_descriptor.from_string(
                self.nav.get_ivy_file(
                    self.org,
                    self.name,
                    version
                )
            )
        return self.all_versions[version]

def build_initial_graph_from_module(nav, root_module, modules):
    # module.revConstraint = module.rev
    for dep in root_module.dependencies:
        dep_id = dep.org + "/" + dep.name
        print dep_id
        if dep_id not in modules:
            modules[dep_id] = module(dep.org, dep.name, nav)

        modules[dep_id].add_constraint(dep.rev)
        satisfied_versions = modules[dep_id].satisfied_versions(dep.rev)
        while(satisfied_versions):
            best_candidate = satisfied_versions[-1]
            # print "candidate : " + dep_id + " " + best_candidate
            try:
                best_module = modules[dep_id].get(best_candidate)
                build_initial_graph_from_module(
                    nav,
                    best_module,
                    modules
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
                + "\n".join(modules[dep_id].versions())
            )
        else:
            # everything went okay
            pass
        # print dep_id + " suggested as " + best_candidate

def build_initial_graph(filename, nav):
    root = module_descriptor.from_file(filename)
    root_module = module( root.info.organisation, root.info.module, nav )
    modules = {root_module.id : root_module}
    build_initial_graph_from_module(
        nav,
        root,
        modules
    )
    return modules
