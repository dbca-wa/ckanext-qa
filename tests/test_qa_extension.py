from paste.deploy import appconfig
import paste.fixture
import json

from ckan.config.middleware import make_app
from ckan.tests import conf_dir, url_for, CreateTestData
from ckan import model
from ckan.lib.dictization.model_dictize import package_dictize
from ckanext.qa.lib.package_scorer import package_score
from ckanext.qa.dictization import (
    five_stars, broken_resource_links_by_package, 
    broken_resource_links_by_package_for_organisation,
    organisations_with_broken_resource_links,
    organisations_with_broken_resource_links_by_name
)
from ckanext.qa.lib import log
log.create_default_logger()

TEST_ARCHIVE_RESULTS_FILE = 'tests/test_archive_results.db'

class TestQAController:
    @classmethod
    def setup_class(cls):
        config = appconfig('config:test.ini', relative_to=conf_dir)
        config.local_conf['ckan.plugins'] = 'qa'
        wsgiapp = make_app(config.global_conf, **config.local_conf)
        cls.app = paste.fixture.TestApp(wsgiapp)
        CreateTestData.create()
                    
    @classmethod
    def teardown_class(self):
        CreateTestData.delete()
            
    def test_index(self):
        url = url_for('qa')
        response = self.app.get(url)
        assert 'Quality Assurance' in response, response
        
    def test_packages_with_broken_resource_links(self):
        url = url_for('qa_package_action', action='broken_resource_links')
        response = self.app.get(url)
        assert 'broken resource.' in response, response
        
    def test_package_openness_scores(self):
        context = {'model': model, 'session': model.Session}
        for p in model.Session.query(model.Package):
            context['id'] = p.id
            p = package_dictize(p, context)
            package_score(p, TEST_ARCHIVE_RESULTS_FILE)
        url = url_for('qa_package_action', action='five_stars')
        response = self.app.get(url)
        assert 'openness scores' in response, response

    def test_qa_in_package_read(self):
        pkg_id = model.Session.query(model.Package).first().id
        url = url_for(controller='package', action='read', id=pkg_id)
        response = self.app.get(url)
        assert 'qa.js' in response, response
        assert '/ckanext/qa/style.css' in response, response

    def test_resource_available_api_exists(self):
        pkg_id = model.Session.query(model.Package).first().id
        url = url_for('qa_api_resources_available', id=pkg_id)
        response = self.app.get(url)
        # make sure that the response content type is JSON
        assert response.header('Content-Type') == "application/json", response
        # make sure that the response contains the expected keys
        response_json = json.loads(response.body)
        assert 'resources' in response_json.keys(), response_json
        for resource in response_json['resources']:
            assert 'resource_hash' in resource.keys(), resource
            assert 'resource_available' in resource.keys(), resource
            assert 'resource_cache' in resource.keys(), resource

    def test_broken_resource_links_by_package(self):
        pass
