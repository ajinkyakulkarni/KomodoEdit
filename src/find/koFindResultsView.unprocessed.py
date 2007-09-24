#!python
# Copyright (c) 2000-2006 ActiveState Software Inc.
# See the file LICENSE.txt for licensing information.

# Implementation of the tree view for displaying find results in the find
# results tab in the output pane of Komodo.

from xpcom import components
import logging
log = logging.getLogger('koFindResultsView')
import sys, os, re, types
from koTreeView import TreeView

class KoFindResultsView(TreeView):
    _com_interfaces_ = [components.interfaces.koIFindResultsView,
                        components.interfaces.nsITreeView]
    _reg_clsid_ = "{154CF0D6-D556-4be5-9F55-65AE5DB46312}"
    _reg_contractid_ = "@activestate.com/koFindResultsView;1"
    _reg_desc_ = "Komodo Find Results Tree Table View"

    def __init__(self):
        TreeView.__init__(self, debug=0)
        self._data = []
        self._tree = None
        self._sortedBy = None
        self.id = None

    def get_rowCount(self):
        return len(self._data)

    def getCellText(self, row, column):
        try:
            datum = self._data[row][column.id]
        except IndexError:
            # Silence this, it is too annoying.
            # c.f. http://bugs.activestate.com/Komodo/show_bug.cgi?id=27487
            #log.error("no %sth find result" % row)
            return ""
        except KeyError:
            log.error("unknown find result column id: '%s'" % column.id)
            return ""
        if type(datum) not in (types.StringType, types.UnicodeType):
            datum = str(datum)
        return datum

    def Clear(self):
        length = len(self._data)
        self._data = []
        self._sortedBy = None
        self._tree.beginUpdateBatch()
        self._tree.rowCountChanged(0, -length)
        self._tree.invalidate()
        self._tree.endUpdateBatch()

    def AddFindResult(self, url, startIndex, endIndex, value, fileName,
                      lineNum, columnNum, context):
        datum = {"url": url,
                 "startIndex": startIndex,
                 "endIndex": endIndex,
                 "value": value,
                 "lineNum": lineNum,
                 "columnNum": columnNum,
                 "findresults%d-filename" % self.id: fileName,
                 "findresults%d-linenum" % self.id: lineNum,
                 "findresults%d-context" % self.id: context}
        self._data.append(datum)
        self._sortedBy = None
        self._tree.beginUpdateBatch()
        self._tree.rowCountChanged(len(self._data)-2, 1)
        self._tree.invalidate()  #XXX invalidating too much here?
        self._tree.endUpdateBatch()

    def AddFindResults(self, urls, startIndexs, endIndexs, values, fileNames,
                       lineNums, columnNums, contexts):
        for (url, startIndex, endIndex, value, fileName, lineNum,
             columnNum, context) in zip(urls, startIndexs, endIndexs, values,
                                        fileNames, lineNums, columnNums,
                                        contexts):
            datum = {"url": url,
                     "startIndex": startIndex,
                     "endIndex": endIndex,
                     "value": value,
                     "lineNum": lineNum,
                     "columnNum": columnNum,
                     "findresults%d-filename" % self.id: fileName,
                     "findresults%d-linenum" % self.id: lineNum,
                     "findresults%d-context" % self.id: context}
            self._data.append(datum)
        self._sortedBy = None
        self._tree.beginUpdateBatch()
        self._tree.rowCountChanged(0, len(urls))
        self._tree.invalidate()  #XXX invalidating too much here?
        self._tree.endUpdateBatch()

    def AddReplaceResult(self, url, startIndex, endIndex, value, replacement,
                         fileName, lineNum, columnNum, context):
        datum = {"url": url,
                 "startIndex": startIndex,
                 "endIndex": endIndex,
                 "value": value,
                 "replacement": replacement,
                 "lineNum": lineNum,
                 "columnNum": columnNum,
                 "findresults%d-filename" % self.id: fileName,
                 "findresults%d-linenum" % self.id: lineNum,
                 "findresults%d-context" % self.id: context}
        self._data.append(datum)
        self._sortedBy = None
        self._tree.beginUpdateBatch()
        self._tree.rowCountChanged(len(self._data)-2, 1)
        self._tree.invalidate()  #XXX invalidating too much here?
        self._tree.endUpdateBatch()

    def GetUrl(self, index):
        return self._data[index]["url"]
    def GetStartIndex(self, index):
        return self._data[index]["startIndex"]
    def GetEndIndex(self, index):
        return self._data[index]["endIndex"]
    def GetValue(self, index):
        return self._data[index]["value"]
    def GetReplacement(self, index):
        try:
            return self._data[index]["replacement"]
        except KeyError:
            return ""
    def GetLineNum(self, index):
        return self._data[index]["lineNum"]
    def GetColumnNum(self, index):
        return self._data[index]["columnNum"]

    def Sort(self, sortBy):
        """Sort the current data by the given key. If already sorted by this
        key then reverse the sorting order."""
        if self._sortedBy == sortBy:
            self._data.reverse()
        else:
            try:
                if sortBy == "findresults%d-context" % self.id:
                    # strip leading whitespace for context sort order
                    self._data.sort(lambda dict1,dict2,sortBy=sortBy:
                                        cmp(dict1[sortBy].lstrip(), dict2[sortBy].lstrip())
                                   )
                else:
                    self._data.sort(lambda dict1,dict2,sortBy=sortBy:
                                        cmp(dict1[sortBy], dict2[sortBy])
                                   )
            except KeyError:
                log.error("Cannot sort find results by: '%s'" % sortBy)
                raise
        self._sortedBy = sortBy
        self._tree.beginUpdateBatch()
        self._tree.invalidate()
        self._tree.endUpdateBatch()

    def GetNumUrls(self):
        urlDict = {}
        for datum in self._data:
            urlDict[datum["url"]] = 1
        return len(urlDict.keys())

