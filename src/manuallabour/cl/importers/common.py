

class ImporterBase(object):
    """
    Base Class for importers
    """
    def __init__(self,key):
        """
        Name of the key in the step dictionary this importer takes care of.
        """
        self.key = key

    def process(self,step_id,in_dict,out_dict,store,cache):
        """
        Process one step.

        in_dict is the dictionary for this Importer as loaded from the yaml.
        out_dict is a dictionary of arguments to GraphStep.

        cache is a FileCache instance that can be used to cache file results.

        This function reads in_dict and adds to out_dict.
        """
        pass
