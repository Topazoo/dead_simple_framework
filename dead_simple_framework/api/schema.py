# JSONSchema
from jsonschema import validate

# logging
import logging


class SchemaHandler:
    ''' Driver for JSONSchema parsing and validation '''

    def __init__(self, schema:dict):
        self.schema = schema


    @staticmethod
    def validate_schema_structure(schema:dict):
        ''' Validate the structure of a passed schema (TODO) '''

        # TODO - Schema schema validation lol

        return schema


    def validate_request(self, method:str, request:dict):
        ''' Validate a request against the provided schema '''

        if method in self.schema:
            method_schema = self.schema[method].copy()
            method_schema.pop('redact')
            validate(request, method_schema)

        return True


    def _redact(self, fullpath:str, path:list, response_chunk:dict):
        ''' Driver for recursive redaction '''

        if not path: return

        if path[0] not in response_chunk:
            logging.warning(f'Redaction path [{fullpath}] not found in response'); return

        if len(path) == 1:
            del response_chunk[path[0]]; return

        self._redact(fullpath, path[1:], response_chunk[path[0]])

        if not response_chunk[path[0]]:
           del response_chunk[path[0]]


    def redact_response(self, method:str, response:dict):
        ''' Redact a response payload bbased on the provided schema '''

        if method in self.schema:
            method_schema = self.schema[method].copy()
            redactions = method_schema.get('redact', [])

            for redaction in redactions:
                redaction_path = redaction.split('.')
                self._redact(redaction, redaction_path, response)

        return response
