#!/usr/bin/env python
#
# Copyright (C) 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# This module is used for version 2 of the Google Data APIs.


__author__ = 'j.s@google.com (Jeff Scudder)'


import unittest
import lxml.etree as ElementTree
import atom.core
import gdata.test_config as conf 


SAMPLE_XML = (b'<outer xmlns="http://example.com/xml/1" '
                    b'xmlns:two="http://example.com/xml/2">'
                b'<inner x="123"/>'
                b'<inner x="234" y="abc"/>'
                b'<inner>'
                  b'<two:nested>Some Test</two:nested>'
                  b'<nested>Different Namespace</nested>'
                b'</inner>'
                b'<other two:z="true"></other>'
              b'</outer>')


NO_NAMESPACE_XML = ('<foo bar="123"><baz>Baz Text!</baz></foo>')


V1_XML = ('<able xmlns="http://example.com/1" '
               'xmlns:ex="http://example.com/ex/1">'
            '<baker foo="42"/>'
            '<ex:charlie>Greetings!</ex:charlie>'
            '<same xmlns="http://example.com/s" x="true">'
          '</able>')


V2_XML = ('<alpha xmlns="http://example.com/2" '
               'xmlns:ex="http://example.com/ex/2">'
            '<bravo bar="42"/>'
            '<ex:charlie>Greetings!</ex:charlie>'
            '<same xmlns="http://example.com/s" x="true">'
          '</alpha>')


class Child(atom.core.XmlElement):
  _qname = ('{http://example.com/1}child', '{http://example.com/2}child')


class Foo(atom.core.XmlElement):
  _qname = 'foo'


class Example(atom.core.XmlElement):
  _qname = '{http://example.com}foo'
  child = Child
  foos = [Foo]
  tag = 'tag'
  versioned_attr = ('attr', '{http://new_ns}attr')


# Example XmlElement subclass declarations.
class Inner(atom.core.XmlElement):
  _qname = '{http://example.com/xml/1}inner'
  my_x = 'x'


class Outer(atom.core.XmlElement):
  _qname = '{http://example.com/xml/1}outer'
  innards = [Inner]


