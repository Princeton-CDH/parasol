import logging

import pytest

try:
    import django
    from django.conf import settings
    from django.test import override_settings
except ImportError:
    django = None

from parasol import django
from parasol.schema import SolrSchema


logger = logging.getLogger(__name__)


if django:

    @pytest.fixture(autouse=True, scope="session")
    def configure_django_test_solr():
        """Automatically configure the default Solr to use a test
        core based on the configured **SOLR_CONNECTIONS**.  Will use
        test name if specified (using the same structure as Django
        DATABASES), or prepend "test_" to the configured COLLECTION
        if no test name is set. The test core will be created and
        schema configured before starting, and unloaded after tests
        complete.  Example configuration::

            SOLR_CONNECTIONS = {
                'default': {
                    'URL': 'http://localhost:8983/solr/',
                    'COLLECTION': 'myproj',
                    'TEST': {
                        'NAME': 'testproj',
                        }
                }
            }

        """

        solr_config_opts = settings.SOLR_CONNECTIONS['default'].copy()
        # use test settings as primary
        if 'TEST' in settings.SOLR_CONNECTIONS['default']:
            # anything in test settings should override default settings
            solr_config_opts.update(settings.SOLR_CONNECTIONS['default']['TEST'])

        # if test collection is not explicitly configured,
        # set it based on default collection
        if 'COLLECTION' not in settings.SOLR_CONNECTIONS['default']['TEST']:
            solr_config_opts['COLLECTION'] = 'test_%s' % \
                settings.SOLR_CONNECTIONS['default']['COLLECTION']


        logger.info('Configuring Solr for tests %(URL)s%(COLLECTION)s',
                    solr_config_opts)

        with override_settings(SOLR_CONNECTIONS={'default': solr_config_opts}):
            # reload core before and after to ensure field list is accurate
            solr = django.SolrClient(commitWithin=10)
            response = solr.core_admin.status(core=solr_config_opts['COLLECTION'])
            if not response.status.get(solr_config_opts['COLLECTION'], None):
                solr.core_admin.create(solr_config_opts['COLLECTION'], configSet='basic_configs')

            try:
                # if a schema is configured, update the test core
                schema_config = SolrSchema.get_configuration()
                schema_config.configure_fieldtypes(solr)
                schema_config.configure_fields(solr)
            except Exception:
                pass

            # yield settings so tests run with overridden solr connection
            yield settings

            # clear out any data indexed in test collection
            solr.update.delete_by_query('*:*')
            # and unload
            solr.core_admin.unload(
                solr_config_opts['COLLECTION'],
                deleteInstanceDir=True,
                deleteIndex=True,
                deleteDataDir=True
            )