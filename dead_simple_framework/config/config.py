
# Utilities
from functools import wraps

class Config():
    ''' Interface shared by all config classes '''

    CONFIG_TYPE = 'config'

    @staticmethod
    def normalize_url(url:str):
        ''' Utility to add a '/' to prefix urls '''

        return '/' + url if url[0] != '/' else url


    def validate_dict(func):
        ''' Decorator used to verify that all arguments passed from_dict() are valid arguments for the class' __init__() method '''
        
        @wraps(func)
        @classmethod
        def wrapped(cls, *args):
            try:
                # Check number of arguments
                assert len(args) == 2, f"{cls.__name__}.from_dict() only passed [{len(args)}] arguments but 2 are required (name and config)"
                # Check types
                config = args[1]; types = cls.__init__.__annotations__
                for key in config: assert isinstance(config[key], types[key]) or not config[key], \
                    f"{cls.__name__}.from_dict() for url [{args[0]}] was passed an invalid type. Key [{key}] must have a type of {types[key]} but is {type(config[key])}"

                return func(cls, args[0], args[1])

            # Catch invalid parameters
            except KeyError as e:
                invalid_param = str(e)[str(e).find("'") + 1: str(e).rfind("'")]
                raise TypeError(f"{cls.__name__}.from_dict() for {cls.CONFIG_TYPE} [{args[0]}] was passed invalid parameter [{invalid_param}]. Supported parameters (config dictionary keys) are {list(filter(lambda x: x!= 'self', cls.__init__.__code__.co_varnames))}")

        return wrapped


    @validate_dict
    def from_dict(cls, name:str, config:dict) -> 'Config':
        ''' Factory for generating a `Config` class from a dictionary. Overriden by concrete config classes '''
        
        return cls(name, **config)


    def to_dict(self):
        ''' Get the route in dictionary form '''

        return self.__dict__