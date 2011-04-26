import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

TEST_RUNNER='geonode.testrunner.GeoNodeNoseTestRunner'

GEOSERVER_BASE_URL='http://localhost:8001/geoserver-geonode-dev/'

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                         'NAME': os.path.join(PROJECT_ROOT, 'development.db'),
                         'TEST_NAME': os.path.join(PROJECT_ROOT,
                                                   'development.db')}}

NOSE_ARGS = [
#      '--failed',
#      '--stop',
      '--verbosity=2',
      '--cover-erase',
      '--with-doctest',
      '--nocapture',
      '--with-coverage',
      '--cover-package=risiko,impact,geonode',
      '--cover-inclusive',
      '--cover-tests',
      '--detailed-errors',
      '--with-xunit',
#      '--with-color',
#      '--with-pdb',
      ]
