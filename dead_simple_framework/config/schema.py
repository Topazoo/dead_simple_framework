# JSONSchema
from json import dumps
from jsonschema import validate
from jsonschema.exceptions import ValidationError

# Errors
from ..api.errors import API_Error

# Flask
from flask import Response

# Logging
import logging


class SchemaHandler:
    ''' Driver for JSONSchema parsing and validation '''

    def __init__(self, schema:dict=None):
        self.schema = self.validate_schema_structure(schema) if schema else {}


    @staticmethod
    def validate_schema_structure(schema:dict):
        ''' Validate the structure of a passed schema (TODO) '''

        # TODO - Schema schema validation lol

        return schema


    def validate_request(self, route:str, method:str, request:dict):
        ''' Validate a request against the provided schema '''

        if method in self.schema:
            method_schema = self.schema[method].copy()
            if 'redact' in method_schema: method_schema.pop('redact')
            if 'filter' in request: request.update(request.pop('filter'))
            for op in ['$and', '$or']:
                if op in request:
                    for chunk in request[op]:
                        self.validate_request(route, method, chunk)
                    return True

            try:
                validate(request, method_schema)
            except ValidationError as e:
                raise API_Error(f'Schema validation for [{method}] request to route [{route}] failed! Error: {e.message} Schema: {method_schema}', 400)

        return True


    def _redact(self, fullpath:str, path:list, response_chunk:dict):
        ''' Driver for recursive redaction '''

        if not path: return

        if path[0] not in response_chunk:
            logging.warning(f'Redaction path [{fullpath}] not found in response'); return

        if len(path) == 1:
            del response_chunk[path[0]]; return

        if not isinstance(response_chunk[path[0]], list):
            self._redact(fullpath, path[1:], response_chunk[path[0]])
        else:
            [self._redact(fullpath, path[1:], response_chunk_item) for response_chunk_item in response_chunk[path[0]]]

        if not response_chunk[path[0]]:
           del response_chunk[path[0]]


    def redact_response(self, method:str, response:Response):
        ''' Redact a response payload bbased on the provided schema '''

        data = response.get_json()
        if method in self.schema:
            method_schema = self.schema[method].copy()
            redactions = method_schema.get('redact', [])

            for redaction in redactions:
                redaction_path = redaction.split('.')
                self._redact(redaction, redaction_path, data)

        response.set_data(dumps(data))
        return response
