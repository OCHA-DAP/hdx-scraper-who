#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for WHO.

'''
from collections import OrderedDict
from os.path import join

import pytest
from hdx.data.vocabulary import Vocabulary
from hdx.hdx_configuration import Configuration
from hdx.hdx_locations import Locations
from hdx.location.country import Country
from hdx.utilities.compare import assert_files_same
from hdx.utilities.path import temp_dir

import who
from who import generate_dataset_and_showcase, get_countries, get_indicators_and_tags


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
                                                 'attr': [{'category': 'DISPLAY_FR',
                                                           'value': 'Esperance de vie a la naissance (ans)'},
                                                          {'category': 'DISPLAY_ES',
                                                           'value': 'Esperanza de vida al nacer'},
                                                          {'category': 'DEFINITION_XML',
                                                           'value': 'http://apps.who.int/gho/indicatorregistryservice/publicapiservice.asmx/IndicatorGetAsXml?profileCode=WHO&applicationCode=System&languageAlpha2=en&indicatorId=65'},
                                                          {'category': 'CATEGORY', 'value': 'health and demographics'},
                                                          {'category': 'RENDERER_ID', 'value': 'RENDER_2'}],
                                                 'display_sequence': 10, 'label': 'WHOSIS_000001'},
                                                {'display': 'Life expectancy at birth (years) 2',
                                                 'url': 'http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65',
                                                 'attr': [{'category': 'DISPLAY_FR',
                                                           'value': 'Esperance de vie a la naissance (ans)'},
                                                          {'category': 'DISPLAY_ES',
                                                           'value': 'Esperanza de vida al nacer'},
                                                          {'category': 'DEFINITION_XML',
                                                           'value': 'http://apps.who.int/gho/indicatorregistryservice/publicapiservice.asmx/IndicatorGetAsXml?profileCode=WHO&applicationCode=System&languageAlpha2=en&indicatorId=65'},
                                                          {'category': 'CATEGORY', 'value': 'health and demographics'},
                                                          {'category': 'RENDERER_ID', 'value': 'RENDER_2'}],
                                                 'display_sequence': 10, 'label': 'WHOSIS_000002'},
                                                {'display': 'Life expectancy at birth (years) 3',
                                                 'url': 'http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65',
                                                 'attr': [{'category': 'DISPLAY_FR',
                                                           'value': 'Esperance de vie a la naissance (ans)'},
                                                          {'category': 'DISPLAY_ES',
                                                           'value': 'Esperanza de vida al nacer'},
                                                          {'category': 'DEFINITION_XML',
                                                           'value': 'http://apps.who.int/gho/indicatorregistryservice/publicapiservice.asmx/IndicatorGetAsXml?profileCode=WHO&applicationCode=System&languageAlpha2=en&indicatorId=65'},
                                                          {'category': 'CATEGORY', 'value': 'sustainable development goals'},
                                                          {'category': 'RENDERER_ID', 'value': 'RENDER_2'}],
                                                 'display_sequence': 10, 'label': 'WHOSIS_000003'}
                                                ]}]}

            response.json = fn
        elif url == 'http://haha/api/COUNTRY?format=json':
            def fn():
                return {'dimension': [{'code': [TestWHO.country]}]}

            response.json = fn
        return response

    @staticmethod
    def get_tabular_rows(url, **kwargs):
        headers = ['GHO (CODE)', 'PUBLISHSTATE (CODE)', 'header2', 'YEAR (DISPLAY)', 'STARTYEAR', 'ENDYEAR', 'Numeric']
        if url == 'http://papa/data/data-verbose.csv?target=GHO/WHOSIS_000001&filter=COUNTRY:AFG&profile=verbose':
            retval = [{'GHO (CODE)': 'WHS7_104', 'PUBLISHSTATE (CODE)': 'PUBLISHED', 'header2': 'val21', 'YEAR (DISPLAY)': '1992-1994', 'Numeric': '123.4'},
                      {'GHO (CODE)': 'MDG_000000X', 'PUBLISHSTATE (CODE)': 'VOID-ACCEPTED', 'header2': 'val22', 'YEAR (DISPLAY)': '2015', 'Numeric': '123.4'},
                      {'GHO (CODE)': 'MDG_0000000001', 'PUBLISHSTATE (CODE)': 'PUBLISHED', 'header2': 'val22', 'YEAR (DISPLAY)': '2015', 'Numeric': '123.4'}]
        elif url == 'http://papa/data/data-verbose.csv?target=GHO/WHOSIS_000002&filter=COUNTRY:AFG&profile=verbose':
            retval = [{'GHO (CODE)': 'WHS7_105', 'PUBLISHSTATE (CODE)': 'PUBLISHED', 'header2': 'val21', 'YEAR (DISPLAY)': '1992', 'Numeric': '123.4'}]
        elif url == 'http://papa/data/data-verbose.csv?target=GHO/WHOSIS_000003&filter=COUNTRY:AFG&profile=verbose':
            retval = [{'GHO (CODE)': 'WHS7_106', 'PUBLISHSTATE (CODE)': 'PUBLISHED', 'header2': 'val21', 'YEAR (DISPLAY)': '1992', 'Numeric': '123.4'},
                      {'GHO (CODE)': 'MDG_000001X', 'PUBLISHSTATE (CODE)': 'VOID-ACCEPTED', 'header2': 'val22', 'YEAR (DISPLAY)': '2015', 'Numeric': '123.4'},
                      {'GHO (CODE)': 'MDG_0000000002', 'PUBLISHSTATE (CODE)': 'PUBLISHED', 'header2': 'val22', 'YEAR (DISPLAY)': '2015-2016', 'Numeric': '123.4'}]
        rows = list()
        for row in retval:
            row = kwargs['row_function'](headers, row)
            if row:
                rows.append(row)
        return headers, rows

    @staticmethod
    def hxl_row(headers, hxltags, dict_form):
        return {header: hxltags.get(header, '') for header in headers}


class TestWHO:
    indicators = OrderedDict([('health and demographics', [('WHOSIS_000001', 'Life expectancy at birth (years)', 'http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65'), ('WHOSIS_000002', 'Life expectancy at birth (years) 2', 'http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65')]), ('sustainable development goals', [('WHOSIS_000003', 'Life expectancy at birth (years) 3', 'http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65')])])
    tags = ['health', 'demographics', 'sustainable development goals - sdg']

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
        Vocabulary._tags_dict = dict()
        Vocabulary._approved_vocabulary = {'tags': [{'name': 'hxl'}, {'name': 'indicators'}, {'name': 'health'}, {'name': 'demographics'}, {'name': 'sustainable development goals - sdg'}], 'id': '4e61d464-4943-4e97-973a-84673c1aaa87', 'name': 'approved'}

    @pytest.fixture(scope='function')
    def downloader(self):
        return Download()

    def test_get_indicators_and_tags(self, configuration, downloader):
        indicators, tags = get_indicators_and_tags('http://lala/', downloader)
        assert indicators == TestWHO.indicators
        assert tags == TestWHO.tags

    def test_get_countriesdata(self, downloader):
        countriesdata = get_countries('http://haha/', downloader)
        assert countriesdata == [TestWHO.country]

    def test_generate_dataset_and_showcase(self, configuration):
        configuration = Configuration.read()
        base_url = configuration['base_url']
        qc_indicators = configuration['qc_indicators']
        with temp_dir('WHO') as folder:
            who.indicator_limit = 1
            dataset, showcase, bites_disabled = generate_dataset_and_showcase(
                base_url, folder, TestWHO.country, TestWHO.indicators, TestWHO.tags, qc_indicators, downloadclass=Download)
            assert dataset == {'name': 'who-data-for-afghanistan',
                               'notes': "Contains data from World Health Organization's [data portal](http://www.who.int/gho/en/) covering the following categories:  \nhealth and demographics, sustainable development goals  \n  \nFor links to individual indicator metadata, see resource descriptions.",
                               'title': 'Afghanistan - Health Indicators', 'groups': [{'name': 'afg'}],
                               'maintainer': '35f7bb2c-4ab6-4796-8334-525b30a94c89', 'owner_org': 'c021f6be-3598-418e-8f7f-c7a799194dba',
                               'data_update_frequency': '30', 'subnational': '0',
                               'tags': [{'name': 'hxl', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'indicators', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'health', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'demographics', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'sustainable development goals - sdg', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}],
                               'dataset_date': '01/01/1992-12/31/2016'}

            resources = dataset.get_resources()
            assert resources == [{'name': 'All Health Indicators for Afghanistan', 'description': 'See resource descriptions below for links to indicator metadata', 'format': 'CSV', 'resource_type': 'file.upload', 'url_type': 'upload'},
                                 {'name': 'health and demographics Indicators for Afghanistan', 'description': '*health and demographics:*\n[Life expectancy at birth (years)](http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65), [Life expectancy at birth (years) 2](http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65)', 'format': 'CSV', 'resource_type': 'file.upload', 'url_type': 'upload'},
                                 {'name': 'sustainable development goals Indicators for Afghanistan', 'description': '*sustainable development goals:*\n[Life expectancy at birth (years) 3](http://apps.who.int/gho/indicatorregistry/App_Main/view_indicator.aspx?iid=65)', 'format': 'CSV', 'resource_type': 'file.upload', 'url_type': 'upload'},
                                 {'name': 'QuickCharts Indicators for Afghanistan', 'description': 'Cut down data for QuickCharts', 'format': 'CSV', 'resource_type': 'file.upload', 'url_type': 'upload'}]

            assert showcase == {'image_url': 'http://www.who.int/sysmedia/images/countries/afg.gif',
                                'url': 'http://www.who.int/countries/afg/en/',
                                'notes': 'Health indicators for Afghanistan', 'name': 'who-data-for-afghanistan-showcase',
                                'tags': [{'name': 'hxl', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'indicators', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'health', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'demographics', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}, {'name': 'sustainable development goals - sdg', 'vocabulary_id': '4e61d464-4943-4e97-973a-84673c1aaa87'}],
                                'title': 'Indicators for Afghanistan'}
            assert bites_disabled == [False, True, False]
            file = 'health_indicators_AFG.csv'
            assert_files_same(join('tests', 'fixtures', file), join(folder, file))
            file = 'qc_%s' % file
            assert_files_same(join('tests', 'fixtures', file), join(folder, file))
            file = 'health and demographics_indicators_AFG.csv'
            assert_files_same(join('tests', 'fixtures', file), join(folder, file))
            country = {'label': 'xxx', 'display': 'Unknown', 'attr': []}
            datasetshowcase = generate_dataset_and_showcase(
                base_url, folder, country, TestWHO.indicators, TestWHO.tags, qc_indicators, downloadclass=Download)
            assert datasetshowcase == (None, None, None)