class XmlElementTest(unittest.TestCase):

  def testGetQName(self):
    class Unversioned(atom.core.XmlElement):
      _qname = '{http://example.com}foo'

    class Versioned(atom.core.XmlElement):
      _qname = ('{http://example.com/1}foo', '{http://example.com/2}foo') 

    self.assert_(
        atom.core._get_qname(Unversioned, 1) == '{http://example.com}foo')
    self.assert_(
        atom.core._get_qname(Unversioned, 2) == '{http://example.com}foo')
    self.assert_(
        atom.core._get_qname(Versioned, 1) == '{http://example.com/1}foo')
    self.assert_(
        atom.core._get_qname(Versioned, 2) == '{http://example.com/2}foo')

  def testConstructor(self):
    e = Example()
    self.assert_(e.child is None)
    self.assert_(e.tag is None)
    self.assert_(e.versioned_attr is None)
    self.assert_(e.foos == [])
    self.assert_(e.text is None)
        
  def testGetRules(self):
    rules1 = Example._get_rules(1)
    self.assert_(rules1[0] == '{http://example.com}foo')
    self.assert_(rules1[1]['{http://example.com/1}child'] == ('child', Child, 
        False))
    self.assert_(rules1[1]['foo'] == ('foos', Foo, True))
    self.assert_(rules1[2]['tag'] == 'tag')
    self.assert_(rules1[2]['attr'] == 'versioned_attr')
    # Check to make sure we don't recalculate the rules.
    self.assert_(rules1 == Example._get_rules(1))
    rules2 = Example._get_rules(2)
    self.assert_(rules2[0] == '{http://example.com}foo')
    self.assert_(rules2[1]['{http://example.com/2}child'] == ('child', Child, 
        False))
    self.assert_(rules2[1]['foo'] == ('foos', Foo, True))
    self.assert_(rules2[2]['tag'] == 'tag')
    self.assert_(rules2[2]['{http://new_ns}attr'] == 'versioned_attr')
    
  def testGetElements(self):
    e = Example()
    e.child = Child()
    e.child.text = 'child text'
    e.foos.append(Foo())
    e.foos[0].text = 'foo1'
    e.foos.append(Foo())
    e.foos[1].text = 'foo2'
    e._other_elements.append(atom.core.XmlElement())
    e._other_elements[0]._qname = 'bar'
    e._other_elements[0].text = 'other1'
    e._other_elements.append(atom.core.XmlElement())
    e._other_elements[1]._qname = 'child'
    e._other_elements[1].text = 'other2'
    
    self.contains_expected_elements(e.get_elements(), 
        ['foo1', 'foo2', 'child text', 'other1', 'other2'])
    self.contains_expected_elements(e.get_elements('child'), 
        ['child text', 'other2'])
    self.contains_expected_elements(
        e.get_elements('child', 'http://example.com/1'), ['child text'])
    self.contains_expected_elements(
        e.get_elements('child', 'http://example.com/2'), [])
    self.contains_expected_elements(
        e.get_elements('child', 'http://example.com/2', 2), ['child text'])
    self.contains_expected_elements(
        e.get_elements('child', 'http://example.com/1', 2), [])
    self.contains_expected_elements(
        e.get_elements('child', 'http://example.com/2', 3), ['child text'])
    self.contains_expected_elements(e.get_elements('bar'), ['other1'])
    self.contains_expected_elements(e.get_elements('bar', version=2), 
        ['other1']) 
    self.contains_expected_elements(e.get_elements('bar', version=3), 
        ['other1']) 
    
  def contains_expected_elements(self, elements, expected_texts):
    self.assert_(len(elements) == len(expected_texts))
    for element in elements:
      self.assert_(element.text in expected_texts)

  def testConstructorKwargs(self):
    e = Example('hello', child=Child('world'), versioned_attr='1')
    self.assert_(e.text == 'hello')
    self.assert_(e.child.text == 'world')
    self.assert_(e.versioned_attr == '1')
    self.assert_(e.foos == [])
    self.assert_(e.tag is None)

    e = Example(foos=[Foo('1', ignored=1), Foo(text='2')], tag='ok')
    self.assert_(e.text is None)
    self.assert_(e.child is None)
    self.assert_(e.versioned_attr is None)
    self.assert_(len(e.foos) == 2)
    self.assert_(e.foos[0].text == '1')
    self.assert_(e.foos[1].text == '2')
    self.assert_('ignored' not in e.foos[0].__dict__)
    self.assert_(e.tag == 'ok')
  
  def testParseBasicXmlElement(self):
    element = atom.core.xml_element_from_string(SAMPLE_XML, 
        atom.core.XmlElement)
    inners = element.get_elements('inner')
    self.assert_(len(inners) == 3)
    self.assert_(inners[0].get_attributes('x')[0].value == '123')
    self.assert_(inners[0].get_attributes('y') == [])
    self.assert_(inners[1].get_attributes('x')[0].value == '234')
    self.assert_(inners[1].get_attributes('y')[0].value == 'abc')
    self.assert_(inners[2].get_attributes('x') == [])
    inners = element.get_elements('inner', 'http://example.com/xml/1')
    self.assert_(len(inners) == 3)
    inners = element.get_elements(None, 'http://example.com/xml/1')
    self.assert_(len(inners) == 4)
    inners = element.get_elements()
    self.assert_(len(inners) == 4)
    inners = element.get_elements('other')
    self.assert_(len(inners) == 1)
    self.assert_(inners[0].get_attributes(
        'z', 'http://example.com/xml/2')[0].value == 'true')
    inners = element.get_elements('missing')
    self.assert_(len(inners) == 0)

  def testBasicXmlElementPreservesMarkup(self):
    element = atom.core.xml_element_from_string(SAMPLE_XML,
        atom.core.XmlElement)
    tree1 = ElementTree.fromstring(SAMPLE_XML)
    tree2 = ElementTree.fromstring(element.to_string())
    self.assert_trees_similar(tree1, tree2)

  def testSchemaParse(self):
    outer = atom.core.xml_element_from_string(SAMPLE_XML, Outer)
    self.assert_(isinstance(outer.innards, list))
    self.assert_(len(outer.innards) == 3)
    self.assert_(outer.innards[0].my_x == '123')

  def testSchemaParsePreservesMarkup(self):
    outer = atom.core.xml_element_from_string(SAMPLE_XML, Outer)
    tree1 = ElementTree.fromstring(SAMPLE_XML)
    tree2 = ElementTree.fromstring(outer.to_string())
    self.assert_trees_similar(tree1, tree2)
    found_x_and_y = False
    found_x_123 = False
    child = tree1.find('{http://example.com/xml/1}inner')
    matching_children = tree2.findall(child.tag)
    for match in matching_children:
      if 'y' in match.attrib and match.attrib['y'] == 'abc':
        if match.attrib['x'] == '234':
          found_x_and_y = True
        self.assert_(match.attrib['x'] == '234')
      if 'x' in match.attrib and match.attrib['x'] == '123':
        self.assert_('y' not in match.attrib)
        found_x_123 = True
    self.assert_(found_x_and_y)
    self.assert_(found_x_123)
    
  def assert_trees_similar(self, a, b):
    """Compares two XML trees for approximate matching."""
    for child in a:
      self.assert_(len(a.findall(child.tag)) == len(b.findall(child.tag)))
    for child in b:
      self.assert_(len(a.findall(child.tag)) == len(b.findall(child.tag)))
    self.assert_(len(a) == len(b))
    self.assert_(a.text == b.text)
    self.assert_(a.attrib == b.attrib)


