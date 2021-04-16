# Interface class
from .setting import Setting

# Utilities
import os

class Sentry_Settings(Setting):
    ''' Used to specify and validate Sentry settings '''

    CONFIG_TYPE = 'sentry_settings'

    # Sentry Config
    APP_USE_SENTRY = os.environ.get('APP_USE_SENTRY', 'True') == 'True'
    APP_SENTRY_HOST = os.environ.get('APP_SENTRY_HOST', '')
    APP_SENTRY_SLUG = os.environ.get('APP_SENTRY_SLUG', '')

    def __init__(self, app_use_sentry:bool=False, app_sentry_host:str=None, app_sentry_slug:str=None):

        if app_use_sentry: Sentry_Settings.APP_USE_SENTRY = app_use_sentry
        if app_sentry_host: Sentry_Settings.APP_SENTRY_HOST = app_sentry_host
        if app_sentry_slug: Sentry_Settings.APP_SENTRY_SLUG = app_sentry_slug

    @staticmethod
    def get_log_data():
        ''' Returns a list of the settings to log to console '''

        sentry_str = 'Sentry logging is disabled for application'
        if Sentry_Settings.APP_USE_SENTRY and Sentry_Settings.APP_SENTRY_HOST and Sentry_Settings.APP_SENTRY_SLUG:
            sentry_str = 'Sentry logging is enabled for application'
        elif Sentry_Settings.APP_USE_SENTRY:
            if not Sentry_Settings.APP_SENTRY_HOST:
                sentry_str += ' (no APP_SENTRY_HOST set!)'
            if not Sentry_Settings.APP_SENTRY_SLUG:
                sentry_str += ' (no APP_SENTRY_SLUG set!)'

        return [sentry_str]
