#!/usr/bin/env python
# encoding: utf-8
'''
This module is used to convert diction to xml and convert xml to diction
usage:
    import simplexml
    simplexml.dumps(dict)   # output xml string
    simplexml.loads(xml)    # output python dict
changelist:
    0.2: add unicode support.
'''

__version__ = "0.2"
__author__ = "@fanmuzhi, @boqiling"
__all__ = ["dumps", "loads", "Xml2Dict", "Dict2Xml"]

from xml.dom.minidom import Document, parseString, Node


def dumps(diction, rootname="entity"):
    '''convert diction to xml
    '''
    if (type(diction) == dict):
        xml = Dict2Xml(rootname).trans(diction)
        return xml


def loads(xml):
    '''convert xml to diction
    '''
    diction = Xml2Dict().trans(xml)
    return diction


class Xml2Dict(object):
    '''class to convert the xml to python diction
       usage:
           diction = Xml2Dict().trans("<xml>xml_string</xml>")
    '''

    def __init__(self):
        self.Dict = {}

    def remove_blanks(self, node):
        for x in node.childNodes:
            if x.nodeType == Node.TEXT_NODE:
                if x.nodeValue:
                    x.nodeValue = x.nodeValue.strip()
            elif x.nodeType == Node.ELEMENT_NODE:
                self.remove_blanks(x)

    def to_list(self, father):
        myList = []
        for node in father.childNodes:
            if (len(node.childNodes) > 1):
                myList.append(self.parse(node))
            else:
                myList.append(node.childNodes[0].nodeValue)
        return myList

    def parse(self, father):
        myDict = {}
        if (father.hasAttributes()):
            for attr in father.attributes.items():
                myDict.update({attr[0]: attr[1]})
        if (father.hasChildNodes()):
            if (len(father.childNodes) > 1):
                if (father.firstChild.nodeName == father.lastChild.nodeName):
                    # parse a list
                    listname = father.nodeName
                    tag = father.firstChild.nodeName
                    myDict.update({listname: {tag: self.to_list(father)}})
                else:
                    # parse a recurse dict
                    subDict = {}
                    for node in father.childNodes:
                        subDict.update(self.parse(node))
                    myDict.update({father.nodeName: subDict})
            else:
                # parse a value
                node = father.childNodes[0]
                if (node.nodeType == Node.TEXT_NODE):
                    myDict.update({father.nodeName: node.nodeValue})
                else:
                    myDict.update({father.nodeName: self.parse(node)})
        return myDict

    def trans(self, xml):
        self.doc = parseString(xml.encode("utf-8"))
        self.remove_blanks(self.doc)
        self.doc.normalize()
        self.root = self.doc.documentElement
        mydict = self.parse(self.root)
        self.Dict.update(mydict[self.root.nodeName])
        return self.Dict


class Dict2Xml(object):
    '''class to convert the python diction to xml
       usage:
           xml = Dict2Xml().trans(diction)
    '''

    def __init__(self, rootname):
        self.doc = Document()
        self.rootName = rootname

    def build(self, father, structure):
        if type(structure) == dict:
            for k in structure:
                tag = self.doc.createElement(k)
                father.appendChild(tag)
                self.build(tag, structure[k])

        elif type(structure) == list:
            grandFather = father.parentNode
            tagName = father.tagName
            grandFather.removeChild(father)
            for l in structure:
                tag = self.doc.createElement(tagName)
                self.build(tag, l)
                grandFather.appendChild(tag)
        else:
            data = unicode(structure)
            tag = self.doc.createTextNode(data)
            father.appendChild(tag)

    def trans(self, diction):
        self.root = self.doc.createElement(self.rootName)
        self.doc.appendChild(self.root)
        self.build(self.root, diction)
        return self.doc.toprettyxml(indent="    ")
        # return self.doc.toxml("utf-8")


if __name__ == '__main__':
    from pprint import pprint as pp

    example = {
        "sn": 2103839,
        "item": "SNR",
        "date": "2009-11-25",
        "errorcode": 7,
        u"错误信息": u"噪声太大",
        "signals": {"signal": [1, 2, 3]},
        "noises": {"noise": [5, 6, 7]},
        "rounds": {
            "round_59": {
                "fail": 1,
                "test_time": "2013-11-11 17:54:21",
                "test_result": "Pass"
            },
            "round_60": {
                "fail": 2,
                "test_time": "2013-11-11 17:55:23",
                "test_result": "fail"
            }
        }
    }

    print("original:")
    pp(example)
    print("dict to xml:")
    myxml = dumps(example)
    print(myxml)
    print(type(myxml))

    print("xml to dict:")
    mydict = loads(myxml)
    pp(mydict)
    print mydict[u"错误信息"]
