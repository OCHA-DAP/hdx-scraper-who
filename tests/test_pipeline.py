#!/usr/bin/python
"""
Unit tests for WHO.
"""

from collections import OrderedDict
from os.path import join
from urllib.parse import urlparse

import pytest
from hdx.api.configuration import Configuration
from hdx.data.showcase import Showcase
from hdx.database import Database
from hdx.utilities.base_downloader import DownloadError
from hdx.utilities.compare import assert_files_same
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from hdx.scraper.who.pipeline import Pipeline


class MockRetrieve:
    @staticmethod
    def download_file(url):
        return

    @staticmethod
    def download_json(url):
        path = urlparse(url).path.strip("/")
        if path.lower().startswith("api/"):
            path = path[4:]  # strip leading 'api/' for azureedge base
        key = path  # keep original case for comparisons below

        if key == "indicator" or key == "INDICATOR":
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
                    # This indicator doesn't have an associated category, to test archiving
                    {
                        "IndicatorCode": "TB_1",
                        "IndicatorName": "Tuberculosis treatment coverage",
                    },
                    # This indicator has no data
                    {
                        "IndicatorCode": "NO_DATA",
                        "IndicatorName": "Fake indicator with no data",
                    },
                ]
            }
        if key == "GHO_MODEL/SF_HIERARCHY_INDICATORS":
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
        if key == "dimension" or key == "DIMENSION":
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
        if key == "DIMENSION/COUNTRY/DimensionValues":
            return {"value": [TestPipeline.country]}
        if key == "DIMENSION/SEX/DimensionValues":
            return {
                "value": [
                    {"Code": "SEX_BTSX", "Title": "Both sexes"},
                    {"Code": "SEX_FMLE", "Title": "Female"},
                    {"Code": "SEX_MLE", "Title": "Male"},
                ]
            }
        if key == "DIMENSION/RESIDENCEAREATYPE/DimensionValues":
            return {
                "value": [
                    {"Code": "RESIDENCEAREATYPE_URB", "Title": "Urban"},
                    {"Code": "RESIDENCEAREATYPE_RUR", "Title": "Urban"},
                ]
            }
        if key == "WHOSIS_000001":
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
                    # Extra entry to test wrong spatial dim type
                    {
                        "Id": 4989839,
                        "IndicatorCode": "WHOSIS_000001",
                        "SpatialDimType": "NONSENSE",
                    },
                ]
            }
        if key == "MDG_0000000001":
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
        if key == "WSH_SANITATION_BASIC":
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

        if key == "TB_1":
            return {
                "value": [
                    {
                        "Id": 137943,
                        "IndicatorCode": "TB_1",
                        "SpatialDimType": "COUNTRY",
                        "SpatialDim": "AFG",
                        "TimeDimType": "YEAR",
                        "ParentLocationCode": "EMR",
                        "ParentLocation": "Eastern Mediterranean",
                        "Dim1Type": None,
                        "Dim1": None,
                        "TimeDim": 2014,
                        "Dim2Type": None,
                        "Dim2": None,
                        "Dim3Type": None,
                        "Dim3": None,
                        "DataSourceDimType": None,
                        "DataSourceDim": None,
                        "Value": "51 [36-79]",
                        "NumericValue": 51,
                        "Low": 36,
                        "High": 79,
                        "Comments": None,
                        "Date": "2023-10-25T09:27:14+02:00",
                        "TimeDimensionValue": "2014",
                        "TimeDimensionBegin": "2014-01-01T00:00:00+01:00",
                        "TimeDimensionEnd": "2014-12-31T00:00:00+01:00",
                    },
                    {
                        "Id": 137944,
                        "IndicatorCode": "TB_1",
                        "SpatialDimType": "COUNTRY",
                        "SpatialDim": "AFG",
                        "TimeDimType": "YEAR",
                        "ParentLocationCode": "EMR",
                        "ParentLocation": "Eastern Mediterranean",
                        "Dim1Type": None,
                        "Dim1": None,
                        "TimeDim": 2015,
                        "Dim2Type": None,
                        "Dim2": None,
                        "Dim3Type": None,
                        "Dim3": None,
                        "DataSourceDimType": None,
                        "DataSourceDim": None,
                        "Value": "51 [36-79]",
                        "NumericValue": 52,
                        "Low": 36,
                        "High": 79,
                        "Comments": None,
                        "Date": "2023-10-25T09:27:14+02:00",
                        "TimeDimensionValue": "2014",
                        "TimeDimensionBegin": "2015-01-01T00:00:00+01:00",
                        "TimeDimensionEnd": "2015-12-31T00:00:00+01:00",
                    },
                    {
                        "Id": 137945,
                        "IndicatorCode": "TB_1",
                        "SpatialDimType": "COUNTRY",
                        "SpatialDim": "AFG",
                        "TimeDimType": "YEAR",
                        "ParentLocationCode": "EMR",
                        "ParentLocation": "Eastern Mediterranean",
                        "Dim1Type": None,
                        "Dim1": None,
                        "TimeDim": 2016,
                        "Dim2Type": None,
                        "Dim2": None,
                        "Dim3Type": None,
                        "Dim3": None,
                        "DataSourceDimType": None,
                        "DataSourceDim": None,
                        "Value": "51 [36-79]",
                        "NumericValue": 53,
                        "Low": 36,
                        "High": 79,
                        "Comments": None,
                        "Date": "2023-10-25T09:27:14+02:00",
                        "TimeDimensionValue": "2016",
                        "TimeDimensionBegin": "2016-01-01T00:00:00+01:00",
                        "TimeDimensionEnd": "2016-12-31T00:00:00+01:00",
                    },
                ]
            }
        if key == "NO_DATA":
            raise DownloadError

        # default: no match
        return None

    @staticmethod
    def hxl_row(headers, hxltags, dict_form):
        return {header: hxltags.get(header, "") for header in headers}


