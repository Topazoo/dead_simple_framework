
# Individual configs
from . import App_Settings, MongoDB_Settings, RabbitMQ_Settings, Redis_Settings, Slack_Settings, JWT_Settings, Sentry_Settings

# Typing
from typing import Union

class Settings(App_Settings, MongoDB_Settings, RabbitMQ_Settings, Redis_Settings, Slack_Settings, JWT_Settings, Sentry_Settings):
    ''' Used to specify and validate all application settings '''

    def __init__(self, 
                 app_settings:Union[dict, App_Settings]=None, 
                 mongodb_settings:Union[dict, MongoDB_Settings]=None, 
                 rabbitmq_settings:Union[dict, RabbitMQ_Settings]=None,
                 redis_settings:Union[dict, Redis_Settings]=None,
                 slack_settings:Union[dict, Slack_Settings]=None,
                 jwt_settings:Union[dict, JWT_Settings]=None,
                 sentry_settings:Union[dict, Sentry_Settings]=None,
            ):


        if isinstance(app_settings, dict): App_Settings.from_dict('app_settings', app_settings)
        if app_settings == None: App_Settings()

        if isinstance(mongodb_settings, dict): MongoDB_Settings.from_dict('mongodb_settings', mongodb_settings)
        if mongodb_settings == None: MongoDB_Settings()
        
        if isinstance(rabbitmq_settings, dict): RabbitMQ_Settings.from_dict('rabbitmq_settings', rabbitmq_settings)
        if rabbitmq_settings == None: RabbitMQ_Settings()
        
        if isinstance(redis_settings, dict): Redis_Settings.from_dict('redis_settings', redis_settings)
        if redis_settings == None: Redis_Settings()

        if isinstance(slack_settings, dict): Slack_Settings.from_dict('slack_settings', slack_settings)
        if slack_settings == None: Slack_Settings()

        if isinstance(jwt_settings, dict): JWT_Settings.from_dict('jwt_settings', jwt_settings)
        if jwt_settings == None: JWT_Settings()

        if isinstance(sentry_settings, dict): Sentry_Settings.from_dict('sentry_settings', sentry_settings)
        if sentry_settings == None: Sentry_Settings()


    @staticmethod
    def log_config():
        ''' Log 3rd party config options '''

        to_log = [App_Settings, JWT_Settings, MongoDB_Settings, Slack_Settings, Sentry_Settings, RabbitMQ_Settings, Redis_Settings]
        for config in to_log: 
            for option in config.get_log_data(): print(' * [dead-simple-config]: ' + option)
            print('--')
