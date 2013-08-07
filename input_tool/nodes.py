import os
import operator
import itertools
import ConfigParser
from openquake.hazardlib.slots import with_slots
#import xml.etree.cElementTree as ET
from lxml import etree as ET
from keyword import iskeyword


def strip(tag):
    "Convert a (fully qualified) tag into a valid Python identifier"
    s = str(tag)
    pieces = s.rsplit('}', 1)
    if len(pieces) > 1:  # '}'
        s = pieces[1]
    if iskeyword(s):
        s += '_'
    return s


@with_slots
class Node(object):
    __slots__ = ('_tag', '_fulltag', '_attrib', '_value', '_nodes')

    def __init__(self, fulltag, attrib=None, value=None, nodes=None):
        self._tag = strip(fulltag)
        self._fulltag = fulltag
        self._attrib = {} if attrib is None else attrib
        self._value = value
        self._nodes = [] if nodes is None else nodes

    def __getattr__(self, name):
        subnodes = self.getnodes(name)
        if len(subnodes) == 0:
            raise NameError('No subnode named %r found in %r' %
                            (name, self._tag))
        elif len(subnodes) > 1:
            raise ValueError(
                'There are several subnodes named %r in %r' %
                (name, self._tag))
        return subnodes[0]

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
            return

        subnodes = self.getnodes(name)
        if len(subnodes) == 0:
            raise NameError('No subnode named %r found in %r' %
                            (name, self._tag))
        elif len(subnodes) > 1:
            raise ValueError(
                'There are several subnodes named %r in %r, '
                'cannot extract a value' % (name, self._tag))

        node = subnodes[0]
        if not isinstance(value, Node):
            raise TypeError('%r is not of type Node' % value)
        for i, node in enumerate(self):
            if node._tag == name:
                self._nodes[i] = value

    def getnodes(self, name):
        "Return the direct subnodes with name 'name'"
        subnodes = []
        for node in self._nodes:
            if node._tag == name:
                subnodes.append(node)
        return subnodes

    def getgroups(self):
        "Returns the direct subnodes grouped by tag"
        gb = itertools.groupby(self._nodes, operator.attrgetter('_tag'))
        return [list(g) for k, g in gb]

    def __iter__(self):
        return iter(self._nodes)

    def __repr__(self):
        return '<%s %s %s %s>' % (self._tag, self._attrib, self._value,
                                  self._nodes)

    def to_xml(self):
        return ET.tostring(to_elem(self), pretty_print=True)


# inspired by https://gist.github.com/651801
def to_elem(node):
    def generate_elem(append, node, level):
        var = "e" + str(level)
        arg = repr(node._fulltag)
        if node._attrib:
            arg += ", **%r" % node._attrib
        if level == 1:
            append("e1 = Element(%s)" % arg)
        else:
            append("%s = SubElement(e%d, %s)" % (var, level - 1, arg))
        if not node._nodes:
            append("%s.text = %r" % (var, node._value))
        for x in node:
            generate_elem(append, x, level + 1)
    # generate code to create a tree
    output = []
    generate_elem(output.append, node, 1)
    # print "\n".join(output)
    namespace = {"Element": ET.Element, "SubElement": ET.SubElement}
    exec "\n".join(output) in namespace
    return namespace["e1"]


def from_elem(elem):
    children = list(elem)
    if not children:
        return Node(elem.tag, elem.attrib, elem.text)
    return Node(elem.tag, elem.attrib, nodes=map(from_elem, children))


def from_ini(ini_file):
    cfp = ConfigParser.RawConfigParser()
    with open(ini_file) as f:
        cfp.readfp(f)
    root = Node(os.path.basename(ini_file))
    sections = cfp.sections()
    for section in sections:
        params = dict(cfp.items(section))
        node = Node(section, params)
        root._nodes.append(node)
    return root


def to_ini(node):
    ls = []
    for subnode in node:
        ls.append('\n[%s]' % subnode._tag)
        for name, value in sorted(subnode._attrib.iteritems()):
            ls.append('%s=%s' % (name, value))
    return '\n'.join(ls)


def displayattrs(attrib, expandattrs):
    if not attrib:
        return ''
    if expandattrs:
        alist = ['%s=%s' % (strip(k), v) for (k, v) in attrib.iteritems()]
    else:
        alist = map(strip, attrib)
    return '{%s}' % ', '.join(alist)


def _display(node, indent, expandattrs, expandvals):
    attrs = displayattrs(node._attrib, expandattrs)
    val = ' ' + (node._value if (expandvals and node._value) else '')
    print indent + node._tag + attrs + val
    for sub_node in node:
        _display(sub_node, indent + '   ', expandattrs, expandvals)


def display(root, expandattrs=False, expandvals=False):
    _display(root, '', expandattrs, expandvals)


#from nrml_schema import get_schema


def parse_nrml(dirname, fname):
    fullname = os.path.join(dirname, fname)
    #validator = ET.XMLSchema(get_schema())
    parsed = ET.parse(fullname, ET.ETCompatXMLParser())
    #validator.assertValid(parsed)
    root = from_elem(parsed.getroot())
    model = root._nodes[0]
    modeltype = model._tag
    return model, modeltype


def test():
    n1 = Node('item1', {}, 'value1')
    n2 = Node('item2', {}, 'value2')
    n3 = Node('empty')
    n4 = Node('empty')
    n0 = Node('body', {'a': 1, 'b': 2}, nodes=[n1, n2, n3, n4])
    print n0
    e0 = to_elem(n0)
    ET.dump(e0)
    print n0.item1
    print n0.getnodes('empty')
    n5 = Node('body', {}, nodes=[n3])
    print n5, n5._nodes
    n0.item1 = n4
    n6 = Node('root', {}, nodes=[n0])
    print n6.body
    n6.body = n1
    print n6


def test_parse():
    root = ET.parse('/home/michele/oq-nrmllib/examples/'
                    'vulnerability-model-discrete.xml').getroot()
    node = from_elem(root)
    display(node, expandattrs=True)
    sets = node.vulnerabilityModel.getnodes('discreteVulnerabilitySet')
    vuln = sets[0].getnodes('discreteVulnerability')[0]
    print vuln.lossRatio._value


def test_schema():
    root = ET.parse('/home/michele/oq-nrmllib/openquake/nrmllib/schema/risk/'
                    'vulnerability.xsd').getroot()
    node = from_elem(root)
    display(node, expandattrs=True)


def test_pickle():
    import cPickle as p
    n1 = Node('item1', {}, 'value1')
    n1.assert_equal(p.loads(p.dumps(n1)))


def test_from_ini():
    root = from_ini('/home/michele/md/gem/CITYC-EB/job_haz.ini')
    display(root)
