import json
from urllib.parse import urljoin

from parasol.solr.client import ClientBase


class Update(ClientBase):
    """API client for Solr update functionality."""
    def __init__(self, solr_url, collection, handler, commitWithin,
                 session=None):
        """
        :param solr_url: Base url for Solr.
        :type solr_url: str
        :param handler: Handler for Update API.
        :type handler: str
        :param session: A python-requests Session.
        :type session: :class:`requests.Session`
        """
        # Go ahead and create a session if one is not passed in
        super().__init__(session=session)
        self.url = self.build_url(solr_url, collection, handler)
        self.headers = {'Content-Type': 'application/json'}
        self.params = {'commitWithin': commitWithin}

    def index(self, docs, commit=False, commitWithin=None):
        """Index a document or documents, by default with a soft commit.
        :param docs: list of :class:`dict` objects to index.
        :type docs: list
        :param commit: Whether or not to make a hard commit to the index.
        :type commit: bool
        :param commitWithin: Override default commitWithin for soft commits.
        :type commitWithin: int
        """
        params = self.params.copy()
        if commitWithin:
            params['commitWithin'] = commitWithin
        # perform a hard commit, so remove commitWithin as superfluous
        # and set params.
        if commit:
            del params['commitWithin']
            params['commit'] = True
        url = urljoin('%s/' % self.url, 'json/docs')
        self.make_request(
            'post',
            url,
            data=docs,
            params=self.params,
            headers=self.headers
        )

    def _delete(self, del_obj):
        """Private method to pass a delete object to the update handler."""
        data = {'delete': del_obj}
        self.make_request(
            'post',
            self.url,
            data=data,
            params=self.params,
            headers=self.headers
        )

    def delete_by_id(self, id_list):
        """Delete documents by id field.

        :param id_list: A list of ids.
        :type id_list: list
        """
        self._delete(id_list)

    def delete_by_query(self, query):
        """Delete documents by an arbitrary search query.
        :param query: Any valid Solr query.
        :type query: str
        """
        self._delete({'query': query})
