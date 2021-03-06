# Copyright 2012 the rootpy developers
# distributed under the terms of the GNU General Public License
"""
This module implements python classes which inherit from
and extend the functionality of the ROOT canvas classes.
"""

import ROOT

from ..core import NamedObject
from .. import QROOT


class _PadBase(NamedObject):

    def _post_init(self):

        self.members = []

    def Clear(self, *args, **kwargs):

        self.members = []
        super(_PadBase, self).Clear(*args, **kwargs)

    def OwnMembers(self):

        for thing in self.GetListOfPrimitives():
            if thing not in self.members:
                self.members.append(thing)


class Pad(_PadBase, QROOT.TPad):

    def __init__(self, *args, **kwargs):

        super(Pad, self).__init__(*args, **kwargs)
        self._post_init()


class Canvas(_PadBase, QROOT.TCanvas):

    def __init__(self,
                 width=None, height=None,
                 x=None, y=None,
                 name=None, title=None):

        # The following line will trigger finalSetup and start the graphics
        # thread if not started already
        style = ROOT.gStyle
        if width is None:
            width = style.GetCanvasDefW()
        if height is None:
            height = style.GetCanvasDefH()
        if x is None:
            x = style.GetCanvasDefX()
        if y is None:
            y = style.GetCanvasDefY()
        super(Canvas, self).__init__(x, y, width, height,
                                     name=name, title=title)
        self._post_init()
