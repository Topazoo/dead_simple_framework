# MongoDB
from pymongo.errors import OperationFailure

# Database
from .main import Database

# Typing
from typing import Dict, Union

# Logging
import logging


class Indices:
    ''' Client to store a collection of MongoDB index information '''

    def __init__(self, indices:dict=None):
        self.indices = self._parse_indices_dict(indices) if indices else {}


    def _parse_indices_dict(self, indices:dict) -> Dict[str, Dict[str, "Index"]]:
        ''' Convert a dictionary of indices in the config to Index objects for storage '''

        parsed_indices = {}
        for collection, fields in indices.items():
            if collection not in parsed_indices: 
                parsed_indices[collection] = {}

            for field in fields:
                index = Index.from_dict(collection, field, indices[collection][field]) if not isinstance(indices[collection][field], Index) else indices[collection][field]
                parsed_indices[collection][field] = index

        return parsed_indices


    def add_index(self, collection:str, index:Union["Index", dict], register:bool=True):
        ''' Add an index to a specified MongoDB collection '''

        if collection not in self.indices:
            self.indices[collection] = {}

        if isinstance(index, dict):
            field = list(index.keys())[0]; index = Index.from_dict(collection, field, index[field])

        if index.field in self.indices[collection]:
            logging.warning(f"Index [{index.field}] for collection [{collection}] was overwritten")

        self.indices[collection][index.field] = index

        if register:
            self.register_indices()


    def add_indices(self, collection:str, indices:list[Union["Index", dict]], register:bool=True):
        ''' Add a list of indices to a specified MongoDB collection '''

        for index in indices:
            self.add_index(collection, index, False)

        if register:
            self.register_indices()


    def register_indices(self):
        ''' Create user specified indices in MongoDB '''

        curr_indices = self.indices.copy()
        for collection,indices in curr_indices.items():
            compounds = [index.compound_with for index in indices.values() if index.compound_with]
            with Database(collection=collection) as coll:
                try:
                    for field, index in indices.items():
                        if field not in compounds and not index.compound_with:
                            coll.create_index([(field, index.order)], **index.properties, background=True)
                        elif field not in compounds:
                            if index.compound_with not in indices:
                                raise TypeError(f'Index [{index.compound_with}] to compound with index [{field}] not specified for collection [{collection}]!')

                            compound = indices[index.compound_with]
                            index.properties.update(compound.properties)
                            coll.create_index([(field, index.order), (compound.field, compound.order)], **index.properties, background=True)

                except OperationFailure as e:
                    if e.code == 85:
                        pass
                    else:
                        raise e
        
    
    @classmethod
    def from_dict(cls, indices:Union[dict, "Indices"]) -> "Indices":
        return cls(indices) if isinstance(indices, dict) else indices


    def __repr__(self) -> str:
        return f'<indices: {[x for x in self.indices.items()]}>' 


class Index:
    ''' Stores MongoDB index information '''

    def __init__(self, field:str, order:int, properties:dict=None, compound_with:str=None):

        self.field = field
        self.order = order
        self.properties = properties or {}
        self.compound_with = compound_with


    @classmethod
    def from_dict(cls, collection:str, field:str, index_data:dict) -> "Index":
        ''' Parse an Index from a dictionary '''

        try:
            return cls(field, **index_data)
        except TypeError as e:
            raise TypeError(f"Index [{field}] for collection [{collection}] was passed an invalid option: {str(e).split(' ')[-1]}")


    def __repr__(self) -> str:
        return f'<order: {self.order}, props: {self.properties}, compound_with: {self.compound_with}' 
