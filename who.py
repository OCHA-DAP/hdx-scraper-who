#!/usr/bin/python
"""
WHO:
------------

Reads WHO API and creates datasets

"""
import logging
from collections import OrderedDict
from datetime import datetime
from urllib.parse import quote

from hdx.data.dataset import Dataset
from hdx.data.showcase import Showcase
from hdx.data.vocabulary import Vocabulary
from hdx.location.country import Country
from hdx.utilities.base_downloader import DownloadError
from hdx.utilities.dateparse import parse_date_range
from hdx.utilities.text import multiple_replace
from slugify import slugify

from database.db_categories import DBCategories
from database.db_dimension_values import DBDimensionValues
from database.db_dimensions import DBDimensions
from database.db_indicator_data import DBIndicatorData
from database.db_indicators import DBIndicators

logger = logging.getLogger(__name__)


class WHO:
    hxltags = {
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

    def __init__(self, configuration, retriever, folder, session):
        self._configuration = configuration
        self._retriever = retriever
        self._folder = folder
        self._session = session
        self._dimension_value_names_dict = dict()
        self._tags = list()

    def populate_dimensions_db(self):
        """The main API only provides the dimension codes. This method
        queries the dimensions in the API to get their names, that can
        be used for quickcharts, etc."""
        logger.info("Populating dimensions DB")
        dimensions_url = f"{self._configuration['base_url']}api/dimension"
        dimensions_result = self._retriever.download_json(dimensions_url)[
            "value"
        ]
        for dimensions_row in dimensions_result:
            dimension_code = dimensions_row["Code"]
            db_dimensions_row = DBDimensions(
                code=dimension_code, title=dimensions_row["Title"]
            )
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

    def create_dimension_names_dict(self):
        results = self._session.query(DBDimensionValues).all()
        self._dimension_value_names_dict = {
            row.code: row.title for row in results
        }

    def get_countries(self):
        results = self._session.query(DBDimensionValues).filter(
            DBDimensionValues.dimension_code == "COUNTRY"
        )
        return [row.code for row in results]

    def populate_categories_and_indicators_db(self):
        # Get the indicator results
        indicator_url = f"{self._configuration['base_url']}api/indicator"
        indicator_result = self._retriever.download_json(indicator_url)[
            "value"
        ]

        # Loop through all indicators and add to table
        for indicator_row in indicator_result:
            db_indicators_row = DBIndicators(
                code=indicator_row["IndicatorCode"],
                title=indicator_row["IndicatorName"],
            )
            self._session.add(db_indicators_row)
        self._session.commit()

        # Get the category results
        category_url = (
            f"{self._configuration['category_url']}"
            f"GHO_MODEL/SF_HIERARCHY_INDICATORS"
        )
        category_result = self._retriever.download_json(category_url)["value"]

        # Loop through categories and add to category DB table, also
        # add the category to the indicator
        for category_row in category_result:
            # Some indicator codes have "\t" in them on the category page
            # which isn't present in the indicator page, such as RADON_Q602,
            # so need to .strip()
            indicator_code = category_row["INDICATOR_CODE"].strip()
            indicator_url = f"https://www.who.int/data/gho/data/indicators/indicator-details/GHO/{quote(category_row['INDICATOR_URL_NAME'])}"
            category_title = category_row["THEME_TITLE"]

            # Add the category to the table
            category_already_exists = (
                self._session.query(DBCategories)
                .filter(DBCategories.title == category_title)
                .first()
            )
            if not category_already_exists:
                db_categories_row = DBCategories(title=category_title)
                self._session.add(db_categories_row)
                self._session.commit()
            # Add category and URL to indicator
            result = (
                self._session.query(DBIndicators)
                .filter(DBIndicators.code == indicator_code)
                .first()
            )
            if not result:
                logger.warning(
                    f"Indicator code {indicator_code} was not found on the "
                    f"indicators page"
                )
                continue
            result.url = indicator_url
            result.category_title = category_title
            self._session.commit()

    def create_tags(self):
        """Use category titles to create tags"""
        tags = []
        replacements = {"(": "", ")": "", "/": "", ",": ""}
        result = self._session.query(DBCategories).all()
        for category_row in result:
            category_title = category_row.title
            if " and " in category_title:
                tag_names = category_title.split(" and ")
                for tag_name in tag_names:
                    tags.append(
                        multiple_replace(tag_name.strip(), replacements)
                    )
            else:
                tags.append(
                    multiple_replace(category_title.strip(), replacements)
                )

        tags = list(OrderedDict.fromkeys(tags).keys())
        tags, _ = Vocabulary.get_mapped_tags(tags)

        self._tags = tags

    def populate_indicator_data_db(self):
        for db_row in self._session.query(DBIndicators).all():
            indicator_name = db_row.title
            indicator_url = db_row.url
            indicator_code = db_row.code
            logger.info(f"Downloading file for indicator {indicator_name}")
            base_url = self._configuration["base_url"]
            url = f"{base_url}api/{indicator_code}"
            try:
                indicator_json = self._retriever.download_json(url)
            except (DownloadError, FileNotFoundError):
                logger.warning(f"{url} has no data")
                continue
            logger.info(f"Populating DB for indicator {indicator_name}")
            for row in indicator_json["value"]:
                if row["SpatialDimType"] != "COUNTRY":
                    continue
                country_iso3 = row["SpatialDim"]
                country_name = Country.get_country_name_from_iso3(country_iso3)
                startyear = datetime.fromisoformat(
                    row["TimeDimensionBegin"]
                ).strftime("%Y")
                endyear = datetime.fromisoformat(
                    row["TimeDimensionEnd"]
                ).strftime("%Y")
                db_indicators_row = DBIndicatorData(
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
                    dimension_name=self._dimension_value_names_dict.get(
                        row["Dim1"]
                    ),
                    numeric=row["NumericValue"],
                    value=row["Value"],
                    low=row["Low"],
                    high=row["High"],
                )
                self._session.add(db_indicators_row)
            self._session.commit()
            logger.info(f"Done indicator {indicator_name}")

    def generate_dataset_and_showcase(self, country_iso3, quickcharts):
        # Setup the dataset information
        country_name = Country.get_country_name_from_iso3(country_iso3)
        title = f"{country_name} - Health Indicators"

        logger.info(f"Creating dataset: {title}")
        slugified_name = slugify(f"WHO data for {country_iso3}").lower()

        category_names = [
            row.title for row in self._session.query(DBCategories).all()
        ]
        cat_str = ", ".join(category_names)
        dataset = Dataset(
            {
                "name": slugified_name,
                "notes": "Contains data from World Health Organization's "
                "[data portal](http://www.who.int/gho/en/) covering "
                "the following categories:  \n"
                f"{cat_str}  \n  \nFor links to individual indicator "
                f"metadata, see resource descriptions.",
                "title": title,
            }
        )
        dataset.set_maintainer("35f7bb2c-4ab6-4796-8334-525b30a94c89")
        dataset.set_organization("c021f6be-3598-418e-8f7f-c7a799194dba")
        dataset.set_expected_update_frequency("Every month")
        dataset.set_subnational(False)
        dataset.add_country_location(country_iso3)
        alltags = ["hxl", "indicators"]
        alltags.extend(self._tags)
        dataset.add_tags(alltags)

        # Loop through categories and generate resource for each

        for category_name in category_names:
            logger.info(f"Category: {category_name}")
            all_category_rows = (
                self._session.query(DBIndicatorData)
                .join(
                    DBIndicators,
                    DBIndicatorData.indicator_code == DBIndicators.code,
                )
                .join(
                    DBCategories,
                    DBIndicators.category_title == DBCategories.title,
                )
                .filter(DBIndicatorData.country_code == country_iso3)
                .filter(DBCategories.title == category_name)
                .all()
            )

            category_data = [_parse_indicator_row for row in all_category_rows]
            indicator_links = [
                f"[{row.title}]({row.url})"
                for row in self._session.query(DBIndicators).filter(
                    DBIndicators.category_title == category_name
                )
            ]

            category_link = f"*{category_name}:*\n{', '.join(indicator_links)}"
            slugified_category = slugify(category_name, separator="_")
            filename = (
                f"{slugified_category}_indicators_{country_iso3.lower()}.csv"
            )
            resourcedata = {
                "name": f"{category_name} Indicators for {country_name}",
                "description": category_link,
            }

            success, results = dataset.generate_resource_from_iterator(
                list(self.hxltags.keys()),
                category_data,
                self.hxltags,
                self._folder,
                filename,
                resourcedata,
                date_function=_yearcol_function,
                quickcharts=None,
            )

            if not success:
                logger.error(
                    f"Resource for category {category_name} failed:"
                    f"{results}"
                )

        # Create the final dataset with all indicators
        filename = f"health_indicators_{country_iso3.lower()}.csv"
        resourcedata = {
            "name": f"All Health Indicators for {country_name}",
            "description": "See resource descriptions below for links "
            "to indicator metadata",
        }
        # TODO: just get all indicators data
        all_rows = (
            self._session.query(DBIndicatorData)
            .filter(DBIndicatorData.country_code == country_iso3)
            .all()
        )
        all_indicators_data = [_parse_indicator_row for row in all_rows]

        success, results = dataset.generate_resource_from_iterator(
            list(self.hxltags.keys()),
            # This line makes one long list of all indicators data,
            # removing the indicator code as keys
            sum(all_indicators_data.values(), []),
            self.hxltags,
            self._folder,
            filename,
            resourcedata,
            date_function=None,
            quickcharts=quickcharts,
        )

        if not success:
            logger.error(f"{country_name} has no data!")
            return None, None, None

        # Move the all data resource to the beginning
        # TODO: this doesn't appear to work on dev
        resources = dataset.get_resources()
        resources.insert(0, resources.pop(-2))

        bites_disabled = results["bites_disabled"]

        showcase = Showcase(
            {
                "name": f"{slugified_name}-showcase",
                "title": f"Indicators for {country_name}",
                "notes": f"Health indicators for {country_name}",
                "url": f"http://www.who.int/countries/{country_iso3.lower()}/en/",
                "image_url": f"http://www.who.int/sysmedia/images/countries/{country_iso3.lower()}.gif",
            }
        )
        showcase.add_tags(alltags)

        return dataset, showcase, bites_disabled


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
        "COUNTRY (DISPLAY)": row.country_name,
        "DIMENSION (TYPE)": row.dimension_type,
        "DIMENSION (CODE)": row.dimension_code,
        "DIMENSION (NAME)": row.dimension_name,
        "Numeric": row.numeric,
        "Value": row.value,
        "Low": row.low,
        "High": row.hight,
    }


def _yearcol_function(row):
    result = dict()
    year = row["YEAR (DISPLAY)"]
    if year:
        year = str(year)
        if len(year) == 9:
            startyear = year[:4]
            endyear = year[5:]
            result["startdate"], _ = parse_date_range(
                startyear, date_format="%Y"
            )
            _, result["enddate"] = parse_date_range(endyear, date_format="%Y")
        else:
            result["startdate"], result["enddate"] = parse_date_range(
                year, date_format="%Y"
            )
    return result
