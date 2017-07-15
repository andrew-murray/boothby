import xml.etree.ElementTree as ET
from attrdict import AttrDict
import logging


def else_default(x, y):
    return y if x is None else x


def maybe_map(x, f):
    return f(x) if x is not None else None


"""

http://ant.apache.org/ivy/history/2.0.0/ivyfile/conf.html

+--------------+-----------------------------------------------------------------------------------------------+-------------------------+
|  Attribute   |                                     Description                                               |       Required          |
+--------------+-----------------------------------------------------------------------------------------------+-------------------------+
| name         | the name of the declared configuration                                                        |  Yes                    |
| description  | a description for the declared configuration                                                  |  No                     |
| visibility   | the visibility of the declared configuration. 'public' means that this configuration can      |                         |
|              | be used by other modules, while 'private' means that this configuration is used only in       |  No, defaults to public |
|              | the module itself, and is not exposed to other modules.                                       |                         |
| extends      | a comma separated list of configurations of this module that the current configuration extends|  No, defaults to none   |
| transitive   | a boolean to indicate if this conf is transitive or not since 1.4                             |  No, defaults to true   |
| deprecated   | indicates that this conf has been deprecated by giving the date of the deprecation.           |  No, by default the     |
|              | It should be given in this format: yyyyMMddHHmmss                                             |  conf is not deprecated |
+----------------------------------------------------------------------------------------------------------------------------------------+
"""


class conf(object):

    def __init__(
        self,
        name,
        description=None,
        visibility="public",
        extends=None,
        transitive=True,
        deprecated=None
    ):
        self.name = name
        self.description = description
        self.visibility = else_default(visibility, "public")
        self.extends = extends if extends else []
        self.transitive = else_default(transitive, True)
        self.deprecated = deprecated

    @staticmethod
    def from_node(node):
        return conf(
            node.get("name"),
            node.get("description"),
            node.get("visibility"),
            maybe_map(
                node.get("extends"),
                lambda k: [x.strip() for x in k.split(",")]
            ),
            node.get("transitive"),
            node.get("deprecated")
        )


"""
http://ant.apache.org/ivy/history/2.0.0/ivyfile/dependency.html

+---------------+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------------+
|   Attribute   |                                        Description                                                |                       Required                                  |
+---------------+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------------+
| org           | the name of the organisation of the dependency.                                                   | No, defaults to the master module organisation                  |
| name          | the module name of the dependency                                                                 | Yes                                                             |
| branch        | the branch of the dependency. since 1.4                                                           | No, defaults to the default branch setting for the dependency.  |
| rev           | the revision of the dependency. See above for details.                                            | Yes                                                             |
| revConstraint | the dynamic revision constraint originally used for this dependency. See above for details.       | No, defaults to the value of rev                                |
| force         | a boolean to give an indication to conflict manager that this dependency                          |                                                                 |
|               | should be forced to this revision (see conflicts manager)                                         | No, defaults to false                                           |                                                                                                                            |
| conf          | an inline mapping configuration spec (see above for details)                                      | No, defaults to defaultconf attribute of dependencies element   |
|               |                                                                                                   | if neither conf attribute nor conf children element is given    |
| transitive    | true to resolve this dependency transitively, false otherwise (since 1.2)                         | No, defaults to true                                            |
| changing      | true if the dependency artifacts may change without revision change, false otherwise (since 1.2). | No, defaults to false                                           |
|               | See cache and change management for details.                                                      |                                                                 |
+---------------+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------------+
"""


