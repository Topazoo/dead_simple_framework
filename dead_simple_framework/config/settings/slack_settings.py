# Interface class
from .setting import Setting

# Utilities
import os

class Slack_Settings(Setting):
    ''' Used to specify and validate Slack settings '''

    CONFIG_TYPE = 'slack_settings'

    # Slack Config
    USE_SLACK = os.environ.get('USE_SLACK', 'False').capitalize() == 'True'
    APP_SLACK_TOKEN = os.environ.get('APP_SLACK_TOKEN', '')
    APP_SLACK_LOGGING_CHANNEL = os.environ.get('APP_SLACK_LOGGING_CHANNEL', '#logging')

    def __init__(self, use_slack:bool=False, app_slack_token:str=None, app_slack_logging_channel:str=None):

        if use_slack: Slack_Settings.USE_SLACK = use_slack
        if app_slack_token: Slack_Settings.APP_SLACK_TOKEN = app_slack_token
        if app_slack_logging_channel: Slack_Settings.APP_SLACK_LOGGING_CHANNEL = app_slack_logging_channel

    @staticmethod
    def get_log_data():
        ''' Returns a list of the settings to log to console '''

        log_str = 'Slack logging is disabled'
        if Slack_Settings.USE_SLACK and Slack_Settings.APP_SLACK_TOKEN:
            log_str = f'Slack logging is enabled. Errors will be logged to the [{Slack_Settings.APP_SLACK_LOGGING_CHANNEL}] channel'
        elif Slack_Settings.USE_SLACK:
            log_str += ' (set the `APP_SLACK_TOKEN` environmental variable to enable it)'
        else:
            log_str += '. Set `USE_SLACK` to True in environment to enable it' 

        return [log_str]
