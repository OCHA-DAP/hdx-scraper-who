#!/usr/bin/python
"""
Unit tests for WHO.

"""
from collections import OrderedDict
from os.path import join

import pytest
from hdx.api.configuration import Configuration
from hdx.api.locations import Locations
from hdx.data.vocabulary import Vocabulary
from hdx.location.country import Country
from hdx.utilities.compare import assert_files_same
from hdx.utilities.path import temp_dir

from who import WHO


class Retrieve:
    @staticmethod
    def download_json(url):
        if url == "https://lala/GHO_MODEL/SF_HIERARCHY_INDICATORS":
            return {
                "value": [
                    {
                        "PROGRAM_ID": "0c231176-b5f1-4b00-80f4-d9ee1938b986",
                        "PROGRAM_TITLE": "GHO",
                        "PROGRAM_URL_NAME": "GHO",
                        "THEME_ID": "0486c4a5-16c9-470d-9c9d-3864b6fe8715",
                        "THEME_TITLE": "Tobacco control",
                        "THEME_URL_NAME": "tobacco-control",
                        "TOPIC_ID": "0d68434e-6c10-466d-a515-5ead36dbe7a5",
                        "TOPIC_TITLE": "Monitor tobacco use and prevention policies (Tobacco control)",
                        "TOPIC_URL_NAME": "gho-tobacco-control-monitor",
                        "INDICATOR_GROUP_ID": "208237de-d8f7-42c5-affe-7573205c0a87",
                        "INDICATOR_GROUP_TITLE": "Compliance scores: tobacco control policies (Tobacco control: Monitor)",
                        "INDICATOR_GROUP_URL_NAME": "gho-tobacco-control-monitor-compliance-scores-tobacco-control-policies",
                        "INDICATOR_ID": "6a71b703-0666-4673-8f19-3cba182329a7",
                        "INDICATOR_TITLE": "Compliance scores: smoke-free legislation (Tobacco control: Monitor)",
                        "INDICATOR_URL_NAME": "gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation",
                        "DEFINITION_ID": "3f98548a-aed9-4b58-b9b9-d4cff022cdc8",
                        "DEFINITION_TITLE": "Compliance scores: smoke-free legislation",
                        "DEFINITION_URL_NAME": "gho-tobacco-control-monitorcompliance-scores-smoke-free-legislation",
                        "INDICATOR_CODE": "P_compl_p3",
                    },
                    {
                        "PROGRAM_ID": "0c231176-b5f1-4b00-80f4-d9ee1938b986",
                        "PROGRAM_TITLE": "GHO",
                        "PROGRAM_URL_NAME": "GHO",
                        "THEME_ID": "0486c4a5-16c9-470d-9c9d-3864b6fe8715",
                        "THEME_TITLE": "Tobacco control",
                        "THEME_URL_NAME": "tobacco-control",
                        "TOPIC_ID": "0d68434e-6c10-466d-a515-5ead36dbe7a5",
                        "TOPIC_TITLE": "Monitor tobacco use and prevention policies (Tobacco control)",
                        "TOPIC_URL_NAME": "gho-tobacco-control-monitor",
                        "INDICATOR_GROUP_ID": "208237de-d8f7-42c5-affe-7573205c0a87",
                        "INDICATOR_GROUP_TITLE": "Compliance scores: tobacco control policies (Tobacco control: Monitor)",
                        "INDICATOR_GROUP_URL_NAME": "gho-tobacco-control-monitor-compliance-scores-tobacco-control-policies",
                        "INDICATOR_ID": "daccc207-2417-45d0-854e-feabbbd7eda0",
                        "INDICATOR_TITLE": "Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)",
                        "INDICATOR_URL_NAME": "gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans",
                        "DEFINITION_ID": "c28d64d7-bf1e-48b2-b156-5331f05df593",
                        "DEFINITION_TITLE": "Compliance scores: advertising promotion and sponsorship bans",
                        "DEFINITION_URL_NAME": "gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans",
                        "INDICATOR_CODE": "E_compl_e12",
                    },
                    {
                        "PROGRAM_ID": "0c231176-b5f1-4b00-80f4-d9ee1938b986",
                        "PROGRAM_TITLE": "GHO",
                        "PROGRAM_URL_NAME": "GHO",
                        "THEME_ID": "0486c4a5-16c9-470d-9c9d-3864b6fe8715",
                        "THEME_TITLE": "Tobacco control",
                        "THEME_URL_NAME": "tobacco-control",
                        "TOPIC_ID": "0d68434e-6c10-466d-a515-5ead36dbe7a5",
                        "TOPIC_TITLE": "Monitor tobacco use and prevention policies (Tobacco control)",
                        "TOPIC_URL_NAME": "gho-tobacco-control-monitor",
                        "INDICATOR_GROUP_ID": "208237de-d8f7-42c5-affe-7573205c0a87",
                        "INDICATOR_GROUP_TITLE": "Compliance scores: tobacco control policies (Tobacco control: Monitor)",
                        "INDICATOR_GROUP_URL_NAME": "gho-tobacco-control-monitor-compliance-scores-tobacco-control-policies",
                        "INDICATOR_ID": "daccc207-2417-45d0-854e-feabbbd7eda0",
                        "INDICATOR_TITLE": "Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)",
                        "INDICATOR_URL_NAME": "gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans",
                        "DEFINITION_ID": "c28d64d7-bf1e-48b2-b156-5331f05df593",
                        "DEFINITION_TITLE": "Compliance scores: advertising promotion and sponsorship bans",
                        "DEFINITION_URL_NAME": "gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans",
                        "INDICATOR_CODE": "E_compl_e14",
                    },
                ]
            }
        elif url == "http://haha/api/DIMENSION/COUNTRY/DimensionValues":
            return {"value": [{TestWHO.country}]}

    @staticmethod
    def get_tabular_rows(url, **kwargs):
        headers = [
            "Id",
            "IndicatorCode",
            "SpatialDimType",
            "SpatialDim",
            "ParentLocationCode",
            "TimeDimType",
            "ParentLocation",
            "Dim1Type",
            "Dim1",
            "TimeDim",
            "Dim2Type",
            "Dim2",
            "Dim3Type",
            "Dim3",
            "DataSourceDimType",
            "DataSourceDim",
            "Value",
            "NumericValue",
            "Low",
            "High",
            "Comments",
            "Date",
            "TimeDimensionValue",
            "TimeDimensionBegin",
            "TimeDimensionEnd",
        ]
        if url == "https://papa/api/WHOSIS_000001?$filter=SpatialDim eq 'AFG'":
            retval = [
                {
                    "Id": 4989839,
                    "IndicatorCode": "WHOSIS_000001",
                    "SpatialDimType": "COUNTRY",
                    "SpatialDim": "AFG",
                    "ParentLocationCode": "EMR",
                    "TimeDimType": "YEAR",
                    "ParentLocation": "Eastern Mediterranean",
                    "Dim1Type": "SEX",
                    "Dim1": "SEX_MLE",
                    "TimeDim": 2010,
                    "Dim2Type": None,
                    "Dim2": None,
                    "Dim3Type": None,
                    "Dim3": None,
                    "DataSourceDimType": None,
                    "DataSourceDim": None,
                    "Value": "59.6",
                    "NumericValue": 59.60036,
                    "Low": None,
                    "High": None,
                    "Comments": None,
                    "Date": "2020-12-04T16:59:43+01:00",
                    "TimeDimensionValue": "2010",
                    "TimeDimensionBegin": "2010-01-01T00:00:00+01:00",
                    "TimeDimensionEnd": "2010-12-31T00:00:00+01:00",
                },
                {
                    "Id": 5155001,
                    "IndicatorCode": "WHOSIS_000001",
                    "SpatialDimType": "COUNTRY",
                    "SpatialDim": "AFG",
                    "ParentLocationCode": "EMR",
                    "TimeDimType": "YEAR",
                    "ParentLocation": "Eastern Mediterranean",
                    "Dim1Type": "SEX",
                    "Dim1": "SEX_MLE",
                    "TimeDim": 2019,
                    "Dim2Type": None,
                    "Dim2": None,
                    "Dim3Type": None,
                    "Dim3": None,
                    "DataSourceDimType": None,
                    "DataSourceDim": None,
                    "Value": "63.3",
                    "NumericValue": 63.28709,
                    "Low": None,
                    "High": None,
                    "Comments": None,
                    "Date": "2020-12-04T16:59:43+01:00",
                    "TimeDimensionValue": "2019",
                    "TimeDimensionBegin": "2019-01-01T00:00:00+01:00",
                    "TimeDimensionEnd": "2019-12-31T00:00:00+01:00",
                },
                {
                    "Id": 5154473,
                    "IndicatorCode": "WHOSIS_000001",
                    "SpatialDimType": "COUNTRY",
                    "SpatialDim": "AFG",
                    "ParentLocationCode": "EMR",
                    "TimeDimType": "YEAR",
                    "ParentLocation": "Eastern Mediterranean",
                    "Dim1Type": "SEX",
                    "Dim1": "SEX_FMLE",
                    "TimeDim": 2019,
                    "Dim2Type": None,
                    "Dim2": None,
                    "Dim3Type": None,
                    "Dim3": None,
                    "DataSourceDimType": None,
                    "DataSourceDim": None,
                    "Value": "63.2",
                    "NumericValue": 63.15551,
                    "Low": None,
                    "High": None,
                    "Comments": None,
                    "Date": "2020-12-04T16:59:43+01:00",
                    "TimeDimensionValue": "2019",
                    "TimeDimensionBegin": "2019-01-01T00:00:00+01:00",
                    "TimeDimensionEnd": "2019-12-31T00:00:00+01:00",
                },
            ]
        elif (
            url == "https://papa/api/WHOSIS_000002?$filter=SpatialDim eq 'AFG'"
        ):
            retval = [
                {
                    "Id": 5256507,
                    "IndicatorCode": "WHOSIS_000002",
                    "SpatialDimType": "COUNTRY",
                    "SpatialDim": "AFG",
                    "TimeDimType": "YEAR",
                    "ParentLocationCode": "EMR",
                    "ParentLocation": "Eastern Mediterranean",
                    "Dim1Type": "SEX",
                    "Dim1": "SEX_MLE",
                    "TimeDim": 2000,
                    "Dim2Type": None,
                    "Dim2": None,
                    "Dim3Type": None,
                    "Dim3": None,
                    "DataSourceDimType": None,
                    "DataSourceDim": None,
                    "Value": "46.9",
                    "NumericValue": 46.93113,
                    "Low": None,
                    "High": None,
                    "Comments": None,
                    "Date": "2020-12-04T16:59:42+01:00",
                    "TimeDimensionValue": "2000",
                    "TimeDimensionBegin": "2000-01-01T00:00:00+01:00",
                    "TimeDimensionEnd": "2000-12-31T00:00:00+01:00",
                }
            ]
        elif (
            url == "https://papa/api/WHOSIS_000003?$filter=SpatialDim eq 'AFG'"
        ):
            retval = [
                {
                    "Id": 407493,
                    "IndicatorCode": "WHOSIS_000003",
                    "SpatialDimType": "COUNTRY",
                    "SpatialDim": "AFG",
                    "TimeDimType": "YEAR",
                    "ParentLocationCode": "EMR",
                    "ParentLocation": "Eastern Mediterranean",
                    "Dim1Type": "SEX",
                    "TimeDim": 2012,
                    "Dim1": "SEX_BTSX",
                    "Dim2Type": None,
                    "Dim2": None,
                    "Dim3Type": None,
                    "Dim3": None,
                    "DataSourceDimType": None,
                    "DataSourceDim": None,
                    "Value": "44.52 [39.49-50]",
                    "NumericValue": 44.52410,
                    "Low": 39.49034,
                    "High": 50.00299,
                    "Comments": None,
                    "Date": "2023-02-16T08:10:49+01:00",
                    "TimeDimensionValue": "2012",
                    "TimeDimensionBegin": "2012-01-01T00:00:00+01:00",
                    "TimeDimensionEnd": "2012-12-31T00:00:00+01:00",
                },
                {
                    "Id": 415008,
                    "IndicatorCode": "WHOSIS_000003",
                    "SpatialDimType": "COUNTRY",
                    "SpatialDim": "AFG",
                    "TimeDimType": "YEAR",
                    "ParentLocationCode": "EMR",
                    "ParentLocation": "Eastern Mediterranean",
                    "Dim1Type": "SEX",
                    "TimeDim": 2013,
                    "Dim1": "SEX_BTSX",
                    "Dim2Type": None,
                    "Dim2": None,
                    "Dim3Type": None,
                    "Dim3": None,
                    "DataSourceDimType": None,
                    "DataSourceDim": None,
                    "Value": "43.13 [37.83-48.86]",
                    "NumericValue": 43.13298,
                    "Low": 37.82833,
                    "High": 48.85624,
                    "Comments": None,
                    "Date": "2023-02-16T08:10:49+01:00",
                    "TimeDimensionValue": "2013",
                    "TimeDimensionBegin": "2013-01-01T00:00:00+01:00",
                    "TimeDimensionEnd": "2013-12-31T00:00:00+01:00",
                },
                {
                    "Id": 364581,
                    "IndicatorCode": "WHOSIS_000003",
                    "SpatialDimType": "COUNTRY",
                    "SpatialDim": "AFG",
                    "TimeDimType": "YEAR",
                    "ParentLocationCode": "EMR",
                    "ParentLocation": "Eastern Mediterranean",
                    "Dim1Type": "SEX",
                    "TimeDim": 2004,
                    "Dim1": "SEX_BTSX",
                    "Dim2Type": None,
                    "Dim2": None,
                    "Dim3Type": None,
                    "Dim3": None,
                    "DataSourceDimType": None,
                    "DataSourceDim": None,
                    "Value": "55.86 [50.85-61.4]",
                    "NumericValue": 55.85786,
                    "Low": 50.84938,
                    "High": 61.40070,
                    "Comments": None,
                    "Date": "2023-02-16T08:10:49+01:00",
                    "TimeDimensionValue": "2004",
                    "TimeDimensionBegin": "2004-01-01T00:00:00+01:00",
                    "TimeDimensionEnd": "2004-12-31T00:00:00+01:00",
                },
            ]
        rows = list()
        for row in retval:
            row = kwargs["row_function"](headers, row)
            if row:
                rows.append(row)
        return headers, rows

    @staticmethod
    def hxl_row(headers, hxltags, dict_form):
        return {header: hxltags.get(header, "") for header in headers}


