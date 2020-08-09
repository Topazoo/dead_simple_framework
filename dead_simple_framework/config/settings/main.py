
# Individual configs
from . import App_Settings, MongoDB_Settings, RabbitMQ_Settings, Redis_Settings

# Utilities
import os

# Typing
from typing import Union

class Settings(App_Settings, MongoDB_Settings, RabbitMQ_Settings, Redis_Settings):
    ''' Used to specify and validate all application settings '''

    def __init__(self, 
                 app_settings:Union[dict, App_Settings]=None, 
                 mongodb_settings:Union[dict, MongoDB_Settings]=None, 
                 rabbitmq_settings:Union[dict, RabbitMQ_Settings]=None,
                 redis_settings:Union[dict, Redis_Settings]=None):


        if isinstance(app_settings, dict): App_Settings.from_dict('app_settings', app_settings)
        if app_settings == None: App_Settings()

        if isinstance(mongodb_settings, dict): MongoDB_Settings.from_dict('mongodb_settings', mongodb_settings)
        if mongodb_settings == None: MongoDB_Settings()
        
        if isinstance(rabbitmq_settings, dict): RabbitMQ_Settings.from_dict('rabbitmq_settings', rabbitmq_settings)
        if rabbitmq_settings == None: RabbitMQ_Settings()
        
        if isinstance(redis_settings, dict): Redis_Settings.from_dict('redis_settings', redis_settings)
        if redis_settings == None: Redis_Settings()


    @staticmethod
    def log_config():
        ''' Log 3rd party config options '''

        to_log = [App_Settings, MongoDB_Settings, RabbitMQ_Settings, Redis_Settings]
        for config in to_log: 
            for option in config.get_log_data(): print(' * [dead-simple-config]: ' + option)
            print('--')
