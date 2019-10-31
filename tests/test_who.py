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
                        return {'dimension': [{'code': [TestWHO.countrydata]}]}
                    response.json = fn
                return response

            @staticmethod
            def get_tabular_rows(url, dict_rows, headers):
                if url == 'http://papa/data/data-verbose.csv?target=GHO/WHOSIS_000001&filter=COUNTRY:AFG&profile=verbose':
                    return [{'header1': 'val11', 'header2': 'val21', 'YEAR (CODE)': '1992'},
                            {'header1': 'val12', 'header2': 'val22', 'YEAR (CODE)': '2015'}]
                elif url == 'http://papa/data/data-verbose.csv?target=GHO/lala&filter=COUNTRY:AFG&profile=verbose':
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
        configuration = Configuration.read()
        base_url = configuration['base_url']
        hxlproxy_url = configuration['hxlproxy_url']
        dataset, showcase = generate_dataset_and_showcase(base_url, hxlproxy_url, downloader, TestWHO.countrydata, TestWHO.indicators)
        assert dataset == {'name': 'who-data-for-afghanistan',
                           'notes': "Contains data from World Health Organization's [data portal](http://www.who.int/gho/en/) covering the following indicators:  \n[Life expectancy at birth (years)](http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65)",
                           'title': 'Afghanistan - Health Indicators', 'groups': [{'name': 'afg'}],
                           'maintainer': '196196be-6037-4488-8b71-d786adf4c081', 'owner_org': 'hdx',
                           'data_update_frequency': '365', 'subnational': '0',
                           'tags': [{'name': 'hxl', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'indicators', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}],
                           'dataset_date': '01/01/1992-12/31/2015'}

        resources = dataset.get_resources()
        assert resources == [{'name': 'Health Indicators for Afghanistan', 'description': 'See dataset description for links to indicator metadata',
                              'format': 'csv', 'url': 'https://proxy.hxlstandard.org/data/download/Health Indicators for Afghanistan.csv?url=http%3A%2F%2Fpapa%2Fdata%2Fdata-verbose.csv%3Ftarget%3DGHO%2FWHOSIS_000001%26filter%3DCOUNTRY%3AAFG%26profile%3Dverbose&header-row=1&tagger-match-all=on&tagger-01-header=gho+%28code%29&tagger-01-tag=%23indicator%2Bcode&tagger-02-header=gho+%28display%29&tagger-02-tag=%23indicator%2Bname&tagger-03-header=gho+%28url%29&tagger-03-tag=%23indicator%2Burl&tagger-05-header=datasource+%28display%29&tagger-05-tag=%23meta%2Bsource&tagger-07-header=publishstate+%28code%29&tagger-07-tag=%23status%2Bcode&tagger-08-header=publishstate+%28display%29&tagger-08-tag=%23status%2Bname&tagger-11-header=year+%28display%29&tagger-11-tag=%23date%2Byear&tagger-13-header=region+%28code%29&tagger-13-tag=%23region%2Bcode&tagger-14-header=region+%28display%29&tagger-14-tag=%23region%2Bname&tagger-16-header=country+%28code%29&tagger-16-tag=%23country%2Bcode&tagger-17-header=country+%28display%29&tagger-17-tag=%23country%2Bname&tagger-19-header=sex+%28code%29&tagger-19-tag=%23sex%2Bcode&tagger-20-header=sex+%28display%29&tagger-20-tag=%23sex%2Bname&tagger-23-header=numeric&tagger-23-tag=%23indicator%2Bvalue%2Bnum&filter01=sort&sort-tags01=%23indicator%2Bcode%2C%23date%2Byear%2C%23sex%2Bcode',
                              'resource_type': 'api', 'url_type': 'api'},
                             {'name': 'QuickCharts Health Indicators for Afghanistan', 'description': 'QuickCharts resource',
                              'format': 'csv',
                              'url': 'https://proxy.hxlstandard.org/data/download/Health Indicators for Afghanistan.csv?url=http%3A%2F%2Fpapa%2Fdata%2Fdata-verbose.csv%3Ftarget%3DGHO%2FMDG_0000000001%2CWHOSIS_000001%2CWHS7_104%26filter%3DCOUNTRY%3AAFG%26profile%3Dverbose&header-row=1&tagger-match-all=on&tagger-01-header=gho+%28code%29&tagger-01-tag=%23indicator%2Bcode&tagger-02-header=gho+%28display%29&tagger-02-tag=%23indicator%2Bname&tagger-03-header=gho+%28url%29&tagger-03-tag=%23indicator%2Burl&tagger-05-header=datasource+%28display%29&tagger-05-tag=%23meta%2Bsource&tagger-07-header=publishstate+%28code%29&tagger-07-tag=%23status%2Bcode&tagger-08-header=publishstate+%28display%29&tagger-08-tag=%23status%2Bname&tagger-11-header=year+%28display%29&tagger-11-tag=%23date%2Byear&tagger-13-header=region+%28code%29&tagger-13-tag=%23region%2Bcode&tagger-14-header=region+%28display%29&tagger-14-tag=%23region%2Bname&tagger-16-header=country+%28code%29&tagger-16-tag=%23country%2Bcode&tagger-17-header=country+%28display%29&tagger-17-tag=%23country%2Bname&tagger-19-header=sex+%28code%29&tagger-19-tag=%23sex%2Bcode&tagger-20-header=sex+%28display%29&tagger-20-tag=%23sex%2Bname&tagger-23-header=numeric&tagger-23-tag=%23indicator%2Bvalue%2Bnum&filter01=sort&sort-tags01=%23indicator%2Bcode%2C%23date%2Byear%2C%23sex%2Bcode',
                              'resource_type': 'api', 'url_type': 'api'}]

        assert showcase == {'image_url': 'http://www.who.int/sysmedia/images/countries/afg.gif',
                            'url': 'http://www.who.int/countries/afg/en/',
                            'notes': 'Health indicators for Afghanistan', 'name': 'who-data-for-afghanistan-showcase',
                            'tags': [{'name': 'hxl', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'indicators', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}],
                            'title': 'Indicators for Afghanistan'}
        datasetshowcase = generate_dataset_and_showcase(base_url, hxlproxy_url, downloader, {'label': 'xxx', 'display': 'Unknown', 'attr': []}, TestWHO.indicators)
        assert datasetshowcase == (None, None)
        datasetshowcase = generate_dataset_and_showcase(base_url, hxlproxy_url, downloader, TestWHO.countrydata,
                                   [('lala', 'Life expectancy at birth (years)',
                                     'http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65')])
        assert datasetshowcase == (None, None)

