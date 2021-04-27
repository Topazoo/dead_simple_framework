# Clients
from slack_sdk.web.client import WebClient

# Settings
from .config.settings.slack_settings import Slack_Settings

# Utils
from sentry_sdk.api import capture_exception
from traceback import format_tb
from pprint import pformat

# Typing
from dead_simple_framework.api.errors import API_Error


class Slack:
    ''' Client for sending Slack messages '''

    def __init__(self, token:str=None, default_channel:str=None):

        # Rely on system token if one wasn't passed
        if not token:
            token = Slack_Settings.APP_SLACK_TOKEN

        # Create internal client to serve as an adapter for
        self._client = WebClient(token=token)

        # Set the default channel
        self.default_channel = Slack_Settings.APP_SLACK_LOGGING_CHANNEL if not default_channel else default_channel


    def send_message(self, message:str, channel:str=None, thread_id:str=None) -> str:
        ''' Sends a message to the passed Slack channel and returns the thread ID. Posts as a reply if  `thread_id` is passed'''

        # Fall back on the default channel if a channel name isn't immediately passed 
        if not channel:
            channel = self.default_channel

        # Ensure the channel name starts with '#'
        if channel[0] != '#':
            channel = f'#{channel}'

        try:
            # Send the message to the channel
            response = self._client.api_call(
                api_method='chat.postMessage',
                json={'channel': channel,'text': message, **({} if not thread_id else {'thread_ts': thread_id})},
            )

            # Log errors
            if not response or 'error' in response:
                capture_exception(Exception(f"Slack logging error: {response['error']}"))
                return None

            # Return the thread ID
            return response.get('ts')

        # Catch and log any exceptions thrown when logging
        except Exception as e:
            capture_exception(e)


    def log_api_exception(self, error:API_Error, endpoint:str, payload:dict, channel:str=None, thread_title:str=None):
        ''' Log an API level exception to Slack with supplementary information '''

        # Generate top level message for the error thread if one was not passed
        if not thread_title:
            emoji = ':broken_wifi:' if str(error.code)[0] != '4' else ':large_yellow_circle:'
            thread_title = f'{emoji} API Error: `{error.code}`\n:api: Endpoint: `{endpoint}`\n:speech_balloon: Error: `{error.message}`'

        # Post the message and get the ID of the thread
        thread_id = self.send_message(thread_title, channel)

        # Only post replies if the last post succeeded
        if thread_id:

            # Prettify paylod data for Slack
            payload_reply = f':package: Payload:\n```{pformat(payload)}```'

            # Post the payload as a reply
            replied = self.send_message(payload_reply, channel, thread_id)

            # Only post replies if the last post succeeded
            if replied:

                # Prettify traceback data for Slack
                traceback_reply = f':mag: Traceback:\n```{"".join(format_tb(error.__traceback__))}```'

                # Post the traceback as a reply
                self.send_message(traceback_reply, channel, thread_id)


    def log_exception(self, error:Exception, channel:str=None, thread_title:str=None, endpoint:str= None, payload:dict=None):
        ''' Log an exception to Slack with supplementary information '''

        # Generate top level message for the error thread if one was not passed
        if not thread_title:
            thread_title = f':x: Exception: `{error.args[0]}`'

            if endpoint:
                thread_title += f'\n:api: Endpoint: `{endpoint}`'

        # Post the message and get the ID of the thread
        thread_id = self.send_message(thread_title, channel)

        # Only post replies if the last post succeeded
        if thread_id and payload:

            # Prettify paylod data for Slack
            payload_reply = f':package: Payload:\n```{pformat(payload)}```'

            # Post the payload as a reply
            self.send_message(payload_reply, channel, thread_id)

        if thread_id:

            # Prettify traceback data for Slack
            traceback_reply = f':mag: Traceback:\n```{"".join(format_tb(error.__traceback__))}```'

            # Post the traceback as a reply
            self.send_message(traceback_reply, channel, thread_id)
     