from unittest.mock import patch, Mock, MagicMock

import pytest

try:
    from django.db.models.query import QuerySet
except ImportError:
    QuerySet = None

from parasolr.indexing import Indexable
from parasolr.tests.utils import skipif_no_django


# Define Indexable subclasses for testing
# Used for both Indexable and index manage command

class SimpleIndexable(Indexable):
    """simple indexable subclass"""
    id = 'a'

    @classmethod
    def index_item_type(cls):
        return 'simple'

    # nededed for index manage command (assumes django model)
    class objects:
        def count():
            return 5
        def all():
            return [SimpleIndexable() for i in range(5)]


class ModelIndexable(Indexable):
    """mock-model indexable subclass"""
    id = 1

    class _meta:
        verbose_name = 'model'

    # nededed for index manage command
    class objects:
        def count():
            return 1
        def all():
            return [ModelIndexable()]


@skipif_no_django
@patch('parasolr.indexing.SolrClient')
class TestIndexable:

    def test_all_indexables(self, mocksolr):
        indexables = Indexable.all_indexables()
        assert SimpleIndexable in indexables
        assert ModelIndexable in indexables

    def test_index_item_type(self, mocksolr):
        # use model verbose name by default
        assert ModelIndexable().index_item_type() == 'model'

    def test_index_id(self, mocksolr):
        assert SimpleIndexable().index_id() == 'simple.a'
        assert ModelIndexable().index_id() == 'model.1'

    def test_index_data(self, mocksolr):
        model = ModelIndexable()
        data = model.index_data()
        assert data['id'] == model.index_id()
        assert data['item_type'] == model.index_item_type()
        assert len(data) == 2

    def test_index(self, mocksolr):
        # index method on a single object instance
        model = ModelIndexable()
        model.index()
        # NOTE: because solr is stored on the class,
        # mocksolr.return_value is not the same object
        model.solr.update.index.assert_called_with([model.index_data()])

    def test_remove_from_index(self, mocksolr):
        # remove from index method on a single object instance
        model = ModelIndexable()
        model.remove_from_index()
        model.solr.update.delete_by_id.assert_called_with([model.index_id()])

    def test_index_items(self, mocksolr):
        items = [SimpleIndexable() for i in range(10)]

        indexed = Indexable.index_items(items)
        assert indexed == len(items)
        Indexable.solr.update.index \
            .assert_called_with([i.index_data() for i in items])

        # index in chunks
        Indexable.index_chunk_size = 6
        Indexable.solr.reset_mock()
        indexed = Indexable.index_items(items)
        assert indexed == len(items)
        # first chunk
        Indexable.solr.update.index \
            .assert_any_call([i.index_data() for i in items[:6]])
        # second chunk
        Indexable.solr.update.index \
            .assert_any_call([i.index_data() for i in items[6:]])

        # pass in a progressbar object
        mock_progbar = Mock()
        Indexable.index_items(items, progbar=mock_progbar)
        # progress bar update method should be called once for each chunk
        assert mock_progbar.update.call_count == 2

    def test_index_items__queryset(self, mocksolr):
        # index a queryset
        mockqueryset = MagicMock(spec=QuerySet)
        Indexable.index_items(mockqueryset)
        mockqueryset.iterator.assert_called_with()