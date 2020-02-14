#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for scrapername.

'''
from os.path import join

import pytest
from hdx.data.vocabulary import Vocabulary
from hdx.hdx_configuration import Configuration
from hdx.hdx_locations import Locations
from hdx.location.country import Country
from hdx.utilities.path import temp_dir

from who import generate_dataset_and_showcase, get_countries, get_indicators_and_tags


class TestWHO:
    indicators = [('WHOSIS_000001', 'Life expectancy at birth (years)',
                   'http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65')]

    country = {'display_sequence': 10, 'url': '', 'display': 'Afghanistan',
               'attr': [{'category': 'WORLD_BANK_INCOME_GROUP_GNI_REFERENCE_YEAR', 'value': '2015'},
                        {'category': 'WORLD_BANK_INCOME_GROUP_RELEASE_DATE', 'value': '2016'},
                        {'category': 'WHO_REGION', 'value': 'Eastern Mediterranean'},
                        {'category': 'WORLD_BANK_INCOME_GROUP', 'value': 'Low-income'},
                        {'category': 'WHO_REGION_CODE', 'value': 'EMR'}, {'category': 'WORLD_BANK_INCOME_GROUP_CODE', 'value': 'WB_LI'},
                        {'category': 'DS', 'value': 'AFG'}, {'category': 'FIPS', 'value': 'AF'},  {'category': 'IOC', 'value': 'AFG'},
                        {'category': 'ISO2', 'value': 'AF'}, {'category': 'ISO', 'value': 'AFG'}, {'category': 'ITU', 'value': 'AFG'},
                        {'category': 'MARC', 'value': 'af'}, {'category': 'WHO', 'value': 'AFG'}, {'category': 'WMO', 'value': 'AF'},
                        {'category': 'GEOMETRY', 'value': 'AFG'}, {'category': 'MORT', 'value': '3010'},
                        {'category': 'LAND_AREA_KMSQ_2012', 'value': '652,230'},
                        {'category': 'LANGUAGES_EN_2012', 'value': 'Dari, Pashto, Turkic languages, 30 minor languages'},
                        {'category': 'SHORTNAMEES', 'value': 'Afganistan'}, {'category': 'SHORTNAMEFR', 'value': 'Afghanistan'},
                        {'category': 'WHOLEGALSTATUS', 'value': 'M'}], 'label': 'AFG'}

    @pytest.fixture(scope='function')
    def configuration(self):
        Configuration._create(hdx_read_only=True, user_agent='test',
                              project_config_yaml=join('tests', 'config', 'project_configuration.yml'))
        Locations.set_validlocations([{'name': 'afg', 'title': 'Afghanistan'}])
        Country.countriesdata(use_live=False)
        Vocabulary._tags_dict = {'sustainable development goals': {'Action to Take': 'merge', 'New Tag(s)': 'sustainable development goals - sdg'}}
        Vocabulary._approved_vocabulary = {'tags': [{'name': 'hxl'}, {'name': 'indicators'}, {'name': 'health'}, {'name': 'demographics'}, {'name': 'sustainable development goals - sdg'}], 'id': '4e61d464-4943-4e97-973a-84673c1aaa87', 'name': 'approved'}

    @pytest.fixture(scope='function')
    def downloader(self):
        class Response:
            @staticmethod
            def json():
                pass

        class Download:
            @staticmethod
            def download(url):
                response = Response()
                if url == 'http://lala/api/GHO?format=json':
                    def fn():
                        return {'dimension': [{'code': [{'display': 'Life expectancy at birth (years)',
                                                         'url': 'http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65',
                                                         'attr': [{'category': 'DISPLAY_FR', 'value': 'Esperance de vie a la naissance (ans)'},
                                                                  {'category': 'DISPLAY_ES', 'value': 'Esperanza de vida al nacer'},
                                                                  {'category': 'DEFINITION_XML', 'value': 'http://apps.who.int/gho/indicatorregistryservice/publicapiservice.asmx/IndicatorGetAsXml?profileCode=WHO&applicationCode=System&languageAlpha2=en&indicatorId=65'},
                                                                  {'category': 'CATEGORY', 'value': 'Sustainable development goals'},
                                                                  {'category': 'CATEGORY', 'value': 'health and demographics'},
                                                                  {'category': 'RENDERER_ID', 'value': 'RENDER_2'}],
                                                         'display_sequence': 10, 'label': 'WHOSIS_000001'}]}]}
                    response.json = fn
                elif url == 'http://haha/api/COUNTRY?format=json':
                    def fn():
                        return {'dimension': [{'code': [TestWHO.country]}]}
                    response.json = fn
                return response

            @staticmethod
            def get_tabular_rows(url, **kwargs):
                if url == 'http://papa/data/data-verbose.csv?target=GHO/WHOSIS_000001&filter=COUNTRY:AFG&profile=verbose':
                    return ['GHO (CODE)', 'header2', 'YEAR (CODE)'], \
                           [{'GHO (CODE)': 'WHS7_104', 'header2': 'val21', 'YEAR (CODE)': '1992'},
                            {'GHO (CODE)': 'MDG_0000000001', 'header2': 'val22', 'YEAR (CODE)': '2015'}]

            @staticmethod
            def hxl_row(headers, hxltags, dict_form):
                return {header: hxltags.get(header, '') for header in headers}

        return Download()

    def test_get_indicators_and_tags(self, configuration, downloader):
        indicators, tags = get_indicators_and_tags('http://lala/', downloader)
        assert indicators == TestWHO.indicators
        assert tags == ['sustainable development goals - sdg', 'health', 'demographics']

    def test_get_countriesdata(self, downloader):
        countriesdata = get_countries('http://haha/', downloader)
        assert countriesdata == [TestWHO.country]

    def test_generate_dataset_and_showcase(self, configuration, downloader):
        configuration = Configuration.read()
        base_url = configuration['base_url']
        with temp_dir('WHO') as folder:
            dataset, showcase, bites_disabled = generate_dataset_and_showcase(base_url, downloader, folder,
                                                                              TestWHO.country, TestWHO.indicators)
            assert dataset == {'name': 'who-data-for-afghanistan',
                               'notes': "Contains data from World Health Organization's [data portal](http://www.who.int/gho/en/) covering the following indicators:  \n[Life expectancy at birth (years)](http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65)",
                               'title': 'Afghanistan - Health Indicators', 'groups': [{'name': 'afg'}],
                               'maintainer': '196196be-6037-4488-8b71-d786adf4c081', 'owner_org': 'hdx',
                               'data_update_frequency': '365', 'subnational': '0',
                               'tags': [{'name': 'hxl', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'indicators', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}],
                               'dataset_date': '01/01/1992-12/31/2015'}

            resources = dataset.get_resources()
            assert resources == [{'name': 'Health Indicators for Afghanistan', 'description': 'See dataset description for links to indicator metadata',
                                  'format': 'csv', 'resource_type': 'file.upload', 'url_type': 'upload'}]

            assert showcase == {'image_url': 'http://www.who.int/sysmedia/images/countries/afg.gif',
                                'url': 'http://www.who.int/countries/afg/en/',
                                'notes': 'Health indicators for Afghanistan', 'name': 'who-data-for-afghanistan-showcase',
                                'tags': [{'name': 'hxl', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'indicators', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}],
                                'title': 'Indicators for Afghanistan'}
            assert bites_disabled == [True, False, False]
            datasetshowcase = generate_dataset_and_showcase(base_url, downloader, folder, {'label': 'xxx', 'display': 'Unknown', 'attr': []}, TestWHO.indicators)
            assert datasetshowcase == (None, None, None)