class TestPipeline:
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
        TB_1={
            "indicator_name": "Tuberculosis treatment coverage",
            "indicator_url": None,
        },
    )
    categories = OrderedDict(
        [
            (
                "Global Health Estimates: Life expectancy and leading causes of "
                "death and disability",
                OrderedDict({"WHOSIS_000001": None, "MDG_0000000001": None}),
            ),
            (
                "World Health Statistics",
                OrderedDict({"WHOSIS_000001": None, "WSH_SANITATION_BASIC": None}),
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

    @pytest.fixture
    def retriever(self):
        return MockRetrieve()

    def test_get_countriesdata(self, configuration, retriever, tmp_path):
        configuration = Configuration.read()
        with Database(
            dialect="sqlite", database=str(tmp_path / "test_who.sqlite")
        ) as database:
            session = database.get_session()
            who = Pipeline(configuration, retriever, tmp_path, session)
            who.populate_db(populate_db=True, create_archived_datasets=False)
            countriesdata = who.get_countries()
            assert countriesdata == [{"Code": "AFG"}]

    def test_generate_dataset_and_showcase(self, configuration, retriever, tmp_path):
        configuration = Configuration.read()
        with Database(
            dialect="sqlite", database=str(tmp_path / "test_who.sqlite")
        ) as database:
            session = database.get_session()
            who = Pipeline(configuration, retriever, tmp_path, session)
            who.populate_db(populate_db=True, create_archived_datasets=False)
            dataset, showcase = who.generate_dataset_and_showcase(TestPipeline.country)
            assert dataset == {
                "dataset_date": "[1992-01-01T00:00:00 TO 2019-12-31T23:59:59]",
                "groups": [{"name": "afg"}],
                "name": "who-data-for-afg",
                "notes": "This dataset contains data from WHO's [data "
                "portal](https://www.who.int/gho/en/) covering the following "
                "categories:  \n"
                "  \n"
                "Global Health Estimates: Life expectancy and leading causes of "
                "death and disability, World Health Statistics.  \n"
                "  \n"
                "For links to individual indicator metadata, see resource "
                "descriptions.",
                "subnational": "0",
                "tags": [
                    {
                        "name": "hxl",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    }
                ],
                "title": "Afghanistan - Health Indicators",
            }

            resources = dataset.get_resources()
            assert resources == [
                {
                    "description": "*World Health Statistics:*\n"
                    "[Life expectancy at birth "
                    "(years)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/life-expectancy-at-birth-%28years%29), "
                    "[Population using at least basic sanitation services( "
                    "%)](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/population-using-at-least-basic-sanitation-services-%28-%29)",
                    "format": "csv",
                    "name": "World Health Statistics Indicators for Afghanistan",
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
                },
                {
                    "description": "See resource descriptions below for links to indicator "
                    "metadata",
                    "format": "csv",
                    "name": "All Health Indicators for Afghanistan",
                },
            ]

            assert showcase == {
                "image_url": "https://cdn.who.int/media/images/default-source/countries-overview/flags/afg.jpg",
                "name": "who-data-for-afg-showcase",
                "notes": "Health indicators for Afghanistan",
                "tags": [
                    {
                        "name": "hxl",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                ],
                "title": "Indicators for Afghanistan",
                "url": "https://www.who.int/countries/afg/en/",
            }

            filename_list = [
                "global_health_estimates_life_expectancy_and_leading_causes_of_death_and_disability_indicators_afg.csv",
                "health_indicators_afg.csv",
                "world_health_statistics_indicators_afg.csv",
            ]
            for filename in filename_list:
                assert_files_same(
                    join("tests", "fixtures", filename),
                    join(tmp_path, filename),
                )

    def test_showcase(self, configuration):
        with temp_dir(
            "TestWho",
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
                showcase = Pipeline.get_showcase(
                    retriever,
                    "AFG",
                    "Afghanistan",
                    "who-data-for-afg",
                    ["hxl", "indicators"],
                )
                assert showcase == {
                    "image_url": "https://cdn.who.int/media/images/default-source/countries-overview/flags/afg.jpg",
                    "name": "who-data-for-afg-showcase",
                    "notes": "Health indicators for Afghanistan",
                    "tags": [
                        {
                            "name": "hxl",
                            "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                        }
                    ],
                    "title": "Indicators for Afghanistan",
                    "url": "https://www.who.int/countries/afg/en/",
                }
                showcase = Pipeline.get_showcase(
                    retriever,
                    "ABC",
                    "Afghanistan",
                    "who-data-for-afg",
                    ["hxl", "indicators"],
                )
                assert showcase == {"name": "who-data-for-afg-showcase"}

    def test_showcase_for_nonexistent_url(self, configuration):
        with temp_dir(
            "TestWho",
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
                showcase = Pipeline.get_showcase(
                    retriever,
                    "ABC",
                    "Afghanistan",
                    "who-data-for-afg",
                    ["hxl", "indicators"],
                )
                assert showcase == Showcase({"name": "who-data-for-afg-showcase"})

    def test_generate_archived_dataset(self, configuration, retriever, tmp_path):
        configuration = Configuration.read()
        with Database(
            dialect="sqlite", database=str(tmp_path / "test_who.sqlite")
        ) as database:
            session = database.get_session()
            who = Pipeline(configuration, retriever, tmp_path, session)
            who.populate_db(populate_db=True, create_archived_datasets=True)
            dataset = who.generate_archived_dataset(TestPipeline.country)
            assert dataset == {
                "archived": True,
                "data_update_frequency": "-1",
                "dataset_date": "[2014-01-01T00:00:00 TO 2016-12-31T23:59:59]",
                "groups": [{"name": "afg"}],
                "name": "who-historical-data-for-afg",
                "notes": "This dataset contains historical data from WHO's [data "
                "portal](https://www.who.int/gho/en/).",
                "subnational": "0",
                "tags": [
                    {
                        "name": "hxl",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                ],
                "title": "Afghanistan - Historical Health Indicators",
            }

            resources = dataset.get_resources()
            assert resources == [
                {
                    "description": "Historical health indicators no longer updated by WHO",
                    "format": "csv",
                    "name": "All Historical Health Indicators for Afghanistan",
                }
            ]

            filename = "historical_health_indicators_afg.csv"
            assert_files_same(
                join("tests", "fixtures", filename), join(tmp_path, filename)
            )
