try:
    from prettytable import PrettyTable
except: pass

"""
This module defines a framework for filtering Trees.
The user must write a class which inherits from Filter and
"""
class Filter(object):
    """
    The base class from which all filter classes must inherit from.
    The derived class must override the passes method which returns True
    if ths event passes and returns False if not.
    The number of passing and failing events are recorded and may be used
    later to create a cut-flow.
    """
    def __init__(self, hooks=None, passthrough=False):
        
        self.total = 0
        self.passing = 0
        self.details = {}
        self.name = self.__class__.__name__
        self.hooks = hooks
        self.passthrough = passthrough
    
    def __str__(self):

        return self.__repr__()
    
    def __getstate__(self):

        return {"name": self.name,
                "total": self.total,
                "passing": self.passing,
                "details": self.details}
    
    def __setstate__(self, state):

        self.name = state['name']
        self.total = state['total']
        self.passing = state['passing']
        self.details = state['details']
    
    def __repr__(self):

        return "Filter %s\n"%(self.name)+\
               "Total: %i\n"%(self.total)+\
               "Pass:  %i"%(self.passing)
    
    @classmethod
    def add(cls, left, right):
        
        if left.name != right.name:
            raise ValueError("Attemping to add filters with different names")
        newfilter = Filter()
        newfilter.name = left.name
        newfilter.total = left.total + right.total
        newfilter.passing = left.passing + right.passing
        newfilter.details = dict([(detail, left.details[detail] + right.details[detail]) for detail in left.details.keys()])

    def __add__(self, other):
        
        return Filter.add(self, other)

class FilterHook(object):

    def __init__(self, target, args):

        self.target = target
        self.args = args

    def __call__(self):

        self.target(*self.args)
 
class EventFilter(Filter):

    def __call__(self, event):

        self.total += 1
        if self.passthrough or self.passes(event):
            if self.hooks:
                for hook in self.hooks:
                    hook()
            self.passing += 1
            return True
        return False
    
    def passes(self, event):

        raise NotImplementedError("You must override this method in your derived class")

class ObjectFilter(Filter):

    def __init__(self, count_events=False, **kwargs):

        self.count_events = count_events
        super(ObjectFilter, self).__init__(**kwargs)

    def __call__(self, event, collection):

        if self.count_events:
            self.total += 1
        else:
            self.total += len(collection)
        if not self.passthrough:
            collection = self.filtered(event, collection)
        if len(collection) > 0:
            if self.count_events:
                self.passing += 1
            else:
                self.passing += len(collection)
        return collection
   
    def filtered(self, event, collection):

        raise NotImplementedError("You must override this method in your derived class")

class FilterList(list):
    """
    Creates a list of Filters for convenient evaluation of a sequence of Filters.
    """
    @classmethod
    def merge(cls, list1, list2):
        
        filterlist = FilterList()
        for f1,f2 in zip(list1,list2):
            filterlist.append(f1+f2)
        return filterlist
    
    @property
    def total(self):
        
        if len(self) > 0:
            return self[0].total
        return 0
    
    @property
    def passing(self):

        if len(self) > 0:
            return self[-1].passing
        return 0
    
    def basic(self):
        """
        Return all filters as simple dicts for pickling.
        Removes all dependence on this module.
        """
        return [filter.__getstate__() for filter in self]
    
    def __setitem__(self, filter):

        if not isinstance(filter, Filter):
            raise TypeError("FilterList can only hold objects inheriting from Filter")
        super(FilterList, self).__setitem__(filter)
    
    def append(self, filter):
        
        if not isinstance(filter, Filter):
            raise TypeError("FilterList can only hold objects inheriting from Filter")
        super(FilterList, self).append(filter)

    def __str__(self):

        return self.__repr__()
    
    def __repr__(self):

        if len(self) > 0:
            table = PrettyTable(["Filter", "Pass"])
            table.align["Filter"] = "l"
            table.align["Pass"] = "l"
            table.add_row(["Total", self[0].total])
            for filter in self:
                table.add_row([filter.name, filter.passing])
            _str = str(table)
            for filter in self:
                if filter.details:
                    _str += "\n%s Details\n"% filter.name
                    details_table = PrettyTable(["Detail", "Value"])
                    for key, value in filter.details.items():
                        details_table.add_row([key, value])
                    _str += str(details_table)
            return _str 
        return "Empty FilterList"

class EventFilterList(FilterList):

    def __call__(self, event):

        for filter in self:
            if not filter(event):
                return False
        return True
    
    def __setitem__(self, filter):

        if not isinstance(filter, EventFilter):
            raise TypeError("EventFilterList can only hold objects inheriting from EventFilter")
        super(EventFilterList, self).__setitem__(filter)
    
    def append(self, filter):
        
        if not isinstance(filter, EventFilter):
            raise TypeError("EventFilterList can only hold objects inheriting from EventFilter")
        super(EventFilterList, self).append(filter)

class ObjectFilterList(FilterList):

    def __call__(self, event, collection):

        passing_objects = collection
        for filter in self:
            passing_objects = filter(event, passing_objects)
            if not passing_objects:
                return []
        return passing_objects

    def __setitem__(self, filter):

        if not isinstance(filter, ObjectFilter):
            raise TypeError("ObjectFilterList can only hold objects inheriting from ObjectFilter")
        super(ObjectFilterList, self).__setitem__(filter)
    
    def append(self, filter):
        
        if not isinstance(filter, ObjectFilter):
            raise TypeError("ObjectFilterList can only hold objects inheriting from ObjectFilter")
        super(ObjectFilterList, self).append(filter)