class UtilityFunctionTest(unittest.TestCase):

  def testMatchQnames(self):
    self.assert_(atom.core._qname_matches(
        'foo', 'http://example.com', '{http://example.com}foo'))
    self.assert_(atom.core._qname_matches(
        None, None, '{http://example.com}foo'))
    self.assert_(atom.core._qname_matches(
        None, None, 'foo'))
    self.assert_(atom.core._qname_matches(
        None, None, None))
    self.assert_(atom.core._qname_matches(
        None, None, '{http://example.com}'))
    self.assert_(atom.core._qname_matches(
        'foo', None, '{http://example.com}foo'))
    self.assert_(atom.core._qname_matches(
        None, 'http://example.com', '{http://example.com}foo'))
    self.assert_(atom.core._qname_matches(
        None, '', 'foo'))
    self.assert_(atom.core._qname_matches(
        'foo', '', 'foo'))
    self.assert_(atom.core._qname_matches(
        'foo', '', 'foo'))
    self.assert_(atom.core._qname_matches(
        'foo', 'http://google.com', '{http://example.com}foo') == False)
    self.assert_(atom.core._qname_matches(
        'foo', 'http://example.com', '{http://example.com}bar') == False)
    self.assert_(atom.core._qname_matches(
        'foo', 'http://example.com', '{http://google.com}foo') == False)
    self.assert_(atom.core._qname_matches(
        'bar', 'http://example.com', '{http://google.com}foo') == False)
    self.assert_(atom.core._qname_matches(
        'foo', None, '{http://example.com}bar') == False)
    self.assert_(atom.core._qname_matches(
        None, 'http://google.com', '{http://example.com}foo') == False)
    self.assert_(atom.core._qname_matches(
        None, '', '{http://example.com}foo') == False)
    self.assert_(atom.core._qname_matches(
        'foo', '', 'bar') == False)


class Chars(atom.core.XmlElement):
  _qname = '{http://example.com/}chars'
  y = 'y'
  alpha = 'a'


class Strs(atom.core.XmlElement):
  _qname = '{http://example.com/}strs'
  chars = [Chars]
  delta = 'd'


def parse(string):
  return atom.core.xml_element_from_string(string, atom.core.XmlElement)


def create(tag, string):
  element = atom.core.XmlElement(text=string)
  element._qname = tag
  return element


class CharacterEncodingTest(unittest.TestCase):

  def testUTF16InputString(self):
    # Test parsing the inner text.
    self.assertEqual(parse('<x>&#948;</x>'.encode('utf-16')).text, '\u03b4')
    self.assertEqual(parse('<x>\u03b4</x>'.encode('utf-16')).text, '\u03b4')

    # Test output valid XML.
    self.assertEqual(parse('<x>&#948;</x>'.encode('utf-16')).to_string(), '<x>\u03b4</x>')
    self.assertEqual(parse('<x>\u03b4</x>'.encode('utf-16')).to_string(), '<x>\u03b4</x>')

    # Test setting the inner text and output valid XML.
    e = create('x', '\u03b4')
    self.assertEqual(e.to_string(), '<x>\u03b4</x>')
    self.assertEqual(e.text, '\u03b4')
    self.assert_(isinstance(e.text, str))
    self.assertEqual(create('x', b'\xce\xb4'.decode('utf-8')).to_string(),
                     '<x>\u03b4</x>')

  def testUTF16TagsAndAttributes(self):
    # Begin with test to show underlying ElementTree behavior.
    t = ElementTree.fromstring('<del\u03b4ta>test</del\u03b4ta>'.encode('utf-8'))
    self.assertEqual(t.tag, 'del\u03b4ta')
    self.assertEqual(parse('<\u03b4elta>test</\u03b4elta>'.encode('utf-16'))._qname,
                     '\u03b4elta')
    
    # Test unicode attribute names and values.
    t = ElementTree.fromstring('<x \u03b4a="\u03b4b" />'.encode('utf-8'))
    self.assertEqual(t.attrib, {'\u03b4a': '\u03b4b'})
    self.assertEqual(parse('<x \u03b4a="\u03b4b" />'.encode('utf-16')).get_attributes(
        '\u03b4a')[0].value, '\u03b4b')
    x = create('x', None)
    x._other_attributes['a'] = '\u03b4elta'
    self.assert_(x.to_string().startswith('<x a="\u03b4elta"'))

  def testUtf8InputString(self):
    # Test parsing inner text.
    self.assertEqual(parse('<x>&#948;</x>'.encode('utf-16')).text, '\u03b4')
    self.assertEqual(parse('<x>\u03b4</x>'.encode('utf-8')).text, '\u03b4')
