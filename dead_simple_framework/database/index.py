# Database
from .main import Database

# Typing
from typing import Dict, Union

# Logging
import logging


class Indices:
    ''' Client to store a collection of MongoDB index information '''

    INDICES = {}

    def __init__(self, indices:dict=None):
        self._merge_dicts(self.INDICES, self._parse_indices_dict(indices) if indices else {})


    @staticmethod
    def _parse_indices_dict(indices:dict) -> Dict[str, Dict[str, "Index"]]:
        ''' Convert a dictionary of indices in the config to Index objects for storage '''

        parsed_indices = {}
        for collection, fields in indices.items():
            if collection not in parsed_indices: 
                parsed_indices[collection] = {}

            for field in fields:
                index = Index.from_dict(collection, field, indices[collection][field]) if not isinstance(indices[collection][field], Index) else indices[collection][field]
                parsed_indices[collection][field] = index

        return parsed_indices


    @classmethod
    def add_index(cls, collection:str, index:Union["Index", dict], register:bool=True):
        ''' Add an index to a specified MongoDB collection '''

        if collection not in cls.INDICES:
            cls.INDICES[collection] = {}

        if isinstance(index, dict):
            field = list(index.keys())[0]; index = Index.from_dict(collection, field, index[field])

        if index.field in cls.INDICES[collection]:
            logging.warning(f"Index [{index.field}] for collection [{collection}] was overwritten")

        cls.INDICES[collection][index.field] = index

        if register:
            Database.register_indices(cls)


    @classmethod
    def add_indices(cls, collection:str, indices:list[Union["Index", dict]], register:bool=True):
        ''' Add a list of indices to a specified MongoDB collection '''

        for index in indices:
            cls.add_index(collection, index, False)

        if register:
            Database.register_indices(cls)
        
    
    @classmethod
    def from_dict(cls, indices:Union[dict, "Indices"]) -> "Indices":
        return indices if isinstance(indices, Indices) else cls(indices)


    @classmethod
    def _merge_dicts(cls, d1:dict, d2:dict):
        ''' Utility for merging dictionaries on all levels '''

        for key in d2:
            if key in d1:
                if isinstance(d2[key], dict):
                    cls._merge_dicts(d1[key], d2[key])
                else:
                    d1[key] = d2[key]
            else:
                d1[key] = d2[key]


    def __repr__(self) -> str:
        return f'<indices: {[x for x in self.INDICES.items()]}>' 


class Index:
    ''' Stores MongoDB index information '''

    def __init__(self, field:str, order:int=None, properties:dict=None, compound_with:str=None, is_text=False):

        if not order and not field:
            raise TypeError(f"Index [{field}] was not passed an order and is_text is False. Please supply and order or create a text index")
            
        self.field = field
        self.order = order
        self.properties = properties or {}
        self.compound_with = compound_with
        self.is_text = is_text


    @classmethod
    def from_dict(cls, collection:str, field:str, index_data:dict) -> "Index":
        ''' Parse an Index from a dictionary '''

        try:
            return cls(field, **index_data)
        except TypeError as e:
            raise TypeError(f"Index [{field}] for collection [{collection}] was passed an invalid option: {str(e).split(' ')[-1]}")


    def __repr__(self) -> str:
        return f'<order: {self.order}, props: {self.properties}, compound_with: {self.compound_with}' 
