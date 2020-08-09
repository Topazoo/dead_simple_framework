# Base class
from ..config import Config

class Setting(Config):
    ''' Interface shared by all settings classes '''

    CONFIG_TYPE = 'setting'

    @Config.validate_dict
    def from_dict(cls, _, config:dict) -> 'Setting':
        ''' Factory for generating a `Setting` class from a dictionary. Overriden by concrete settings classes '''
        
        return cls(**config)

    @staticmethod
    def get_log_data():
        ''' Returns a list of the settings to log to console 
            Overridden by concrete classes
        '''

        return []