#    self.assertEqual(parse(b'<x>\xce\xb4</x>'.encode('utf-16')).text, '\u03b4')

    # Test output valid XML.
    self.assertEqual(parse('<x>&#948;</x>'.encode('utf-16')).to_string(), '<x>\u03b4</x>')
    self.assertEqual(parse('<x>\u03b4</x>'.encode('utf-8')).to_string(), '<x>\u03b4</x>')
#    self.assertEqual(parse('<x>\xce\xb4</x>'.encode('utf-16')).to_string(), '<x>&#948;</x>')

#    # Test setting the inner text and output valid XML.
#    e = create('x', b'\xce\xb4'.decode('utf-8'))
#    self.assertEqual(e.to_string(), '<x>&#948;</x>')
#    # Don't change the encoding until the we convert to an XML string.
#    self.assertEqual(e.text, '\xce\xb4')
#    self.assert_(isinstance(e.text, str))
#    self.assert_(isinstance(e.to_string(), str))
##    self.assertEqual(create('x', '\u03b4'.encode('utf-8')).to_string(),
##                     b'<x>&#948;</x>')
#    # Test attributes and values with UTF-8 inputs.
#    self.assertEqual(parse(b'<x \xce\xb4a="\xce\xb4b" />').get_attributes(
#        '\u03b4a')[0].value, '\u03b4b')

  def testUtf8TagsAndAttributes(self):
    self.assertEqual(
        parse('<\u03b4elta>test</\u03b4elta>'.encode('utf-8'))._qname,
        '\u03b4elta')
    self.assertEqual(parse(b'<\xce\xb4elta>test</\xce\xb4elta>')._qname,
                     '\u03b4elta')
    # Test an element with UTF-8 in the attribute value.
    x = create('x', None)
    x._other_attributes['a'] = b'\xce\xb4'.decode('utf-8')
    self.assert_(x.to_string().startswith('<x a="\u03b4"'))

#  def testOtherEncodingOnInputString(self):
#    BIG_ENDIAN = 0
#    LITTLE_ENDIAN = 1
#    # Test parsing inner text.
#    self.assertEqual(parse('<x>\u03b4</x>'.encode('utf-16')).text, '\u03b4')
#
#    # Test output valid XML.
#    self.assertEqual(parse('<x>\u03b4</x>'.encode('utf-16')).to_string(),
#                     '<x>&#948;</x>')
#
#    # Test setting the inner text and output valid XML.
#    e = create('x', '\u03b4')
#    self.assertEqual(e.to_string(), '<x>&#948;</x>')
#    # Don't change the encoding until the we convert to an XML string.
#    # Allow either little-endian or big-endian byte orderings.
#    self.assert_(e.text in [b'\xff\xfe\xb4\x03', b'\xfe\xff\x03\xb4'])
#    endianness = LITTLE_ENDIAN
#    if e.text == b'\xfe\xff\x03\xb4':
#      endianness = BIG_ENDIAN
#    self.assert_(isinstance(e.text, str))
#    self.assert_(isinstance(e.to_string(encoding='utf-16'), str))
#    if endianness == LITTLE_ENDIAN:
#      self.assertEqual(
#          create('x', '\xff\xfe\xb4\x03'.decode('utf-16')).to_string(), '<x>&#948;</x>')
#    else:
#      self.assertEqual(
#          create('x', '\xfe\xff\x03\xb4'.decode('utf-16')).to_string(), '<x>&#948;</x>')
#
#  def testOtherEncodingInTagsAndAttributes(self):
#    self.assertEqual(
#        parse('<\u03b4elta>test</\u03b4elta>'.encode('utf-16'))._qname,
#        '\u03b4elta')
#    # Test an element with UTF-16 in the attribute value.
#    x = create('x', None)
#    x._other_attributes['a'] = '\u03b4'.encode('utf-16')
#    self.assert_(x.to_string(encoding='UTF-16').startswith(b'<x a="&#948;"'))


def suite():
  return conf.build_suite([XmlElementTest, UtilityFunctionTest, 
                           CharacterEncodingTest])


if __name__ == '__main__':
  unittest.main()
