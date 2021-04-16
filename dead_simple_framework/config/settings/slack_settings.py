# Interface class
from .setting import Setting

# Utilities
import os

class Slack_Settings(Setting):
    ''' Used to specify and validate Slack settings '''

    CONFIG_TYPE = 'slack_settings'

    # Slack Config
    APP_USE_SLACK = os.environ.get('APP_USE_SLACK', 'False') == 'True'
    APP_SLACK_TOKEN = os.environ.get('APP_SLACK_TOKEN', '')
    APP_SLACK_DEFAULT_USER = os.environ.get('APP_SLACK_DEFAULT_USER', '')

    def __init__(self, app_use_slack:bool=False, app_slack_token:str=None, app_slack_default_user:str=None):

        if app_use_slack: Slack_Settings.APP_USE_SLACK = app_use_slack
        if app_slack_token: Slack_Settings.APP_SLACK_TOKEN = app_slack_token
        if app_slack_default_user: Slack_Settings.APP_SLACK_DEFAULT_USER = app_slack_default_user

    @staticmethod
    def get_log_data():
        ''' Returns a list of the settings to log to console '''

        log_str = 'Slack logging is disabled'
        if Slack_Settings.APP_USE_SLACK and Slack_Settings.APP_SLACK_TOKEN:
            log_str = 'Slack logging is enabled - No default user specified'
            if Slack_Settings.APP_SLACK_DEFAULT_USER:
                log_str += f' - Default user [{Slack_Settings.APP_SLACK_DEFAULT_USER}]'
        elif Slack_Settings.APP_USE_SLACK:
            log_str += ' (No APP_SLACK_TOKEN set!)'

        return [log_str]
