#!/usr/bin/python
"""
Unit tests for WHO.

"""

from collections import OrderedDict
from os.path import join

import pytest
from hdx.api.configuration import Configuration
from hdx.data.showcase import Showcase
from hdx.database import Database
from hdx.utilities.compare import assert_files_same
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from who import WHO


class MockRetrieve:
    @staticmethod
    def download_file(url):
        return

    @staticmethod
    def download_json(url):
        if url == "https://papa/api/indicator":
            return {
                "value": [
                    {
                        "IndicatorCode": "WHOSIS_000001",
                        "IndicatorName": "Life expectancy at birth (years)",
                    },
                    {
                        "IndicatorCode": "MDG_0000000001",
                        "IndicatorName": "Infant mortality rate (probability of dying between birth and age 1 per 1000 live births",
                    },
                    {
                        "IndicatorCode": "WSH_SANITATION_BASIC",
                        "IndicatorName": "Population using at least basic sanitation services( %)",
                    },
                ]
            }
        if url == "https://lala/GHO_MODEL/SF_HIERARCHY_INDICATORS":
            return {
                "value": [
                    {
                        "THEME_TITLE": "Global Health Estimates: Life expectancy and leading causes of death and disability",
                        "INDICATOR_URL_NAME": "life-expectancy-at-birth-(years)",
                        "INDICATOR_CODE": "WHOSIS_000001",
                    },
                    {
                        "THEME_TITLE": "Global Health Estimates: Life expectancy and leading causes of death and disability",
                        "INDICATOR_URL_NAME": "infant-mortality-rate-(probability-of-dying-between-birth-and-age-1-per-1000-live-births) ",
                        "INDICATOR_CODE": "MDG_0000000001",
                    },
                    {
                        "THEME_TITLE": "World Health Statistics",
                        "INDICATOR_URL_NAME": "life-expectancy-at-birth-(years)",
                        "INDICATOR_CODE": "WHOSIS_000001",
                    },
                    {
                        "THEME_TITLE": "World Health Statistics",
                        "INDICATOR_URL_NAME": "population-using-at-least-basic-sanitation-services-(-)",
                        "INDICATOR_CODE": "WSH_SANITATION_BASIC",
                    },
                ]
            }
        elif url == "https://papa/api/DIMENSION/COUNTRY/DimensionValues":
            return {"value": [TestWHO.country]}
        elif url == "https://papa/api/dimension":
            return {
                "value": [
                    {"Code": "SEX", "Title": "Sex"},
                    {"Code": "COUNTRY", "Title": "Country"},
                    {
                        "Code": "RESIDENCEAREATYPE",
                        "Title": "Residence Area Type",
                    },
                ]
            }
        elif url == "https://papa/api/DIMENSION/SEX/DimensionValues":
            return {
                "value": [
                    {"Code": "SEX_BTSX", "Title": "Both sexes"},
                    {"Code": "SEX_FMLE", "Title": "Female"},
                    {"Code": "SEX_MLE", "Title": "Male"},
                ]
            }
        elif (
            url
            == "https://papa/api/DIMENSION/RESIDENCEAREATYPE/DimensionValues"
        ):
            return {
                "value": [
                    {"Code": "RESIDENCEAREATYPE_URB", "Title": "Urban"},
                    {"Code": "RESIDENCEAREATYPE_RUR", "Title": "Urban"},
                ]
            }
        elif url == "https://papa/api/WHOSIS_000001":
            return {
                "value": [
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
            }
        elif url == "https://papa/api/MDG_0000000001":
            return {
                "value": [
                    {
                        "Id": 5785042,
                        "IndicatorCode": "MDG_0000000001",
                        "SpatialDimType": "COUNTRY",
                        "SpatialDim": "AFG",
                        "ParentLocationCode": "EMR",
                        "TimeDimType": "YEAR",
                        "ParentLocation": "Eastern Mediterranean",
                        "Dim1Type": "SEX",
                        "TimeDim": 2011,
                        "Dim1": "SEX_BTSX",
                        "Dim2Type": None,
                        "Dim2": None,
                        "Dim3Type": None,
                        "Dim3": None,
                        "DataSourceDimType": None,
                        "DataSourceDim": None,
                        "Value": "61.76 [56.88-67.01]",
                        "NumericValue": 61.76149,
                        "Low": 56.88115,
                        "High": 67.01448,
                        "Comments": None,
                        "Date": "2023-02-16T07:52:34+01:00",
                        "TimeDimensionValue": "2011",
                        "TimeDimensionBegin": "2011-01-01T00:00:00+01:00",
                        "TimeDimensionEnd": "2011-12-31T00:00:00+01:00",
                    },
                    {
                        "Id": 5675670,
                        "IndicatorCode": "MDG_0000000001",
                        "SpatialDimType": "COUNTRY",
                        "SpatialDim": "AFG",
                        "ParentLocationCode": "EMR",
                        "TimeDimType": "YEAR",
                        "ParentLocation": "Eastern Mediterranean",
                        "Dim1Type": "SEX",
                        "TimeDim": 2005,
                        "Dim1": "SEX_MLE",
                        "Dim2Type": None,
                        "Dim2": None,
                        "Dim3Type": None,
                        "Dim3": None,
                        "DataSourceDimType": None,
                        "DataSourceDim": None,
                        "Value": "81.72 [76.22-87.73]",
                        "NumericValue": 81.71819,
                        "Low": 76.21614,
                        "High": 87.72866,
                        "Comments": None,
                        "Date": "2023-02-16T07:52:32+01:00",
                        "TimeDimensionValue": "2005",
                        "TimeDimensionBegin": "2005-01-01T00:00:00+01:00",
                        "TimeDimensionEnd": "2005-12-31T00:00:00+01:00",
                    },
                    {
                        "Id": 5425776,
                        "IndicatorCode": "MDG_0000000001",
                        "SpatialDimType": "COUNTRY",
                        "SpatialDim": "AFG",
                        "ParentLocationCode": "EMR",
                        "TimeDimType": "YEAR",
                        "ParentLocation": "Eastern Mediterranean",
                        "Dim1Type": "SEX",
                        "TimeDim": 1992,
                        "Dim1": "SEX_BTSX",
                        "Dim2Type": None,
                        "Dim2": None,
                        "Dim3Type": None,
                        "Dim3": None,
                        "DataSourceDimType": None,
                        "DataSourceDim": None,
                        "Value": "113.55 [105.31-122.27]",
                        "NumericValue": 113.54819,
                        "Low": 105.30619,
                        "High": 122.27416,
                        "Comments": None,
                        "Date": "2023-02-16T07:52:34+01:00",
                        "TimeDimensionValue": "1992",
                        "TimeDimensionBegin": "1992-01-01T00:00:00+01:00",
                        "TimeDimensionEnd": "1992-12-31T00:00:00+01:00",
                    },
                ]
            }
        elif url == "https://papa/api/WSH_SANITATION_BASIC":
            return {
                "value": [
                    {
                        "Id": 375582,
                        "IndicatorCode": "WSH_SANITATION_BASIC",
                        "SpatialDimType": "COUNTRY",
                        "SpatialDim": "AFG",
                        "TimeDimType": "YEAR",
                        "ParentLocationCode": "EMR",
                        "ParentLocation": "Eastern Mediterranean",
                        "Dim1Type": "RESIDENCEAREATYPE",
                        "TimeDim": 2005,
                        "Dim1": "RESIDENCEAREATYPE_URB",
                        "Dim2Type": None,
                        "Dim2": None,
                        "Dim3Type": None,
                        "Dim3": None,
                        "DataSourceDimType": None,
                        "DataSourceDim": None,
                        "Value": "37",
                        "NumericValue": 36.95171,
                        "Low": None,
                        "High": None,
                        "Comments": None,
                        "Date": "2023-07-10T08:10:46+02:00",
                        "TimeDimensionValue": "2005",
                        "TimeDimensionBegin": "2005-01-01T00:00:00+01:00",
                        "TimeDimensionEnd": "2005-12-31T00:00:00+01:00",
                    },
                    {
                        "Id": 375583,
                        "IndicatorCode": "WSH_SANITATION_BASIC",
                        "SpatialDimType": "COUNTRY",
                        "SpatialDim": "AFG",
                        "TimeDimType": "YEAR",
                        "ParentLocationCode": "EMR",
                        "ParentLocation": "Eastern Mediterranean",
                        "Dim1Type": "RESIDENCEAREATYPE",
                        "TimeDim": 2006,
                        "Dim1": "RESIDENCEAREATYPE_URB",
                        "Dim2Type": None,
                        "Dim2": None,
                        "Dim3Type": None,
                        "Dim3": None,
                        "DataSourceDimType": None,
                        "DataSourceDim": None,
                        "Value": "37",
                        "NumericValue": 36.95171,
                        "Low": None,
                        "High": None,
                        "Comments": None,
                        "Date": "2023-07-10T08:10:46+02:00",
                        "TimeDimensionValue": "2006",
                        "TimeDimensionBegin": "2006-01-01T00:00:00+01:00",
                        "TimeDimensionEnd": "2006-12-31T00:00:00+01:00",
                    },
                    {
                        "Id": 375584,
                        "IndicatorCode": "WSH_SANITATION_BASIC",
                        "SpatialDimType": "COUNTRY",
                        "SpatialDim": "AFG",
                        "TimeDimType": "YEAR",
                        "ParentLocationCode": "EMR",
                        "ParentLocation": "Eastern Mediterranean",
                        "Dim1Type": "RESIDENCEAREATYPE",
                        "TimeDim": 2007,
                        "Dim1": "RESIDENCEAREATYPE_RUR",
                        "Dim2Type": None,
                        "Dim2": None,
                        "Dim3Type": None,
                        "Dim3": None,
                        "DataSourceDimType": None,
                        "DataSourceDim": None,
                        "Value": "37",
                        "NumericValue": 36.95171,
                        "Low": None,
                        "High": None,
                        "Comments": None,
                        "Date": "2023-07-10T08:10:46+02:00",
                        "TimeDimensionValue": "2007",
                        "TimeDimensionBegin": "2007-01-01T00:00:00+01:00",
                        "TimeDimensionEnd": "2007-12-31T00:00:00+01:00",
                    },
                ]
            }

    @staticmethod
    def hxl_row(headers, hxltags, dict_form):
        return {header: hxltags.get(header, "") for header in headers}


class TestWHO:
    indicators = OrderedDict(
        WHOSIS_000001={
            "indicator_name": "Life expectancy at birth (years)",
            "indicator_url": "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/life-expectancy-at-birth-%28years%29",
        },
        MDG_0000000001={
            "indicator_name": "Infant mortality rate (probability of dying between birth and age 1 per 1000 live births",
            "indicator_url": "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/infant-mortality-rate-%28probability-of-dying-between-birth-and-age-1-per-1000-live-births%29%20",
        },
        WSH_SANITATION_BASIC={
            "indicator_name": "Population using at least basic sanitation services( %)",
            "indicator_url": "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/population-using-at-least-basic-sanitation-services( %)",
        },
    )
    tags = ["disability"]
    categories = OrderedDict(
        [
            (
                "Global Health Estimates: Life expectancy and leading causes of "
                "death and disability",
                OrderedDict({"WHOSIS_000001": None, "MDG_0000000001": None}),
            ),
            (
                "World Health Statistics",
                OrderedDict(
                    {"WHOSIS_000001": None, "WSH_SANITATION_BASIC": None}
                ),
            ),
        ]
    )

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
                "tests", "config", "project_configuration.yaml"
            ),
        )

    @pytest.fixture(scope="function")
    def retriever(self):
        return MockRetrieve()

    def test_get_countriesdata(self, configuration, retriever, tmp_path):
        configuration = Configuration.read()
        with Database(
            dialect="sqlite", database=str(tmp_path / "test_who.sqlite")
        ) as session:
            who = WHO(configuration, retriever, tmp_path, session)
            who.populate_db(populate_db=True, create_archived_datasets=False)
            countriesdata = who.get_countries()
            assert countriesdata == [{"Code": "AFG"}]

    def test_generate_dataset_and_showcase(
        self, configuration, retriever, tmp_path
    ):
        configuration = Configuration.read()
        with Database(
            dialect="sqlite", database=str(tmp_path / "test_who.sqlite")
        ) as session:
            who = WHO(configuration, retriever, tmp_path, session)
            who.populate_db(populate_db=True, create_archived_datasets=False)
            qc_indicators = configuration["qc_indicators"]
            quickcharts = {
                "hashtag": "#indicator+code",
                "values": [x["code"] for x in qc_indicators],
                "numeric_hashtag": "#indicator+value+num",
                "cutdown": 2,
                "cutdownhashtags": [
                    "#indicator+code",
                    "#country+code",
                    "#date+year+end",
                    "#dimension+name",
                ],
            }
            dataset, showcase, bites_disabled = (
                who.generate_dataset_and_showcase(TestWHO.country, quickcharts)
            )
            assert dataset == {
                "data_update_frequency": "30",
                "dataset_date": "[2005-01-01T00:00:00 TO 2019-12-31T23:59:59]",
                "groups": [{"name": "afg"}],
                "maintainer": "35f7bb2c-4ab6-4796-8334-525b30a94c89",
                "name": "who-data-for-afghanistan",
                "notes": "This dataset contains data from WHO's [data "
                "portal](https://www.who.int/gho/en/) covering the following "
                "categories:  \n"
                "  \n"
                "Global Health Estimates: Life expectancy and leading causes of "
                "death and disability, World Health Statistics.  \n"
                "  \n"
                "For links to individual indicator metadata, see resource "
                "descriptions.",
                "owner_org": "c021f6be-3598-418e-8f7f-c7a799194dba",
                "subnational": "0",
                "tags": [
                    {
                        "name": "hxl",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "indicators",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "disability",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                ],
                "title": "Afghanistan - Health Indicators",
            }

            resources = dataset.get_resources()
            assert resources == [
                {
                    "description": "See resource descriptions below for links to indicator "
                    "metadata",
                    "format": "csv",
                    "name": "All Health Indicators for Afghanistan",
                    "resource_type": "file.upload",
                    "url_type": "upload",
                },
                {
                    "description": "*Global Health Estimates: Life expectancy and leading causes "
                    "of death and disability:*\n"
                    "[Infant mortality rate (probability of dying between birth "
                    "and age 1 per 1000 live "
                    "births](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/infant-mortality-rate-%28probability-of-dying-between-birth-and-age-1-per-1000-live-births%29%20), "
                    "[Life expectancy at birth "
                    "(years)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/life-expectancy-at-birth-%28years%29)",
                    "format": "csv",
                    "name": "Global Health Estimates: Life expectancy and leading causes of "
                    "death and disability Indicators for Afghanistan",
                    "resource_type": "file.upload",
                    "url_type": "upload",
                },
                {
                    "description": "*World Health Statistics:*\n"
                    "[Life expectancy at birth "
                    "(years)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/life-expectancy-at-birth-%28years%29), "
                    "[Population using at least basic sanitation services( "
                    "%)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/population-using-at-least-basic-sanitation-services-%28-%29)",
                    "format": "csv",
                    "name": "World Health Statistics Indicators for Afghanistan",
                    "resource_type": "file.upload",
                    "url_type": "upload",
                },
                {
                    "description": "Cut down data for QuickCharts",
                    "format": "csv",
                    "name": "QuickCharts-All Health Indicators for Afghanistan",
                    "resource_type": "file.upload",
                    "url_type": "upload",
                },
            ]

            assert showcase == {
                "image_url": "https://cdn.who.int/media/images/default-source/countries-overview/flags/afg.jpg",
                "name": "who-data-for-afghanistan-showcase",
                "notes": "Health indicators for Afghanistan",
                "tags": [
                    {
                        "name": "hxl",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "indicators",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "disability",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                ],
                "title": "Indicators for Afghanistan",
                "url": "https://www.who.int/countries/afg/en/",
            }

            assert bites_disabled == [False, False, False]
            filename_list = [
                "global_health_estimates_life_expectancy_and_leading_causes_of_death_and_disability_indicators_afg.csv",
                "health_indicators_afg.csv",
                "qc_health_indicators_afg.csv",
                "world_health_statistics_indicators_afg.csv",
            ]
            for filename in filename_list:
                assert_files_same(
                    join("tests", "fixtures", filename),
                    join(tmp_path, filename),
                )

    def test_showcase(self, configuration):
        with temp_dir(
            "TestWHO",
            delete_on_success=True,
            delete_on_failure=False,
        ) as tempdir:
            with Download(user_agent="test") as downloader:
                retriever = Retrieve(
                    downloader,
                    tempdir,
                    tempdir,
                    tempdir,
                    save=False,
                    use_saved=False,
                )
                showcase = WHO.get_showcase(
                    retriever,
                    "AFG",
                    "Afghanistan",
                    "who-data-for-afghanistan",
                    ["hxl", "indicators"],
                )
                assert showcase == {
                    "image_url": "https://cdn.who.int/media/images/default-source/countries-overview/flags/afg.jpg",
                    "name": "who-data-for-afghanistan-showcase",
                    "notes": "Health indicators for Afghanistan",
                    "tags": [
                        {
                            "name": "hxl",
                            "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                        },
                        {
                            "name": "indicators",
                            "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                        },
                    ],
                    "title": "Indicators for Afghanistan",
                    "url": "https://www.who.int/countries/afg/en/",
                }
                showcase = WHO.get_showcase(
                    retriever,
                    "ABC",
                    "Afghanistan",
                    "who-data-for-afghanistan",
                    ["hxl", "indicators"],
                )
                assert showcase == {
                    "name": "who-data-for-afghanistan-showcase"
                }

    def test_showcase_for_nonexistent_url(self, configuration):
        with temp_dir(
            "TestWHO",
            delete_on_success=True,
            delete_on_failure=False,
        ) as tempdir:
            with Download(user_agent="test") as downloader:
                retriever = Retrieve(
                    downloader,
                    tempdir,
                    tempdir,
                    tempdir,
                    save=False,
                    use_saved=False,
                )
                showcase = WHO.get_showcase(
                    retriever,
                    "ABC",
                    "Afghanistan",
                    "who-data-for-afghanistan",
                    ["hxl", "indicators"],
                )
                assert showcase == Showcase(
                    {"name": "who-data-for-afghanistan-showcase"}
                )
