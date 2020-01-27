# -*- coding: utf-8 -*-

class Postproc():
    """
        postprocessor class
        continues analysis of calculated motion, e.g. enables selection of a specific roi
        or specific filters and subsequent motion calculation
    """
    # depending on analysis there can be various MVs/variables to store/track
    
    
    def __init__(self):
        self.filters = {"filter_singlemov":{"on":False, "par": "parval"}}
        self.roi = None
        # link to config somehow/ default pars somehow
        # init somewhere else?

    def link_ohw(self, curr_ohw):
        """ connect to ohw analysis object with calculated motion and other metadata """
        # or does it make sense to do this already in the constructor?
        self.curr_ohw = curr_ohw
        
        #check if analysis already happened before connecting?
        
    def set_name(self, name):
        """ specify name of specific Postproc operation, like tissue_spot1 or mybestfilterset """
        self.name = name
        
    def set_roi(self, roi = None):
        """ sets roi of postprocessing region. If a list of roi coordinates is provided use list, otherwise open selection"""
        if roi is None:
            self.roi = helpfunctions.sel_roi(self.curr_ohw.rawImageStack[0])
        elif isinstance(roi, list):
            self.roi = roi
    
    def reset_roi(self):
        self.roi = None
    
    def process(self):
        """ starts postprocessing, i.e. selects subset of MVs and performs filterng """
        # basically same as init_motion previously did
        # ... to be seen to what extent quiver components or similarly should be calculated here
        
        scalingfactor, delay = self.curr_ohw.analysis_meta["scalingfactor"], self.curr_ohw.analysis_meta["MV_parameters"]["delay"]
        print (scalingfactor, delay)
        #rawMVs_filt = Filters.filter_singlemov(self.curr_ohw.rawMVs) #don't change rawMVs! repeated loading would vary it each time
    
        #for filter in self.filters:
        if self.filters["filter_singlemov"]["on"] == True:
            rawMVs_filt = Filters.filter_singlemov(self.curr_ohw.rawMVs)
    
    def set_filter(self, filtername = "", on = True, **filterparameters):
        """ turns specific filter on/ off and sets specified parameters to filter """
        if filtername in self.filters:
            self.filters[filtername]["on"] = on
            self.filters[filtername].update(filterparameters)
        else:
            print("filter {} is not a valid filteroption".format(filtername))
    
    # might be best to turn filters in future in class (derived from general filter class)?
    # only rudimental filter implementation so far
    
    def get_processpar(self):
        """ shows all filters and parameters"""
        print("set roi: ", self.roi)
        
        print("set filter options:")
        for filtername, filterdict in self.filters.items():
            print("filter \"" + filtername + " with parameters: ")
            print (filterdict)