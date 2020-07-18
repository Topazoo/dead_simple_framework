
# Utilities
from functools import wraps

class Config():
    ''' Interface shared by all config classes '''


    @staticmethod
    def normalize_url(url:str):
        ''' Utility to add a '/' to prefix urls '''

        return '/' + url if url[0] != '/' else url


    def validate_dict(func):
        ''' Decorator used to verify that all arguments passed from_dict() are valid arguments for the class' __init__() method '''
        
        @wraps(func)
        @classmethod
        def wrapped(cls, *args, **kwargs):
            try:
                # Check types
                config = args[1]; types = cls.__init__.__annotations__
                for key in config: assert isinstance(config[key], types[key]), \
                    f"{cls.__name__}.from_dict() for url [{args[0]}] was passed an invalid type. Key [{key}] must have a type of {types[key]}"
                
                return func(cls, *args, **kwargs)

            # Catch invalid parameters
            except TypeError as e:
                invalid_param = str(e)[str(e).find("'") + 1: str(e).rfind("'")]
                raise TypeError(f"{cls.__name__}.from_dict() for url [{args[0]}] was passed invalid parameter [{invalid_param}]. Supported parameters (config dictionary keys) are {list(filter(lambda x: x!= 'self', cls.__init__.__code__.co_varnames))}")

        return wrapped


    @validate_dict
    def from_dict(cls, *arg, **kwargs) -> 'Config':
        ''' Factory for generating a `Config` class from a dictionary. Overriden by concrete config classes '''
        
        return cls(*arg, **kwargs)


    def to_dict(self):
        ''' Get the route in dictionary form '''

        return self.__dict__