class dependency(object):

    def __init__(
        self,
        org,
        name,
        branch,
        rev,
        revConstraint,
        conf,
        force=False,
        transitive=True,
        changing=False
    ):
        self.org = org
        self.name = name
        self.branch = branch
        self.rev = rev
        self.revConstraint = revConstraint
        self.conf = conf
        self.force = else_default(force, False)
        self.transitive = else_default(transitive, True)
        self.changing = else_default(changing, False)

    @staticmethod
    def from_node(node):
        # at the moment, we canonicalise into a string representation
        # a little messy ... they should be canonicalised to
        # a set of mappings ?
        # lists of pairs of strings ?
        conf_nodes = list(node.findall("conf"))

        def parse_sub_conf(cn):
            src = cn.get("name")
            sub_mapped_nodes = list(cn.findall("mapped"))
            mapping_from_nodes = ",".join(
                mn.get("name") for mn in sub_mapped_nodes
            )
            mapping_from_attributes = cn.get("mapped")
            return (
                src + "->" + mapping_from_nodes
                + else_default(mapping_from_attributes, "")
            )


        conf_from_nodes=";".join(parse_sub_conf(cn) for cn in conf_nodes)
        conf_from_attr=else_default(node.get("conf"), "")

        if conf_from_attr and conf_from_nodes:
            conf=conf_from_attr + ";" + conf_from_nodes
        elif not conf_from_nodes and not conf_from_attr:
            conf=None
        else:
            # one of them is valid
            # concat without seperator ...
            # at least one of them will be an empty string
            conf=conf_from_attr + conf_from_nodes

        # we ignore some features
        # notably artifact, include, exclude
        # these three features are designed for "specifying an ivy structure
        # for a dependency that doesn't have an ivy file" ... this is obviosly
        # convenient, but I currently don't use this, and mimicking this
        # feature faithfully would rather complicate matters

        artifacts = list(node.findall("artifact"))
        includes = list(node.findall("include"))
        excludes = list(node.findall("exclude"))
        if artifacts or includes or excludes:
            logging.warning(
                "ira does not support artifact declarations "
                "inside dependencies. <artifact>, <include> and <exclude> "
                "will be ignored in this context."
            )

        return dependency(
            node.get("org"),
            node.get("name"),
            node.get("branch"),
            node.get("rev"),
            node.get("revConstraint"),
            conf,
            node.get("force"),
            node.get("transitive"),
            node.get("changing")
        )


"""
http://ant.apache.org/ivy/history/2.0.0/ivyfile/artifact.html

+-----------+---------------------------------------------------------------------------------------+-----------------------------------------------------------------------------+
| Attribute |                                      Description                                      |                                  Required                                   |
+-----------+---------------------------------------------------------------------------------------+-----------------------------------------------------------------------------+
| name      | the name of the published artifact. This name must not include revision.              | No, defaults to the name of the module                                      |
| type      | the type of the published artifact. It's usually its extension, but not necessarily.  | No, defaults to jar                                                         |
|           | For instance, ivy files are of type 'ivy' but have 'xml' extension                    |                                                                             |
| ext       | the extension of the published artifact                                               | No, defaults to type                                                        |
| conf      | comma separated list of public configurations in which this artifact is published.    |                                                                             |
|           | '*' wildcard can be used to designate all public configurations of this module        | No, defaults to defaultconf attribute value on parent publications element. |
| url       | a url at which this artifact can be found if it isn't located at the standard         | No, defaults to no url                                                      |
|           | location in the repository since 1.4                                                  |                                                                             |
+-----------+---------------------------------------------------------------------------------------+-----------------------------------------------------------------------------+
"""


class artifact(object):
    def __init__(
        self,
        name,
        type_,
        ext,
        conf,
        url
    ):
        self.name = name
        self.type = type_
        self.ext = ext
        self.conf = conf
        self.url = url

    @staticmethod
    def from_node(node):
        # publication supports child conf elements, to indicate how it has
        # been published, or as an attribute on the tag
        # this parse, should support both simultaneously, though this would
        # be a little silly
        child_configurations = list(
            subnode.get("name") for subnode in node.findall("conf")
        )
        attr_configurations = maybe_map(
            node.get("conf"),
            lambda k: [x.strip() for x in k.split(",")]
        )
        configurations = (
            child_configurations + else_default(attr_configurations, [])
        )
        return artifact(
            node.get("name"),
            node.get("type"),
            node.get("ext"),
            configurations,
            node.get("url")
        )


def parse_info(node):
    info = AttrDict({
        "license": maybe_map(node.find("license"), lambda n : n.attrib),
        "ivyauthor": maybe_map(node.find("ivyauthor"), lambda n : n.attrib),
        "repository": maybe_map(node.find("repository"), lambda n : n.attrib),
        "description": maybe_map(node.find("description"), lambda n : n.attrib)
    })
    return info + node.attrib


class ivy_module(object):
    @staticmethod
    def from_element_tree(root):
        info = parse_info(root.find("info"))
        config_section = root.find("configurations")
        configurations = [
            conf.from_node(x)
            for x in (config_section.findall("conf")
            if config_section is not None else [])
        ]
        dep_section = root.find("dependencies")
        dependencies = [
            dependency.from_node(x)
            for x in (dep_section.findall("dependency")
            if dep_section is not None else [])
        ]
        pub_section = root.find("publications")
        publications = [
            artifact.from_node(x)
            for x in (pub_section.findall("artifact")
            if pub_section is not None else [])
        ]

        return AttrDict({
            "info": info,
            "configurations": configurations,
            "dependencies": dependencies,
            "publications": publications
        })

    @staticmethod
    def from_string(text):
        tree = ET.fromstring(text)
        return ivy_module.from_element_tree(tree)

    @staticmethod
    def from_file(filename):
        tree = ET.parse(filename)
        return ivy_module.from_element_tree(tree.getroot())
