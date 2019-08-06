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

from who import generate_dataset_and_showcase, get_countriesdata, get_indicators_and_tags


class TestWHO:
    indicators = [('WHOSIS_000001', 'Life expectancy at birth (years)',
                   'http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65')]

    countrydata = {'display_sequence': 10, 'url': '', 'display': 'Afghanistan',
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
        Vocabulary._approved_vocabulary = {'tags': [{'name': 'hxl'}, {'name': 'health'}, {'name': 'demographics'}, {'name': 'sustainable development goals - sdg'}], 'id': '4e61d464-4943-4e97-973a-84673c1aaa87', 'name': 'approved'}

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
                if url == 'http://lala/GHO?format=json':
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
                elif url == 'http://haha/COUNTRY?format=json':
                    def fn():
                        return {'dimension': [{'code': [TestWHO.countrydata]}]}
                    response.json = fn
                return response

            @staticmethod
            def get_tabular_rows(url, dict_rows, headers):
                if url == 'http://papa/GHO/WHOSIS_000001.csv?filter=COUNTRY:AFG&profile=verbose':
                    return [{'header1': 'val11', 'header2': 'val21', 'YEAR (CODE)': '1992'},
                            {'header1': 'val12', 'header2': 'val22', 'YEAR (CODE)': '2015'}]
                elif url == 'http://papa/GHO/lala.csv?filter=COUNTRY:AFG&profile=verbose':
                    raise Exception('Error!')

        return Download()

    def test_get_indicators_and_tags(self, configuration, downloader):
        indicators, tags = get_indicators_and_tags('http://lala/', downloader, ['WHOSIS_000001'])
        assert indicators == TestWHO.indicators
        assert tags == ['sustainable development goals - sdg', 'health', 'demographics']

    def test_get_countriesdata(self, downloader):
        countriesdata = get_countriesdata('http://haha/', downloader)
        assert countriesdata == [TestWHO.countrydata]

    def test_generate_dataset_and_showcase(self, configuration, downloader):
        base_url = Configuration.read()['base_url']
        dataset, showcase = generate_dataset_and_showcase(base_url, downloader, TestWHO.countrydata, TestWHO.indicators)
        assert dataset == {'groups': [{'name': 'afg'}], 'title': 'Afghanistan - Health Indicators',
                           'data_update_frequency': '365', 'dataset_date': '01/01/1992-12/31/2015',
                           'name': 'who-data-for-afghanistan', 'maintainer': '196196be-6037-4488-8b71-d786adf4c081',
                           'owner_org': 'hdx', 'subnational': '0'}

        resources = dataset.get_resources()
        assert resources == [{'format': 'csv', 'name': 'Life expectancy at birth (years)',
                              'description': '[Indicator metadata](http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65)',
                              'url': 'http://papa/GHO/WHOSIS_000001.csv?filter=COUNTRY:AFG&profile=verbose',
                              'resource_type': 'api',
                              'url_type': 'api'}]
        assert showcase == {'image_url': 'http://www.who.int/sysmedia/images/countries/afg.gif',
                            'url': 'http://www.who.int/countries/afg/en/',
                            'notes': 'Health indicators for Afghanistan', 'name': 'who-data-for-afghanistan-showcase',
                            'title': 'Indicators for Afghanistan'}
        datasetshowcase = generate_dataset_and_showcase(base_url, downloader, {'label': 'xxx', 'display': 'Unknown', 'attr': []}, TestWHO.indicators)
        assert datasetshowcase == (None, None)
        datasetshowcase = generate_dataset_and_showcase(base_url, downloader, TestWHO.countrydata,
                                   [('lala', 'Life expectancy at birth (years)',
                                     'http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65')])
        assert datasetshowcase == (None, None)

