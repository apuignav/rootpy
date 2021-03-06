# Copyright 2012 the rootpy developers
# distributed under the terms of the GNU General Public License
from contextlib import contextmanager

# Note about locks: we don't need this in cases where ROOT as a thread-specific
# variable, so gDirectory and gPad are safe.
# Not so for gStyle, IsBatch and TH1.AddDirectory, so we use a lock in these
# cases. To prevent out-of-order lock grabbing, just use one reentrant lock for
# all of them.
import threading
LOCK = threading.RLock()

import ROOT
from . import gDirectory


@contextmanager
def preserve_current_style():
    """
    Context manager which ensures that the current style remains the current
    style when the context is left.
    """
    # this should be 'Modern' by default
    with LOCK:
        old = ROOT.gStyle
        try:
            yield
        finally:
            ROOT.gROOT.SetStyle(old.GetName())

@contextmanager
def preserve_current_canvas():
    """
    Context manager which ensures that the current canvas remains the current
    canvas when the context is left.
    """
    old = ROOT.gPad.func()
    try:
        yield
    finally:
        if old:
            old.cd()

        else:
            # Put things back how they were before.
            if ROOT.gPad.func():
                with invisible_canvas():
                    # This is a round-about way of resetting gPad to None.
                    # No other technique I tried could do it.
                    pass

@contextmanager
def preserve_current_directory():
    """
    Context manager which ensures that the current directory remains the current
    directory when the context is left.
    """
    old = gDirectory()
    try:
        yield
    finally:
        assert old, "BUG: assumptions were invalid. Please report this"
        # old is always valid and refers to ROOT.TROOT if no file is created.
        old.cd()

@contextmanager
def preserve_batch_state():
    """
    Context manager which ensures the batch state is the same on exit as it was
    on entry.
    """
    with LOCK:
        old = ROOT.gROOT.IsBatch()
        try:
            yield
        finally:
            ROOT.gROOT.SetBatch(old)

@contextmanager
def invisible_canvas():
    """
    Context manager yielding a temporary canvas drawn in batch mode, invisible
    to the user. Original state is restored on exit.

    Example use; obtain X axis object without interfering with anything::

        with invisible_canvas() as c:
            efficiency.Draw()
            g = efficiency.GetPaintedGraph()
            return g.GetXaxis()
    """
    with preserve_current_canvas():

        with preserve_batch_state():
            ROOT.gROOT.SetBatch()
            c = ROOT.TCanvas()

        try:
            c.cd()
            yield c
        finally:
            c.Close()
            c.IsA().Destructor(c)

@contextmanager
def thread_specific_tmprootdir():
    """
    Context manager which makes a thread specific gDirectory to avoid interfering
    with the current file.

    Use cases:

        A TTree Draw function which doesn't want to interfere with whatever
        gDirectory happens to be.

        Multi-threading where there are two threads creating objects with the
        same name which must reside in a directory. (again, this happens with
        TTree draw)
    """
    with preserve_current_directory():
        dname = "rootpy-tmp/thread/{0}".format(threading.current_thread().ident)
        d = ROOT.gROOT.mkdir(dname)
        if not d:
            d = ROOT.gROOT.GetDirectory(dname)
            assert d, "Unexpected failure, can't cd to tmpdir."
        d.cd()
        yield d

@contextmanager
def set_directory(robject):
    """
    Context manager to temporarily set the directory of a ROOT object
    """
    old_dir = robject.GetDirectory()
    try:
        robject.SetDirectory(gDirectory())
        yield
    finally:
        robject.SetDirectory(old_dir)

@contextmanager
def preserve_set_th1_add_directory(state=True):
    """
    Context manager to temporarily set TH1.AddDirectory() state
    """
    with LOCK:
        status = ROOT.TH1.AddDirectoryStatus()
        try:
            ROOT.TH1.AddDirectory(state)
            yield
        finally:
            ROOT.TH1.AddDirectory(status)

@contextmanager
def do_nothing():
    yield

