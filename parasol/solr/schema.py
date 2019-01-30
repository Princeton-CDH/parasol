from urllib.parse import urljoin

class Schema:
    '''Class for managing Solr schema API.'''
    def __init__(self, client):

        self.client = client
        self.url = self.client.build_url(client.schema_handler)
        self.headers = {
            'Content-type': 'application/json'
        }

    def _post_field(self, method, **field_kwargs):
        '''Post a field definition to the schema API'''
        data = {
            method: field_kwargs
        }
        self.client.make_request(
            'post',
            self.url,
            headers=self.headers,
            data=data
        )

    def add_field(self, **field_kwargs):
        '''Add a field with the supplied kwargs (or dict as kwargs)'''
        self._post_field('add-field', **field_kwargs)

    def delete_field(self, name):
        '''Delete a field with the supplied kwargs (or dict as kwargs)'''
        self._post_field('delete-field', name=name)

    def replace_field(self, **field_kwargs):
        '''Replace a field with the supplied kwargs (or dict as kwargs)'''
        # NOTE: Requires a full field definition, no partial updates
        self._post_field('replace-field', **field_kwargs)

    def add_copy_field(self, source, dest, max_chars=None):
        field_definition = {
            'source': source,
            'dest': dest
        }
        if max_chars:
            field_definition.max_chars = max_chars
        self._post_field('add-copy-field', field_definition)

    def delete_copy_field(self, source, dest):
        self._post_field('delete-copy-field', {'source': source, 'dest': dest})

    def add_field_type(self, **field_kwargs):
        '''Add a field type to the Solr collection or core.'''
        self._post_field('add-field-type', **field_kwargs)

    def delete_field_type(self, name):
       '''Delete a field type from the Solr collection or core'''
       self._post_field('delete-field-type', name=name)

    def replace_field_type(self, **field_kwargs):
        '''Provide a full definition to replace a field'''
        # NOTE: Requires a full field-type definition, no partial updates
        self._post_field('replace-field-type', **field_kwargs)

    def get_schema(self):
        '''Get the full schema for a Solr collection or core.'''
        response = self.client.make_request('get', self.url)
        if response:
            return response.json()

    def list_fields(self, fields=None, include_dynamic=False):
        '''Get a list of field definitions for a Solr Collection or core.'''
        url = urljoin('%s/' % self.url, 'fields')
        params = {}
        if fields:
            params['fields'] = fields
        params['includeDynamic'] = False
        response = self.client.make_request('get', url, params=params)
        if response:
            return response.json()

    def list_field_types(self, show_defaults=False):
        '''List all field types in a Solr collection or core.'''
        url = urljoin('%s/' % self.url, 'fieldtypes')
        params = {}
        params['showDefaults'] = show_defaults
        response = self.client.make_request('get', url, params=params)
        if response:
            return response.json()