class TestWHO:
    indicators = OrderedDict(
        {
            "Tobacco control": [
                (
                    "P_compl_p3",
                    "Compliance scores: smoke-free legislation (Tobacco control: Monitor)",
                    "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation",
                ),
                (
                    "E_compl_e12",
                    "Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)",
                    "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans",
                ),
                (
                    "E_compl_e14",
                    "Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)",
                    "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans",
                ),
            ]
        }
    )
    tags = ["hxl", "indicators", "maternity", "health", "disease"]

    country = {
        "Code": "AFG",
        "Dimension": "COUNTRY",
        "ParentCode": "EMR",
        "ParentDimension": "REGION",
        "ParentTitle": "Eastern Mediterranean",
        "Title": "Afghanistan",
    }

    @pytest.fixture(scope="function")
    def configuration(self):
        Configuration._create(
            hdx_read_only=True,
            user_agent="test",
            project_config_yaml=join(
                "tests", "config", "project_configuration.yml"
            ),
        )
        Locations.set_validlocations([{"name": "afg", "title": "Afghanistan"}])
        Country.countriesdata(use_live=False)
        Vocabulary._tags_dict = dict()
        Vocabulary._approved_vocabulary = {
            "tags": [
                {"name": "hxl"},
                {"name": "indicators"},
                {"name": "maternity"},
                {"name": "health"},
                {"name": "disease"},
            ],
            "id": "4e61d464-4943-4e97-973a-84673c1aaa87",
            "name": "approved",
        }

    @pytest.fixture(scope="function")
    def retriever(self):
        return Retrieve()

    def test_get_indicators_and_tags(self, configuration, retriever):
        indicators, tags = WHO.get_indicators_and_tags(self)
        assert indicators == TestWHO.indicators
        assert tags == TestWHO.tags

    def test_get_countriesdata(self, retriever):
        countriesdata = WHO.get_countries()
        assert countriesdata == [TestWHO.country]

    def test_generate_dataset_and_showcase(self, configuration):
        configuration = Configuration.read()
        qc_indicators = configuration["qc_indicators"]
        with temp_dir("Test_WHO", delete_on_failure=False) as folder:
            WHO.indicator_limit = 1
            dataset, showcase, bites_disabled = (
                WHO.generate_dataset_and_showcase(
                    self,
                    TestWHO.country,
                    TestWHO.indicators,
                    TestWHO.tags,
                    qc_indicators,
                )
            )
            assert dataset == {
                "name": "who-data-for-afghanistan",
                "notes": "Contains data from World Health Organization's [data portal](http://www.who.int/gho/en/) covering the following categories:  \nhealth and demographics, sustainable development goals  \n  \nFor links to individual indicator metadata, see resource descriptions.",
                "title": "Afghanistan - Health Indicators",
                "groups": [{"name": "afg"}],
                "maintainer": "35f7bb2c-4ab6-4796-8334-525b30a94c89",
                "owner_org": "c021f6be-3598-418e-8f7f-c7a799194dba",
                "data_update_frequency": "30",
                "subnational": "0",
                "tags": [
                    {
                        "name": "hxl",
                        "vocabulary_id": "4e61d464-4943-4e97-973a-84673c1aaa87",
                    },
                    {
                        "name": "indicators",
                        "vocabulary_id": "4e61d464-4943-4e97-973a-84673c1aaa87",
                    },
                    {
                        "name": "maternity",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "health",
                        "vocabulary_id": "4e61d464-4943-4e97-973a-84673c1aaa87",
                    },
                    {
                        "name": "disease",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                ],
                "dataset_date": "[1992-01-01T00:00:00 TO 2016-12-31T23:59:59]",
            }

            resources = dataset.get_resources()
            assert resources == [
                {
                    "name": "All Health Indicators for Afghanistan",
                    "description": "See resource descriptions below for links to indicator metadata",
                    "format": "csv",
                    "resource_type": "file.upload",
                    "url_type": "upload",
                },
                {
                    "name": "Tobacco control Indicators for Afghanistan",
                    "description": "*Tobacco control:*\n[Compliance scores: smoke-free legislation (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Age-standardized estimates of current tobacco use, tobacco smoking and cigarette smoking (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-current-tobaccouse-tobaccosmoking-cigarrettesmoking-agestd-tobagestdcurr), [Tobacco use or smoking among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adolescents), [Most recent nationally representative survey reporting prevalence of tobacco use or smoking among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adults), [Health warnings on smokeless tobacco packaging must not be obscured in any way including by required markings such as tax stamps (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w9-no-obscure-c), [Specific health warnings are mandated for other smoked tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w15-specific-hw-b), [Health warnings on other smoked tobacco packaging must be rotated (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w7-rotation-b), [Health warnings on other smoked tobacco packaging must be written in the principal language(s) of the country (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w8-princ-langs-b), [Health warnings on other smoked tobacco packaging must be placed at the top of the principal display areas of the package (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w5-top-side-b), [Ban on deceitful terms on other smoked tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w18-misleading-terms-b), [Ban on deceitful terms on cigarette packaging (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w18-misleading-terms-a), [Health warnings on cigarette packaging must not be obscured in any way including by required markings such as tax stamps (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w9-no-obscure-a), [Health warnings on cigarette packaging must include a photograph or graphic (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w10-graphic-a), [Campaign was pre-tested (Tobacco control: Anti-tobacco mass media campaigns)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-antitobacco-campaigns-camp-mat-tested), [Health warnings appear on each smokeless tobacco package and any outside packaging and labelling used in the retail sale (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w11-outside-pack-c), [Smoking cessation support is available in other settings (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-smoking-cessation-support-is-available-in-other-settings), [Smoke-free pubs, bars and cafes (national legislation) (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-smoke-free-public-places-pubs-bars-and-cafes), [FINES ON THE ESTABLISHMENT for violations of smoke-free laws (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-legislation-fines-on-the-establishment-for-violations-of-smoke-free-laws), [Compliance scores: smoke-free legislation (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation), [Compliance scores: smoke-free legislation (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation), [Compliance scores: smoke-free legislation (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Age-standardized estimates of current tobacco use, tobacco smoking and cigarette smoking (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-current-tobaccouse-tobaccosmoking-cigarrettesmoking-agestd-tobagestdcurr), [Tobacco use or smoking among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adolescents), [Smokeless tobacco use or e-cigarette use among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adolescents), [National tobacco control programmes (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-national-tobacco-control-programmes), [Most recent nationally representative survey reporting prevalence of smokeless tobacco use or e-cigarette use among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adults), [Most recent nationally representative survey reporting prevalence of smokeless tobacco use or e-cigarette use among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adults), [Most recent nationally representative survey reporting prevalence of smokeless tobacco use or e-cigarette use among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adults), [Most recent nationally representative survey reporting prevalence of smokeless tobacco use or e-cigarette use among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adults), [Non-age-standardized estimates of current tobacco use, tobacco smoking and cigarette smoking (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-current-tobaccouse-tobaccosmoking-cigarrettesmoking-nonagestd-tobnonagestdcurr), [Health warnings appear on each other smoked tobacco package and any outside packaging and labelling used in the retail sale (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w11-outside-pack-b), [Health warnings on other smoked tobacco packaging must include a photograph or graphic (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w10-graphic-b), [Percentage of principal display area mandated to be covered by health warnings - front of other smoked tobacco packaging(Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w3-pc-front-b), [Health warnings on other smoked tobacco packaging must not be obscured in any way including by required markings such as tax stamps (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w9-no-obscure-b), [Other smoked tobacco packaging and labelling must not use figurative or other signs including colors or numbers as substitutes for prohibited misleading terms and descriptors (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w19-colours-numbers-b), [Percentage of principal display area mandated to be covered by health warnings - front and back of cigarette packaging (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w2-pc-front-back-a), [Health warnings appear on each cigarette package and any outside packaging and labelling used in the retail sale (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/do-health-warnings-appear-on-each-cigarette-package-and-any-outside-packaging-and-labelling-used-in-the-retail-sale-), [Campaign was part of a comprehensive tobacco control programme (Tobacco control: Anti-tobacco mass media campaigns)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-antitobacco-campaigns-camp-gov-prog), [Percentage of principal display area mandated to be covered by health warnings - front of smokeless tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w3-pc-front-c), [Smoking cessation support is available in hospitals (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-smoking-cessation-support-is-available-in-hospitals), [Varenicline - legally sold (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-medication-varenicline-legally-sold), [Smoke-free education facilities except universities (national legislation) (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-national-smoking-ban-in-educational-facilities-except-universities), [Smoke-free restaurants (national legislation) (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-smoke-free-public-places-restaurants), [Smoke-free government facilities (national legislation) (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-smoke-free-public-places-government-facilities), [Smoke-free indoor offices (national legislation) (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-smoke-free-public-places-indoor-offices), [Citizen complaints and investigations of smoke-free laws (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-smoke-free-legislation-citizen-complaints-and-investigations-of-smoke-free-laws), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Tobacco use or smoking among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adolescents), [National tobacco control programmes (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-national-tobacco-control-programmes), [National tobacco control programmes (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-national-tobacco-control-programmes), [National tobacco control programmes (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-national-tobacco-control-programmes), [Most recent nationally representative survey reporting prevalence of smokeless tobacco use or e-cigarette use among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adults), [Most recent nationally representative survey reporting prevalence of tobacco use or smoking among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adults), [Health warnings on smokeless tobacco packaging do not remove or diminish the liability of the tobacco industry (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w13-ind-liability-c), [Smokeless tobacco packaging and labelling must not use figurative or other signs including colors or numbers as substitutes for prohibited misleading terms and descriptors (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w19-colours-numbers-c), [Smokeless tobacco packaging and labelling must not display quantitative information on emission yields (such as tar nicotine and carbon monoxide) including when used as part of a brand name or trademark (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w21-emissions-quant-c), [Health warnings on other smoked tobacco packaging law applys to products whether manufactured domestically imported AND for duty-free sale (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w12-imports-dutyfree-b), [Cigarette packaging and labelling must not use figurative or other signs including colors or numbers as substitutes for prohibited misleading terms and descriptors (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w19-colours-numbers-a), [Health warnings on cigarette packaging law applys to products whether manufactured domestically imported AND for duty-free sale (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w12-imports-dutyfree-a), [Plain packaging of cigarettes is mandatory (ie.  packaging other than brand names and product names displayed in a standard colour and font style is prohibited). Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w26-plain-packaging-a), [Percentage of principal display area mandated to be covered by health warnings - front of cigarette packaging (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w3-pc-front-a), [Health warning labels on alcohol advertising](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/health-warning-labels-on-alcohol-advertising), [Percentage of principal display area mandated to be covered by health warnings - front and back of smokeless tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w2-pc-front-back-c), [Bupropion - place available (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-medication-bupropion-place-available), [Protecting people from tobacco smoke](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-people-from-tobacco-smoke), [FINES ON THE PATRONS of establishments for violations of smoke-free laws (Tobacco control: Protect](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-legislation-fines-on-the-patrons-of-establishments), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Tobacco use or smoking among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adolescents), [Tobacco use or smoking among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adolescents), [Smokeless tobacco use or e-cigarette use among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adolescents), [National tobacco control programmes (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-national-tobacco-control-programmes), [Most recent nationally representative survey reporting prevalence of smokeless tobacco use or e-cigarette use among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adults), [Most recent nationally representative survey reporting prevalence of tobacco use or smoking among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adults), [Most recent nationally representative survey reporting prevalence of tobacco use or smoking among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adults), [Health warnings on smokeless tobacco packaging law requires or establishes fines for violations (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w17-fines-c), [Health warnings on other smoked tobacco packaging describe the harmful effects of tobacco use on health (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w14-harm-effects-b), [Health warnings on other smoked tobacco packaging law requires or establishes fines for violations  (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w17-fines-b), [Number of health warnings approved by the law for cigarette packaging (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w16-number-hw-a), [Specific health warnings are mandated for cigarette packaging (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w15-specific-hw-a), [Legal requirement for size of health warning labels](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/legal-requirement-for-size-of-health-warning-labels), [Health warning labels on alcohol containers](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/health-warning-labels-on-alcohol-containers), [Percentage of principal display area mandated to be covered by health warnings - back of smokeless tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w4-pc-back-c), [Health warnings on smokeless tobacco packaging describe the harmful effects of tobacco use on health (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w14-harm-effects-c), [Smoking cessation support is available in the community (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/smoking-cessation-support-is-available-in-the-community-%28tobacco-control-offer-help%29), [DEDICATED FUNDS FOR ENFORCEMENT (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-legislation-dedicated-funds-for-enforcement), [Subnational smoke-free legislation authority exists (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-legislation-subnational-smoke-free-legislation-authority-exists), [Subnational bans on advertising, promotion and sponsorship - at least one jurisdiction has a comprehensive ban in place (Tobacco control: Enforce bans)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-legislation-subnational-smoking-bans-at-least-one-jurisdiction-comprehensive-ban-in-place-), [Compliance scores: smoke-free legislation (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation), [Age-standardized estimates of current tobacco use, tobacco smoking and cigarette smoking (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-current-tobaccouse-tobaccosmoking-cigarrettesmoking-agestd-tobagestdcurr), [Tobacco use or smoking among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adolescents), [Tobacco use or smoking among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adolescents), [Tobacco use or smoking among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adolescents), [Smokeless tobacco use or e-cigarette use among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adolescents), [Most recent nationally representative survey reporting prevalence of tobacco use or smoking among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adults), [Most recent nationally representative survey reporting prevalence of tobacco use or smoking among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adults), [Ban on deceitful terms on smokeless tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w18-misleading-terms-c), [Health warnings on smokeless tobacco packaging law applys to products whether manufactured domestically imported AND for duty-free sale (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w12-imports-dutyfree-c), [Law mandates that health warnings appear on other smoked tobacco packages (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/law-mandates-that-health-warnings-appear-on-other-smoked-tobacco-packages), [Percentage of principal display area mandated to be covered by health warnings - back of other smoked tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w4-pc-back-b), [Other smoked tobacco packaging and labelling must not display quantitative information on emission yields (such as tar nicotine and carbon monoxide) including when used as part of a brand name or trademark (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w21-emissions-quant-b), [Health warnings on other smoked tobacco packaging do not remove or diminish the liability of the tobacco industry (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w13-ind-liability-b), [The quit line number must appear on other smoked tobacco packaging or labelling (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w25-quitline-number-b), [Percentage of principal display area mandated to be covered by health warnings - back of cigarette packaging (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w4-pc-back-a), [Health warnings on cigarette packaging describe the harmful effects of tobacco use on health (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w14-harm-effects-a), [Earned media/public relations were used to promote the campaign (Tobacco control: Anti-tobacco mass media campaigns)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-antitobacco-campaigns-camp-news), [Alcohol content displayed on containers](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/alcohol-content-displayed-on-containers), [Font style, font size and colour of health warnings are mandated for smokeless tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w6-font-c), [Health warnings on smokeless tobacco packaging must include a photograph or graphic (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w10-graphic-c), [Health warnings on smokeless tobacco packaging must be rotated (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w7-rotation-c), [Number of health warnings approved by the law for smokeless tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w16-number-hw-c), [Varenicline - place available (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-medication-varenicline-place-available), [Nicotine replacement therapy - place available (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-medication-nicotine-replacement-therapy-place-available), [Cytisine - place available (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-medication-cytisine-place-available), [Monitoring tobacco use and prevention policies](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitori-tobacco-use-and-prevention-policies), [Compliance scores: smoke-free legislation (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation), [Compliance scores: smoke-free legislation (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Compliance scores: smoke-free legislation (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Smokeless tobacco use or e-cigarette use among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adolescents), [Smokeless tobacco use or e-cigarette use among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adolescents), [Most recent nationally representative survey reporting prevalence of smokeless tobacco use or e-cigarette use among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adults), [Most recent nationally representative survey reporting prevalence of tobacco use or smoking among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adults), [The quit line number must appear on smokeless tobacco packaging or labelling (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/the-quit-line-number-must-appear-on-smokeless-tobacco-packaging-or-labelling), [Plain packaging of smokeless tobacco products is mandatory (ie.  packaging other than brand names and product names displayed in a standard colour and font style is prohibited) (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w26-plain-packaging-c), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Compliance scores: advertising promotion and sponsorship bans (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-advertising-promotion-and-sponsorship-bans), [Smokeless tobacco use or e-cigarette use among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adolescents), [Smokeless tobacco packaging and labelling must not use descriptors depicting flavours (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w20-flavours-c), [Font style, font size and colour of health warnings are mandated for other smoked tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w6-font-b), [The quit line number must appear on cigarette packaging or labelling (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w25-quitline-number-a), [Law mandates that health warnings appear on cigarette packages (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w1-hw-law-a), [Health warnings on cigarette packaging must be written in the principal language(s) of the country (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarette-w8-princ-langs-a), [Outcome evaluation was employed to assess effectiveness of the campaign (Tobacco control: Anti-tobacco mass media campaigns)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-antitobacco-campaigns-camp-eval-impact), [National tobacco control programmes (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-national-tobacco-control-programmes), [Most recent nationally representative survey reporting prevalence of tobacco use or smoking among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adults), [Non-age-standardized estimates of current tobacco use, tobacco smoking and cigarette smoking (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-current-tobaccouse-tobaccosmoking-cigarrettesmoking-nonagestd-tobnonagestdcurr), [Non-age-standardized estimates of current tobacco use, tobacco smoking and cigarette smoking (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-current-tobaccouse-tobaccosmoking-cigarrettesmoking-nonagestd-tobnonagestdcurr), [Health warnings on smokeless tobacco packaging must be placed at the top of the principal display areas of the package (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w5-top-side-c), [Law mandates that health warnings appear on smokeless tobacco packages (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w1-hw-law-c), [Smoking cessation support is available in offices of health professionals (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-smoking-cessation-support-is-available-in-offices-of-health-professionals), [Access to a toll-free quit line (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-smoking-cessation-access-to-a-toll-free-quit-line), [Nicotine replacement therapy - legally sold (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-medication-nicotine-replacement-therapy-legally-sold), [Bupropion - legally sold (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-medication-bupropion-legally-sold), [Warn about the dangers of tobacco](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warn-about-the-dangers-of-tobacco), [FINES FOR VIOLATIONS OF SMOKE-FREE LAWS (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/national-smoking-ban-fines-for-violations), [Other smoked tobacco packaging and labelling must not use descriptors depicting flavours (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w20-flavours-b), [Health warnings on cigarette packaging law requires or establishes fines for violations (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w17-fines-a), [Health warnings on cigarette packaging must be placed at the top of the principal display areas of the package (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/health-warnings-on-cigarette-packaging-must-be-placed-at-the-top-of-the-principal-display-areas-of-the-package), [Cigarette packaging and labelling must not use descriptors depicting flavours (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w20-flavours-a), [Health warning labels on under-age drinking](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/health-warning-labels-on-under-age-drinking), [Health warning labels on pregnancy](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/health-warning-labels-on-pregnancy), [Specific health warnings are mandated for smokeless tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokeless-w15-specific-hw-c), [Anti-tobacco mass media campaigns](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-anti-tobacco-mass-media-campaigns), [Offer help to quit tobacco use](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-offer-help-to-quit-tobacco-use), [Raise taxes on tobacco](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/raising-taxes-on-tobacco), [Smoke-free public transport (national legislation) (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-smoke-free-public-places-public-transport), [Compliance scores: smoke-free legislation (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation), [Compliance scores: smoke-free legislation (Tobacco control: Monitor)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-compliance-scores-smoke-free-legislation), [Tobacco use or smoking among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adolescents), [Tobacco use or smoking among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adolescents), [Smokeless tobacco use or e-cigarette use among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adolescents), [Smokeless tobacco use or e-cigarette use among adolescents most recent nationally representative survey](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-monitor-survey-reporting-prevalence-of-smokeless-tobacco-use-or-e-cigarette-use-among-adolescents), [Most recent nationally representative survey reporting prevalence of tobacco use or smoking among adults](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/most-recent-nationally-representative-survey-reporting-prevalence-of-tobacco-use-or-smoking-among-adults), [Number of health warnings approved by the law for other smoked tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/how-many-health-warnings-are-approved-by-the-law-for-other-smoked-tobacco-packaging-), [Percentage of principal display area mandated to be covered by health warnings - front and back of other smoked tobacco packaging (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w2-pc-front-back-b), [Plain packaging of other smoked tobacco products is mandatory (ie. promotional information on packaging other than brand names and product names displayed in a standard colour and font style is prohibited) (Tobacco control: Health warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-smokedtobacco-w26-plain-packaging-b), [Health warnings on cigarette packaging do not remove or diminish the liability of the tobacco industry (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w13-ind-liability-a), [Font style, font size and colour of health warnings are mandated for cigarette packaging (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w6-font-a), [Health warnings on cigarette packaging must be rotated (Tobacco control: Health Warnings)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-cigarettes-w7-rotation-a), [Process evaluation was employed to assess implementation of the campaign (Tobacco control: Anti-tobacco mass media campaigns)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-antitobacco-campaigns-camp-media-monitor), [At least one national mass media campaign ran during the survey period (Tobacco control: Anti-tobacco mass media campaigns)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-warnings-antitobacco-campaigns-camp-nat), [Consumer information about calories, additives, etc on containers](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/consumer-information-about-calories-additives-etc-on-containers), [Number of standard alcoholic drinks displayed on containers](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/number-of-standard-alcoholic-drinks-displayed-on-containers), [Health warning labels on drink-driving](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/health-warning-labels-on-drink-driving), [Smoking cessation support is available in health clinics or other primary care facilities (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-smoking-cessation-support-is-available-in-health-clinics-or-other-primary-care-facilities), [Cytisine - legally sold (Tobacco control: Offer help)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-offerhelp-medication-cytisine-legally-sold), [NUMBER OF PLACES SMOKE-FREE (national legislation) (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-national-legislation-number-of-places-smoke-free), [Smoke-free universities (national legislation) (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-smoke-free-public-places-universities), [Smoke-free health care facilities (national legislation) (Tobacco control: Protect)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/gho-tobacco-control-protect-smoke-free-health-care-facilities)",
                    "format": "csv",
                    "resource_type": "file.upload",
                    "url_type": "upload",
                },
            ]

            assert showcase == {
                "image_url": "http://www.who.int/sysmedia/images/countries/afg.gif",
                "url": "http://www.who.int/countries/afg/en/",
                "notes": "Health indicators for Afghanistan",
                "name": "who-data-for-afghanistan-showcase",
                "tags": [
                    {
                        "name": "hxl",
                        "vocabulary_id": "4e61d464-4943-4e97-973a-84673c1aaa87",
                    },
                    {
                        "name": "indicators",
                        "vocabulary_id": "4e61d464-4943-4e97-973a-84673c1aaa87",
                    },
                    {
                        "name": "maternity",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "health",
                        "vocabulary_id": "4e61d464-4943-4e97-973a-84673c1aaa87",
                    },
                    {
                        "name": "disease",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                ],
                "title": "Indicators for Afghanistan",
            }
            assert bites_disabled == [False, True, False]
            file = "health_indicators_AFG.csv"
            assert_files_same(
                join("tests", "fixtures", file), join(folder, file)
            )
            # file = f"qc_{file}"
            # assert_files_same(join("tests", "fixtures", file), join(folder, file))
            file = "global_health_estimates_life_expectancy_and_leading_causes_of_death_and_disability_indicators_AFG.csv"
            assert_files_same(
                join("tests", "fixtures", file), join(folder, file)
            )
            country = {"label": "xxx", "display": "Unknown", "attr": []}
            datasetshowcase = WHO.generate_dataset_and_showcase(
                self, country, TestWHO.indicators, TestWHO.tags, qc_indicators
            )
            assert datasetshowcase == (None, None, None)
