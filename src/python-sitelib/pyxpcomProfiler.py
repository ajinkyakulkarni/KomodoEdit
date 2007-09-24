import xpcom, xpcom.server
#import hotshot
import cProfile as profile
import threading

class koProfile:
    def __init__(self):
        #self.prof = hotshot.Profile("kogrind.prof", lineevents=1)
        self.prof = profile.Profile()
        self.lock = threading.Lock()

    def __del__(self):
        self.prof.close()

    def acquire(self):
        return self.lock.acquire(0)

    def release(self):
        self.lock.release()

    def print_stats(self, sort=-1, limit=None):
        import pstats
        stats = pstats.Stats(self.prof)
        #stats.strip_dirs()
        stats.sort_stats(sort)
        stats.print_stats(limit)

# store in xpcom module
xpcom._koprofiler = koProfile()

xpcom_recordings = {}

class XPCOMRecorder:
    """Object to record pyxpcom usage"""
    def __init__(self, name):
        self.name = name
        self.calls = {}
        self.getters = {}
        self.setters = {}

    def recordCall(self, attr):
        self.calls[attr] = self.calls.get(attr, 0) + 1

    def recordGetter(self, attr):
        self.getters[attr] = self.getters.get(attr, 0) + 1

    def recordSetter(self, attr):
        self.setters[attr] = self.setters.get(attr, 0) + 1

    def __len__(self):
        return sum(self.calls.values()) + sum(self.getters.values()) + sum(self.setters.values())

    def print_stats(self):
        print "%s" % (self.name)
        if self.calls:
            print "  Calls: %d" % (sum(self.calls.values()))
            for name, num in sorted(self.calls.items(), key=lambda (k,v): (v,k), reverse=True):
                print "      %-30s%d" % (name, num)
        if self.getters:
            print "  Getters: %d" % (sum(self.getters.values()))
            for name, num in sorted(self.getters.items(), key=lambda (k,v): (v,k), reverse=True):
                print "      %-30s%d" % (name, num)
        if self.setters:
            print "  Setters: %d" % (sum(self.setters.values()))
            for name, num in sorted(self.setters.items(), key=lambda (k,v): (v,k), reverse=True):
                print "      %-30s%d" % (name, num)
        #print

def getXPCOMRecorder(xpcomObject):
    """Return the base xpcom recorder object for this python xpcom object.

    Tries to record all the same xpcom instances for one interface in the same
    recorder object.
    """
    names = None
    if hasattr(xpcomObject, "_interface_names_"):
        names = [x.name for x in xpcomObject._interface_names_]
    if not names:
        com_interfaces = getattr(xpcomObject, "_com_interfaces_", None)
        if com_interfaces:
            if not isinstance(com_interfaces, (tuple, list)):
                names = [com_interfaces.name]
            else:
                names = [x.name for x in com_interfaces]
    if names is not None:
        name = "_".join(names)
    else:
        name = repr(xpcomObject)
    recorder = xpcom_recordings.get(name)
    if recorder is None:
        recorder = XPCOMRecorder(name)
        xpcom_recordings[name] = recorder
    return recorder

# A wrapper around a function - looks like a function,
# but actually profiles the delegate.
class TracerDelegate:
    def __init__(self, callme):
        self.callme = callme
    def __call__(self, *args):
        if not xpcom._koprofiler.acquire():
            return apply(self.callme, args)
        try:
            return xpcom._koprofiler.prof.runcall(self.callme, *args)
        finally:
            xpcom._koprofiler.release()

# A wrapper around each of our XPCOM objects.  All PyXPCOM calls
# in are made on this object, which creates a TracerDelagate around
# every function.  As the function is called, it collects profile info.
class Tracer:
    def __init__(self, ob):
        self.__dict__['_ob'] = ob
        self.__dict__['_recorder'] = getXPCOMRecorder(ob)
    def __repr__(self):
        return "<Tracer around %r>" % (self._ob,)
    def __str__(self):
        return "<Tracer around %r>" % (self._ob,)
    def __getattr__(self, attr):
        ret = getattr(self._ob, attr) # Attribute error just goes up
        if callable(ret):
            if not attr.startswith("_com_") and not attr.startswith("_reg_"):
                self.__dict__['_recorder'].recordCall(attr)
            return TracerDelegate(ret)
        else:
            if not attr.startswith("_com_") and not attr.startswith("_reg_"):
                self.__dict__['_recorder'].recordGetter(attr)
            return ret
    def __setattr__(self, attr, val):
        if self.__dict__.has_key(attr):
            self.__dict__[attr] = val
            return
        if not attr.startswith("_com_") and not attr.startswith("_reg_"):
                self.__dict__['_recorder'].recordSetter(attr)
        setattr(self._ob, attr, val)

def print_stats():
    """Print out the pyXPCOM stats and the python main thread profiler stats"""
    def recorder_cmp(a, b):
        return cmp(len(a[0]), len(b[0]))
    for name, recorder in sorted(xpcom_recordings.items(),
                                 cmp=recorder_cmp,
                                 key=lambda (k,v): (v,k), reverse=True):
        if len(recorder) > 0:
            recorder.print_stats()
    print
    print "*" * 60
    print
    xpcom._koprofiler.print_stats(sort='time', limit=100)
    print "*" * 60
    print "Stats finished\n"


# Installed as a global XPCOM function that if exists, will be called
# to wrap each XPCOM object created.
def MakeTracer(ob):
    # In some cases we may be asked to wrap ourself, so handle that.
    if isinstance(ob, Tracer):
        return ob
    return Tracer(ob)

def UnwrapTracer(ob):
    if isinstance(ob, Tracer):
        return ob._ob
    return ob

xpcom.server.tracer = MakeTracer
xpcom.server.tracer_unwrap = UnwrapTracer

class xpcomShutdownObserver(object):
    _com_interfaces_ = [xpcom.components.interfaces.nsIObserver]
    def observe(self, subject, topic, data):
        if topic == "xpcom-shutdown":
            print_stats()

xpcomObs = xpcomShutdownObserver()
obsSvc = xpcom.components.classes["@mozilla.org/observer-service;1"].\
               getService(xpcom.components.interfaces.nsIObserverService)
wrappedxpcomObs = xpcom.server.WrapObject(xpcomObs, xpcom.components.interfaces.nsIObserver)
obsSvc.addObserver(wrappedxpcomObs, 'xpcom-shutdown', 1)
