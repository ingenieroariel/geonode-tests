from django.conf import settings
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

import geonode.maps.models

from geonode.maps.models import Layer
from geonode.maps.utils import upload, file_upload, GeoNodeException

from geoserver.catalog import FailedRequestError

from geonode.maps.gs_helpers import cascading_delete

import os
import urllib2

TEST_DATA = os.path.join(settings.PROJECT_ROOT, 'geonode_test_data')


def check_layer(uploaded):
    """Verify if an object is a valid Layer.
    """
    msg = ('Was expecting layer object, got %s' % (type(uploaded)))
    assert type(uploaded) is Layer, msg
    msg = ('The layer does not have a valid name: %s' % uploaded.name)
    assert len(uploaded.name) > 0, msg


def get_web_page(url, username=None, password=None):
    """Get url page possible with username and password.
    """

    if username is not None:

        # Create password manager
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, username, password)

        # create the handler
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

    try:
        pagehandle = urllib2.urlopen(url)
    except HTTPError, e:
        msg = ('The server couldn\'t fulfill the request. '
                'Error code: ' % e.code)
        e.args = (msg,)
        raise
    except urllib2.URLError, e:
        msg = 'Could not open URL "%s": %s' % (url, e)
        e.args = (msg,)
        raise
    else:
        page = pagehandle.readlines()

    return page


