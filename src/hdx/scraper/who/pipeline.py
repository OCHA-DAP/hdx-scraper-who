#!/usr/bin/python
"""Who scraper"""

import logging
import re
from collections import OrderedDict
from datetime import datetime
from urllib.parse import quote

from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.data.hdxobject import HDXError
from hdx.data.showcase import Showcase
from hdx.data.vocabulary import Vocabulary
from hdx.location.country import Country
from hdx.utilities.base_downloader import DownloadError
from hdx.utilities.dateparse import parse_date_range
from hdx.utilities.retriever import Retrieve
from slugify import slugify
from sqlalchemy import false, insert, true

from .database.db_categories import DBCategories
from .database.db_dimension_values import DBDimensionValues
from .database.db_dimensions import DBDimensions
from .database.db_indicator_data import DBIndicatorData
from .database.db_indicators import DBIndicators

logger = logging.getLogger(__name__)

_BATCH_SIZE = 1000
_TAG_CLEAN_TABLE = str.maketrans(
    {
        "(": "",
        ")": "",
        "/": "",
        ",": "",
    }
)


def _clean_tag(s: str) -> str:
    """Remove punctuation used by old multiple_replace and trim whitespace."""
    return s.translate(_TAG_CLEAN_TABLE).strip()


class Pipeline:
    def __init__(
        self, configuration: Configuration, retriever: Retrieve, tempdir: str, session
    ):
        self._configuration = configuration
        self._retriever = retriever
        self._tempdir = tempdir
        self._session = session
        self._dimension_value_names_dict = dict()
        self._hxltags = {
            "GHO (CODE)": "#indicator+code",
            "GHO (DISPLAY)": "#indicator+name",
            "GHO (URL)": "#indicator+url",
            "YEAR (DISPLAY)": "#date+year",
            "STARTYEAR": "#date+year+start",
            "ENDYEAR": "#date+year+end",
            "REGION (CODE)": "#region+code",
            "REGION (DISPLAY)": "#region+name",
            "COUNTRY (CODE)": "#country+code",
            "COUNTRY (DISPLAY)": "#country+name",
            "DIMENSION (TYPE)": "#dimension+type",
            "DIMENSION (CODE)": "#dimension+code",
            "DIMENSION (NAME)": "#dimension+name",
            "Numeric": "#indicator+value+num",
            "Value": "#indicator+value",
            "Low": "#indicator+value+low",
            "High": "#indicator+value+high",
        }

    def populate_db(self, populate_db: bool, create_archived_datasets: bool):
        """Populate the database and create convenience dictionaries and
        lists

        Args:
            populate_db (bool): populate the database

        Returns:
            None
        """
        if populate_db:
            self._populate_dimensions_db()
        # This dictionary is needed for populating the other DBs
        self._create_dimension_value_names_dict()
        self._create_countries_dict()
        if populate_db:
            self._populate_categories_and_indicators_db()
            self._populate_indicator_data_db(create_archived_datasets)

    def get_countries(self):
        """Public method that returns countries in the format required
        for progress_starting_folder"""
        return [{"Code": country_iso3} for country_iso3 in self._countries_dict.keys()]

    def _populate_dimensions_db(self):
        """The main API only provides the dimension codes. This method
        queries the dimensions in the API to get their names, that can
        be used for quickcharts, etc."""
        logger.info("Populating dimensions DB")
        dimensions_url = f"{self._configuration['base_url']}api/dimension"
        dimensions_result = self._retriever.download_json(dimensions_url)["value"]
        for dimensions_row in dimensions_result:
            dimension_code = dimensions_row["Code"]
            dimension_title = dimensions_row["Title"]

            db_dimensions_row = DBDimensions(code=dimension_code, title=dimension_title)
            self._session.add(db_dimensions_row)
            self._session.commit()
            dimension_values_url = (
                f"{self._configuration['base_url']}api/DIMENSION/"
                f"{dimension_code}/DimensionValues"
            )
            dimension_values_result = self._retriever.download_json(
                dimension_values_url
            )["value"]
            for dimension_values_row in dimension_values_result:
                db_dimension_values_row = DBDimensionValues(
                    code=dimension_values_row["Code"],
                    title=dimension_values_row["Title"],
                    dimension_code=dimension_code,
                )
                self._session.add(db_dimension_values_row)
            self._session.commit()
        logger.info("Done populating dimensions DB")

    def _create_dimension_value_names_dict(self):
        results = self._session.query(DBDimensionValues).all()
        self._dimension_value_names_dict = {row.code: row.title for row in results}

    def _create_countries_dict(self):
        results = self._session.query(DBDimensionValues).filter(
            DBDimensionValues.dimension_code == "COUNTRY"
        )

        self._countries_dict = {
            row.code: Country.get_country_name_from_iso3(row.code) for row in results
        }

    def _populate_categories_and_indicators_db(self):
        # Get the indicator results
        indicator_url = f"{self._configuration['base_url']}api/indicator"
        indicator_result = self._retriever.download_json(indicator_url)["value"]

        # Loop through all indicators and add to table, checking for duplicates
        for indicator_row in indicator_result:
            db_indicators_row = DBIndicators(
                code=indicator_row["IndicatorCode"],
                title=indicator_row["IndicatorName"],
            )
            self._session.add(db_indicators_row)
        self._session.commit()

        # Get the category results
        category_url = (
            f"{self._configuration['category_url']}GHO_MODEL/SF_HIERARCHY_INDICATORS"
        )
        category_result = self._retriever.download_json(category_url)["value"]

        # Loop through categories and add to category DB table, also
        # add indicator URL to indicator.
        for category_row in category_result:
            # Some indicator codes have "\t" in them on the category page
            # which isn't present in the indicator page, such as RADON_Q602,
            # so need to .strip()
            indicator_code = category_row["INDICATOR_CODE"].strip()
            indicator_url = f"https://www.who.int/data/gho/data/indicators/indicator-details/GHO/{quote(category_row['INDICATOR_URL_NAME'])}"
            category_title = category_row["THEME_TITLE"]

            # Add the category to the table
            # Categories can repeat but should be unique in combination with
            # the indicator code, together the title and indicator code make the PK
            category_plus_indicator_exists = (
                self._session.query(DBCategories)
                .filter_by(title=category_title, indicator_code=indicator_code)
                .first()
            )
            if category_plus_indicator_exists:
                logger.warning(
                    f"Category {category_title} with indicator {indicator_code} already exists, skipping"
                )
                continue

            db_categories_row = DBCategories(
                title=category_title, indicator_code=indicator_code
            )
            self._session.add(db_categories_row)
            self._session.commit()
            # Add URL to indicator
            indicator_row = (
                self._session.query(DBIndicators)
                .filter(DBIndicators.code == indicator_code)
                .first()
            )
            if not indicator_row:
                logger.warning(
                    f"Indicator code {indicator_code} was not found on the "
                    f"indicators page"
                )
                continue
            else:
                indicator_row.url = indicator_url
                indicator_row.to_archive = False
            self._session.commit()

    def _create_tags(self, country_iso3: str, to_archive: bool):
        """Use category titles to create tags"""
        base_tags = ["hxl", "indicators"]
        if to_archive:
            return base_tags
        tags = []

        # This is done in a roundabout way for speed, doing it as a single sql
        # query is very slow
        country_category_names = []
        all_category_names = [
            row.title
            for row in self._session.query(DBCategories.title).distinct().all()
        ]
        for category_name in all_category_names:
            data_exists = (
                self._session.query(DBIndicatorData)
                .join(
                    DBIndicators,
                    DBIndicators.code == DBIndicatorData.indicator_code,
                )
                .join(
                    DBCategories,
                    DBCategories.indicator_code == DBIndicators.code,
                )
                .filter(DBCategories.title == category_name)
                .filter(DBIndicatorData.country_code == country_iso3)
                .filter(DBIndicators.to_archive.is_(false()))
                .first()
            )
            if data_exists:
                country_category_names.append(category_name)
        for category_name in country_category_names:
            parts = re.split(r"\s+and\s+", category_name, flags=re.IGNORECASE)
            for part in parts:
                cleaned = _clean_tag(part)
                if cleaned:
                    tags.append(cleaned)

        tags = list(OrderedDict.fromkeys(tags).keys())
        tags, _ = Vocabulary.get_mapped_tags(tags)
        tags = base_tags + tags
        return tags

    def _populate_indicator_data_db(self, create_archived_datasets: bool):
        for db_row in self._session.query(DBIndicators).all():
            indicator_name = db_row.title
            indicator_url = db_row.url
            indicator_code = db_row.code
            to_archive = db_row.to_archive

            # If we're not creating the archived datasets,
            # save time by not downloading and populating
            # the outdated indicators (there are thousands)
            if to_archive and not create_archived_datasets:
                continue

            logger.info(f"Downloading file for indicator {indicator_name}")
            base_url = self._configuration["base_url"]
            url = f"{base_url}api/{indicator_code}"
            try:
                indicator_json = self._retriever.download_json(url)
            except (DownloadError, FileNotFoundError):
                logger.warning(f"{url} has no data")
                continue
            logger.info(f"Populating DB for indicator {indicator_name}")

            batch = []
            irow = 0
            for row in indicator_json["value"]:
                if row["SpatialDimType"] != "COUNTRY":
                    continue
                country_iso3 = row["SpatialDim"]
                country_name = self._countries_dict[country_iso3]
                startyear = datetime.fromisoformat(row["TimeDimensionBegin"]).strftime(
                    "%Y"
                )
                endyear = datetime.fromisoformat(row["TimeDimensionEnd"]).strftime("%Y")
                db_indicators_row = dict(
                    id=row["Id"],
                    indicator_code=indicator_code,
                    indicator_name=indicator_name,
                    indicator_url=indicator_url,
                    year=row["TimeDim"],
                    start_year=startyear,
                    end_year=endyear,
                    region_code=row["ParentLocationCode"],
                    region_display=row["ParentLocation"],
                    country_code=country_iso3,
                    country_display=country_name,
                    dimension_type=row["Dim1Type"],
                    dimension_code=row["Dim1"],
                    dimension_name=self._dimension_value_names_dict.get(row["Dim1"]),
                    numeric=row["NumericValue"],
                    value=row["Value"],
                    low=row["Low"],
                    high=row["High"],
                )
                batch.append(db_indicators_row)
                irow += 1
                if len(batch) >= _BATCH_SIZE:
                    logger.info(f"Added {irow} rows")
                    self._session.execute(insert(DBIndicatorData), batch)
                    batch = []
            if batch:
                self._session.execute(insert(DBIndicatorData), batch)
            self._session.commit()
            logger.info(f"Done indicator {indicator_name}")

    @staticmethod
    def get_showcase(retriever, country_iso3, country_name, slugified_name, alltags):
        try:
            lower_iso3 = country_iso3.lower()
            url = f"https://www.who.int/countries/{lower_iso3}/en/"
            retriever.download_file(url)
            showcase = Showcase(
                {
                    "name": f"{slugified_name}-showcase",
                    "title": f"Indicators for {country_name}",
                    "notes": f"Health indicators for {country_name}",
                    "url": url,
                    "image_url": f"https://cdn.who.int/media/images/default-source/countries-overview/flags/{lower_iso3}.jpg",
                }
            )
            showcase.add_tags(alltags)
            return showcase
        except DownloadError:
            # If the showcase URL doesn't exist, only return the showcase id
            # so that it can be deleted if needed
            return Showcase({"name": f"{slugified_name}-showcase"})

    def generate_dataset_and_showcase(self, country):
        # Setup the dataset information
        country_iso3 = country["Code"]
        country_name = self._countries_dict[country_iso3]
        title = f"{country_name} - Health Indicators"

        logger.info(f"Creating dataset: {title}")
        slugified_name = slugify(f"WHO data for {country_iso3}").lower()

        # Get unique category names
        category_names = [
            row.title
            for row in self._session.query(DBCategories.title).distinct().all()
        ]
        cat_str = ", ".join(category_names)
        dataset = Dataset(
            {
                "name": slugified_name,
                "notes": f"This dataset contains data from WHO's "
                f"[data portal](https://www.who.int/gho/en/) covering "
                f"the following categories:  \n  \n"
                f"{cat_str}.  \n  \nFor links to individual indicator "
                f"metadata, see resource descriptions.",
                "title": title,
            }
        )
        dataset.set_subnational(False)
        try:
            dataset.add_country_location(country_iso3)
        except HDXError:
            logger.error(f"Couldn't find country {country_iso3}, skipping")
            return None, None
        tags = self._create_tags(country_iso3=country_iso3, to_archive=False)
        dataset.add_tags(tags)

        # Loop through categories and generate resource for each
        for category_name in category_names:
            logger.info(f"Category: {category_name}")

            all_rows_for_category = (
                self._session.query(DBIndicatorData)
                .join(
                    DBIndicators,
                    DBIndicators.code == DBIndicatorData.indicator_code,
                )
                .join(
                    DBCategories,
                    DBCategories.indicator_code == DBIndicators.code,
                )
                .filter(DBCategories.title == category_name)
                .filter(DBIndicatorData.country_code == country_iso3)
                # Create the archived dataset later
                .filter(DBIndicators.to_archive.is_(false()))
                .all()
            )

            category_data = [_parse_indicator_row(row) for row in all_rows_for_category]
            indicator_links = [
                f"[{row.title}]({row.url})"
                for row in (
                    self._session.query(DBIndicators)
                    .join(
                        DBCategories,
                        DBCategories.indicator_code == DBIndicators.code,
                    )
                    .filter(DBCategories.title == category_name)
                )
            ]

            category_link = f"*{category_name}:*\n{', '.join(indicator_links)}"
            slugified_category = slugify(category_name, separator="_")
            filename = f"{slugified_category}_indicators_{country_iso3.lower()}.csv"
            resourcedata = {
                "name": f"{category_name} Indicators for {country_name}",
                "description": category_link,
            }

            success, results = dataset.generate_resource_from_iterable(
                list(self._hxltags.keys()),
                category_data,
                self._hxltags,
                self._tempdir,
                filename,
                resourcedata,
                date_function=None,
                quickcharts=None,
            )

            if not success:
                logger.error(f"Resource for category {category_name} failed:{results}")

        # Create the dataset with all indicators

        filename = f"health_indicators_{country_iso3.lower()}.csv"
        resourcedata = {
            "name": f"All Health Indicators for {country_name}",
            "description": "See resource descriptions below for links "
            "to indicator metadata",
        }
        all_rows = (
            self._session.query(DBIndicatorData)
            .join(
                DBIndicators,
                DBIndicatorData.indicator_code == DBIndicators.code,
            )
            .filter(DBIndicatorData.country_code == country_iso3)
            .filter(DBIndicators.to_archive.is_(false()))
            .all()
        )

        all_indicators_data = [_parse_indicator_row(row) for row in all_rows]

        success_all_indicators, results_all_indicators = (
            dataset.generate_resource_from_iterable(
                list(self._hxltags.keys()),
                all_indicators_data,
                self._hxltags,
                self._tempdir,
                filename,
                resourcedata,
                date_function=_yearcol_function,
                quickcharts=None,
            )
        )

        if not success_all_indicators:
            logger.error(f"{country_name} has no data!")
            return None, None

        # Move the "all data" resource to the beginning
        # TODO: this doesn't appear to work on dev
        resources = dataset.get_resources()
        resources.insert(0, resources.pop(-2))

        showcase = self.get_showcase(
            self._retriever,
            country_iso3,
            country_name,
            slugified_name,
            tags,
        )
        return dataset, showcase

    def generate_archived_dataset(self, country):
        # Setup the dataset information
        country_iso3 = country["Code"]
        country_name = self._countries_dict[country_iso3]
        title = f"{country_name} - Historical Health Indicators"

        logger.info(f"Creating dataset: {title}")
        slugified_name = slugify(f"WHO historical data for {country_iso3}").lower()

        dataset = Dataset(
            {
                "name": slugified_name,
                "notes": "This dataset contains historical data from WHO's "
                "[data portal](https://www.who.int/gho/en/).",
                "title": title,
                "archived": True,
            }
        )
        dataset.set_expected_update_frequency("Never")
        dataset.set_subnational(False)
        try:
            dataset.add_country_location(country_iso3)
        except HDXError:
            logger.error(f"Couldn't find country {country_iso3}, skipping")
            return None
        tags = self._create_tags(country_iso3=country_iso3, to_archive=True)
        dataset.add_tags(tags)

        # Create the dataset with all indicators

        filename = f"historical_health_indicators_{country_iso3.lower()}.csv"
        resourcedata = {
            "name": f"All Historical Health Indicators for {country_name}",
            "description": "Historical health indicators no longer updated by WHO",
        }

        all_rows = (
            self._session.query(DBIndicatorData)
            .join(
                DBIndicators,
                DBIndicatorData.indicator_code == DBIndicators.code,
            )
            .filter(DBIndicatorData.country_code == country_iso3)
            .filter(DBIndicators.to_archive.is_(true()))
            .all()
        )
        all_indicators_data = [_parse_indicator_row(row) for row in all_rows]

        success_all_indicators, results_all_indicators = (
            dataset.generate_resource_from_iterable(
                list(self._hxltags.keys()),
                all_indicators_data,
                self._hxltags,
                self._tempdir,
                filename,
                resourcedata,
                date_function=_yearcol_function,
            )
        )

        if not success_all_indicators:
            logger.error(f"{country_name} has no data!")
            return None

        return dataset


def _parse_indicator_row(row):
    return {
        "GHO (CODE)": row.indicator_code,
        "GHO (DISPLAY)": row.indicator_name,
        "GHO (URL)": row.indicator_url,
        "YEAR (DISPLAY)": row.year,
        "STARTYEAR": row.start_year,
        "ENDYEAR": row.end_year,
        "REGION (CODE)": row.region_code,
        "REGION (DISPLAY)": row.region_display,
        "COUNTRY (CODE)": row.country_code,
        "COUNTRY (DISPLAY)": row.country_display,
        "DIMENSION (TYPE)": row.dimension_type,
        "DIMENSION (CODE)": row.dimension_code,
        "DIMENSION (NAME)": row.dimension_name,
        "Numeric": row.numeric,
        "Value": row.value,
        "Low": row.low,
        "High": row.high,
    }


def _yearcol_function(row):
    result = dict()
    year = row["YEAR (DISPLAY)"]
    if year:
        result["startdate"], result["enddate"] = parse_date_range(
            str(year), date_format="%Y"
        )
    return result
