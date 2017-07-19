from .import_context import boothby
from boothby.ivy import module_descriptor
import unittest
import copy

TEST_FILE = "tests/data/official_sample.xml"


class parse_module_test(unittest.TestCase):

    def setUp(self):
        self.parsed_module = module_descriptor.from_file(TEST_FILE)

    def test_configurations(self):
        assert len(self.parsed_module.configurations) == 5
        """
    		<conf name="myconf1" description="desc 1"/>
    		<conf name="myconf2" description="desc 2" visibility="public"/>
    		<conf name="myconf3" description="desc 3" visibility="private"/>
    		<conf name="myconf4" description="desc 4" extends="myconf1, myconf2"/>
    		<conf name="myoldconf" description="my old desc" deprecated="20050115"/>
        """
        correct_configurations = [
            {
                'name': 'myconf1',
                'deprecated': None,
                'extends': [],
                'transitive': True,
                'visibility': "public",
                'description': 'desc 1'
            },
            {
                'name': 'myconf2',
                'deprecated': None,
                'extends': [],
                'transitive': True,
                'visibility': 'public',
                'description': 'desc 2'
            },
            {
                'name': 'myconf3',
                'deprecated': None,
                'extends': [],
                'transitive': True,
                'visibility': 'private',
                'description': 'desc 3'
            },
            {
                'name': 'myconf4',
                'deprecated': None,
                'extends': ["myconf1", "myconf2"],
                'transitive': True,
                'visibility': "public",
                'description': 'desc 4'
            },
            {
                'name': 'myoldconf',
                'deprecated': '20050115',
                'extends': [],
                'transitive': True,
                'visibility': "public",
                'description': 'my old desc'
            }
        ]

        conf_dicts = [vars(x) for x in self.parsed_module.configurations]
        for correct, parsed in zip( correct_configurations, conf_dicts):
            assert correct == parsed

    def test_publications(self):
        assert len(self.parsed_module.publications) == 4
        """
        	<artifact name="myartifact1" type="jar"/>
        	<artifact name="myartifact2" type="jar" conf="myconf1"/>
        	<artifact name="myartifact3" type="jar" conf="myconf1, myconf2, myconf3"/>
        	<artifact name="myartifact4" type="jar">
        		<conf name="myconf1"/>
        		<conf name="myconf3"/>
        	</artifact>
        """
        correct_publications = [
            {
                'url': None,
                'ext': None,
                'type': 'jar',
                'name': 'myartifact1',
                'conf': []
            },
            {
                'url': None,
                'ext': None,
                'type': 'jar',
                'name': 'myartifact2',
                'conf': ['myconf1']
            },
            {
                'url': None,
                'ext': None,
                'type': 'jar',
                'name': 'myartifact3',
                'conf': ['myconf1', 'myconf2', 'myconf3']
            },
            {
                'url': None,
                'ext': None,
                'type': 'jar',
                'name': 'myartifact4',
                'conf': ['myconf1', 'myconf3']
            }
        ]

        zipped = zip(
            correct_publications,
            self.parsed_module.publications
        )
        for correct, parsed in zipped:
            assert correct == vars(parsed)

    def test_dependencies(self):
        assert len(self.parsed_module.dependencies) == 11
        """
    		<dependency name="mymodule2" rev="2.0"/>
    		<dependency org="yourorg" name="yourmodule1" rev="1.1" conf="myconf1"/>
    		<dependency org="yourorg" name="yourmodule2" rev="2+" conf="myconf1->yourconf1"/>
    		<dependency org="yourorg" name="yourmodule3" rev="3.1" conf="myconf1->yourconf1, yourconf2"/>
    		<dependency org="yourorg" name="yourmodule4" rev="4.1" conf="myconf1, myconf2->yourconf1, yourconf2"/>
    		<dependency org="yourorg" name="yourmodule5" rev="5.1" conf="myconf1->yourconf1;myconf2->yourconf1, yourconf2"/>

    		<dependency org="yourorg" name="yourmodule6" rev="latest.integration">
    			<conf name="myconf1" mapped="yourconf1"/>
    			<conf name="myconf2" mapped="yourconf1, yourconf2"/>
    		</dependency>

    		<dependency org="yourorg" name="yourmodule7" rev="7.1">
    			<conf name="myconf1">
    				<mapped name="yourconf1"/>
    			</conf>
    			<conf name="myconf2">
    				<mapped name="yourconf1"/>
    				<mapped name="yourconf2"/>
    			</conf>
    		</dependency>

    		<dependency org="yourorg" name="yourmodule8" rev="8.1">
    			<artifact name="yourartifact8-1" type="jar"/>
    			<artifact name="yourartifact8-2" type="jar"/>
    		</dependency>

    		<dependency org="yourorg" name="yourmodule9" rev="9.1" conf="myconf1,myconf2,myconf3->default">
    			<artifact name="yourartifact9-1" type="jar" conf="myconf1,myconf2"/>
    			<artifact name="yourartifact9-2" type="jar">
    				<conf name="myconf2"/>
    				<conf name="myconf3"/>
    			</artifact>
    		</dependency>

    		<dependency org="yourorg" name="yourmodule10" rev="10.1">
    			<include name="your.*" type="jar"/>
    			<include ext="xml"/>
    			<exclude name="toexclude"/>
    		</dependency>
        """

        default_dep = {
            'force': False,
            'conf': None,
            "revConstraint": None,
            "branch": None,
            "changing": False,
            "transitive": True,
            "org": None
        }

        def dep(y):
            to_mutate = copy.deepcopy(default_dep)
            to_mutate.update(y)
            return to_mutate

        # FIXME: Fundamentally, we don't support all the things
        # associated with dependency tags, in particular when you
        # specify the ivy structure for an external, this will be ignored
        # this is a known limitation, and the below test regresses this
        # behaviour
        correct_dependencies = [
            dep({
                'name': 'mymodule2',
                'rev': '2.0'
            }),
            dep({
                'name': 'yourmodule1',
                'conf': 'myconf1',
                'rev': '1.1',
                'org': 'yourorg'
            }),
            dep({
                'name': 'yourmodule2',
                'conf': 'myconf1->yourconf1',
                'rev': '2+',
                'org': 'yourorg'
            }),
            dep({
                'name': 'yourmodule3',
                'conf': 'myconf1->yourconf1, yourconf2',
                'rev': '3.1',
                'org': 'yourorg'
            }),
            dep({
                'name': 'yourmodule4',
                'conf': 'myconf1, myconf2->yourconf1, yourconf2',
                'rev': '4.1',
                'org': 'yourorg'
            }),
            dep({
                'name': 'yourmodule5',
                'conf': 'myconf1->yourconf1;myconf2->yourconf1, yourconf2',
                'rev': '5.1',
                'org': 'yourorg'
            }),
            dep({
                'name': 'yourmodule6',
                'rev': 'latest.integration',
                'org': 'yourorg',
                'conf': "myconf1->yourconf1;myconf2->yourconf1, yourconf2"
            }),
            dep({
                'name': 'yourmodule7',
                'rev': '7.1',
                'org': 'yourorg',
                'conf': "myconf1->yourconf1;myconf2->yourconf1,yourconf2"
            }),
            dep({
                'name': 'yourmodule8',
                'rev': '8.1',
                'org': 'yourorg'
            }),
            dep({
                'name': 'yourmodule9',
                'conf': 'myconf1,myconf2,myconf3->default',
                'rev': '9.1',
                'org': 'yourorg'
            }),
            dep({
                'name': 'yourmodule10',
                'rev': '10.1',
                'org': 'yourorg'
            })
        ]

        for correct, parsed in zip(correct_dependencies, self.parsed_module.dependencies):
            assert correct == vars(parsed)