class GeoNodeMapTest(TestCase):
    """Tests geonode.maps app/module
    """

    fixtures = ['test_data.json', 'map_data.json']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # maps/models.py tests

    def test_layer_delete_from_geoserver(self):
        """Verify that layer is correctly deleted from GeoServer
        """
        # Layer.delete_from_geoserver() uses cascading_delete()
        # Should we explicitly test that the styles and store are
        # deleted as well as the resource itself?
        # There is already an explicit test for cascading delete

        gs_cat = Layer.objects.gs_catalog

        # Test Uploading then Deleting a Shapefile from GeoServer
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
        shp_store = gs_cat.get_store(shp_layer.name)
        shp_layer.delete_from_geoserver()
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(shp_layer.name, store=shp_store))

        shp_layer.delete()

        # Test Uploading then Deleting a TIFF file from GeoServer
        tif_file = os.path.join(TEST_DATA, 'test_grid.tif')
        tif_layer = file_upload(tif_file)
        tif_store = gs_cat.get_store(tif_layer.name)
        tif_layer.delete_from_geoserver()
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(shp_layer.name, store=tif_store))

        tif_layer.delete()

    def test_layer_delete_from_geonetwork(self):
        """Verify that layer is correctly deleted from GeoNetwork
        """

        gn_cat = Layer.objects.gn_catalog

        # Test Uploading then Deleting a Shapefile from GeoNetwork
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
        shp_layer.delete_from_geonetwork()
        shp_layer_info = gn_cat.get_by_uuid(shp_layer.uuid)
        assert shp_layer_info == None

        # Clean up and completely delete the layer
        shp_layer.delete()

        # Test Uploading then Deleting a TIFF file from GeoNetwork
        tif_file = os.path.join(TEST_DATA, 'test_grid.tif')
        tif_layer = file_upload(tif_file)
        tif_layer.delete_from_geonetwork()
        tif_layer_info = gn_cat.get_by_uuid(tif_layer.uuid)
        assert tif_layer_info == None

        # Clean up and completely delete the layer
        tif_layer.delete()

    def test_delete_layer(self):
        """Verify that the 'delete_layer' pre_delete hook is functioning
        """

        gs_cat = Layer.objects.gs_catalog
        gn_cat = Layer.objects.gn_catalog

        # Upload a Shapefile Layer
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
        shp_layer_id = shp_layer.pk
        shp_store = gs_cat.get_store(shp_layer.name)
        shp_store_name = shp_store.name

        id = shp_layer.pk
        name = shp_layer.name
        uuid = shp_layer.uuid

        # Delete it with the Layer.delete() method
        shp_layer.delete()

        # Verify that it no longer exists in GeoServer
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(name, store=shp_store))
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_store(shp_store_name))

        # Verify that it no longer exists in GeoNetwork
        shp_layer_gn_info = gn_cat.get_by_uuid(uuid)
        assert shp_layer_gn_info == None

        # Check that it was also deleted from GeoNodes DB
        self.assertRaises(ObjectDoesNotExist,
            lambda: Layer.objects.get(pk=shp_layer_id))

    # maps/utils.py tests

    def test_layer_upload(self):
        """Test that layers can be uploaded to running GeoNode/GeoServer
        """
        layers = {}
        expected_layers = []
        not_expected_layers = []
        datadir = TEST_DATA
        BAD_LAYERS = [
            'lembang_schools_percentage_loss.shp',
        ]

        for filename in os.listdir(datadir):
            basename, extension = os.path.splitext(filename)
            if extension.lower() in ['.tif', '.shp', '.zip']:
                if filename not in BAD_LAYERS:
                    expected_layers.append(os.path.join(datadir, filename))
                else:
                    not_expected_layers.append(
                                    os.path.join(datadir, filename)
                                             )
        uploaded = upload(datadir)

        for item in uploaded:
            errors = 'errors' in item
            if errors:
                # should this file have been uploaded?
                if item['file'] in not_expected_layers:
                    continue
                msg = 'Could not upload %s. ' % item['file']
                assert errors is False, msg + 'Error was: %s' % item['errors']
                msg = ('Upload should have returned either "name" or '
                  '"errors" for file %s.' % item['file'])
            else:
                assert 'name' in item, msg
                layers[item['file']] = item['name']

        msg = ('There were %s compatible layers in the directory,'
               ' but only %s were sucessfully uploaded' %
               (len(expected_layers), len(layers)))
        assert len(layers) == len(expected_layers), msg

        uploaded_layers = [layer for layer in layers.items()]

        for layer in expected_layers:
            msg = ('The following file should have been uploaded'
                   'but was not: %s. ' % layer)
            assert layer in layers, msg

            layer_name = layers[layer]

            # Check the layer is in the Django database
            Layer.objects.get(name=layer_name)

            # Check that layer is in geoserver
            found = False
            gs_username, gs_password = settings.GEOSERVER_CREDENTIALS
            page = get_web_page(os.path.join(settings.GEOSERVER_BASE_URL,
                                             'rest/layers'),
                                             username=gs_username,
                                             password=gs_password)
            for line in page:
                if line.find('rest/layers/%s.html' % layer_name) > 0:
                    found = True
            if not found:
                msg = ('Upload could not be verified, the layer %s is not '
                   'in geoserver %s, but GeoNode did not raise any errors, '
                   'this should never happen.' %
                   (layer_name, settings.GEOSERVER_BASE_URL))
                raise GeoNodeException(msg)

        server_url = settings.GEOSERVER_BASE_URL + 'ows?'
        # Verify that the GeoServer GetCapabilities record is accesible:
        #metadata = get_layers_metadata(server_url, '1.0.0')
        #msg = ('The metadata list should not be empty in server %s'
        #        % server_url)
        #assert len(metadata) > 0, msg
        # Check the keywords are recognized too

        # Clean up and completely delete the layers
        for layer in expected_layers:
            layer_name = layers[layer]
            Layer.objects.get(name=layer_name).delete()

    def test_extension_not_implemented(self):
        """Verify a GeoNodeException is returned for not compatible extensions
        """
        sampletxt = os.path.join(TEST_DATA,
            'lembang_schools_percentage_loss.dbf')
        try:
            file_upload(sampletxt)
        except GeoNodeException, e:
            pass
        except Exception, e:
            msg = ('Was expecting a %s, got %s instead.' %
                   (GeoNodeException, type(e)))
            assert e is GeoNodeException, msg


    def test_shapefile(self):
        """Test Uploading a good shapefile
        """
        thefile = os.path.join(TEST_DATA, 'lembang_schools.shp')
        uploaded = file_upload(thefile)
        check_layer(uploaded)

        # Clean up and completely delete the layer
        uploaded.delete()

    def test_bad_shapefile(self):
        """Verifying GeoNode complains about a shapefile without .prj
        """

        thefile = os.path.join(TEST_DATA, 'lembang_schools_percentage_loss.shp')
        try:
            uploaded = file_upload(thefile)
        except GeoNodeException, e:
            pass
        except Exception, e:
            msg = ('Was expecting a %s, got %s instead.' %
                   (GeoNodeException, type(e)))
            assert e is GeoNodeException, msg


    def test_tiff(self):
        """Uploading a good .tiff
        """
        thefile = os.path.join(TEST_DATA, 'test_grid.tif')
        uploaded = file_upload(thefile)
        check_layer(uploaded)

        # Clean up and completely delete the layer
        uploaded.delete()
    
    def test_repeated_upload(self):
        """Upload the same file more than once
        """
        thefile = os.path.join(TEST_DATA, 'test_grid.tif')
        uploaded1 = file_upload(thefile)
        check_layer(uploaded1)
        uploaded2 = file_upload(thefile, overwrite=True)
        check_layer(uploaded2)
        uploaded3 = file_upload(thefile, overwrite=False)
        check_layer(uploaded3)
        msg = ('Expected %s but got %s' % (uploaded1.name, uploaded2.name))
        assert uploaded1.name == uploaded2.name, msg
        msg = ('Expected a different name when uploading %s using '
               'overwrite=False but got %s' % (thefile, uploaded3.name))
        assert uploaded1.name != uploaded3.name, msg

        # Clean up and completely delete the layers

        # uploaded1 is overwritten by uploaded2 ... no need to delete it
        uploaded2.delete()
        uploaded3.delete()
    
    # gs_helpers tests

    def test_fixup_style(self):
        pass

    def test_cascading_delete(self):
        """Verify that the gs_helpers.cascading_delete() method is working properly
        """
        gs_cat = Layer.objects.gs_catalog

        # Upload a Shapefile
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
       
        # Save the names of the Resource/Store/Styles 
        resource_name = shp_layer.resource.name
        store = shp_layer.resource.store
        store_name = store.name
        layer = gs_cat.get_layer(resource_name)
        styles = layer.styles + [layer.default_style]
        
        # Delete the Layer using cascading_delete()
        cascading_delete(gs_cat, shp_layer.resource)
        
        # Verify that the styles were deleted
        for style in styles:
            s = gs_cat.get_style(style)
            assert s == None
        
        # Verify that the resource was deleted
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_resource(resource_name, store=store))

        # Verify that the store was deleted 
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_store(store_name))

        # Clean up by deleting the layer from GeoNode's DB and GeoNetwork
        shp_layer.delete()
