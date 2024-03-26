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

    def __init__(self, configuration, retriever, folder):
        self._configuration = configuration
        self._retriever = retriever
        self._folder = folder
        self._dimension_names = self._get_dimension_names()
        self._indicators, self._tags, self._categories = (
            self._get_indicators_and_tags()
        )

    def get_countries(self):
        # TODO: combine with get dimension names
        base_url = self._configuration["base_url"]
        json = self._retriever.download_json(
            f"{base_url}api/DIMENSION/COUNTRY/DimensionValues"
        )
        return json["value"]

    def generate_dataset_and_showcase(self, country, quickcharts):

        # Setup the dataset information
        base_url = self._configuration["base_url"]
        countryiso = country["Code"]
        countryname = Country.get_country_name_from_iso3(countryiso)

        title = f"{countryname} - Health Indicators"
        logger.info(f"Creating dataset: {title}")
        slugified_name = slugify(f"WHO data for {countryiso}").lower()
        # TODO: check this works
        cat_str = ", ".join(self._indicators.keys())
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
        dataset.add_country_location(countryiso)
        alltags = ["hxl", "indicators"]
        alltags.extend(self._tags)
        dataset.add_tags(alltags)

        # Loop through the indicators to download the data for each,
        # saving the rows in a dictionary with indicator code keys, which can
        # will used to build the categories files
        all_indicators_data = OrderedDict()
        for indicator_code, indicator_dict in self._indicators.items():
            indicator_name = indicator_dict["indicator_name"]
            # Some indicators don't have URLs, if they don't have a theme
            indicator_url = indicator_dict.get("indicator_url")
            logger.info(f"Indicator name: {indicator_name}")
            # URL for a specific indicator and country:
            # https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim eq 'AFG' # noqa E501
            url = (
                f"{base_url}api/{indicator_code}?$filter=SpatialDim eq "
                f"'{countryiso}'"
            )
            try:
                indicator_json = self._retriever.download_json(url)
            except (DownloadError, FileNotFoundError):
                logger.warning(f"{url} has no data!")
                continue
            indicator_data = [
                self._parse_indicator_row(
                    row, indicator_code, indicator_name, indicator_url
                )
                for row in indicator_json["value"]
            ]
            all_indicators_data[indicator_code] = indicator_data

        # Loop through categories and generate resource for each
        for category_name, indicator_dict in self._categories.items():

            logger.info(f"Category: {category_name}")

            category_data = list()
            indicator_links = list()

            for indicator_code in indicator_dict.keys():

                indicator_name = self._indicators[indicator_code][
                    "indicator_name"
                ]
                indicator_url = self._indicators[indicator_code][
                    "indicator_url"
                ]
                indicator_links.append(f"[{indicator_name}]({indicator_url})")
                category_data.extend(all_indicators_data[indicator_code])

            category_link = f"*{category_name}:*\n{', '.join(indicator_links)}"
            slugified_category = slugify(category_name, separator="_")
            filename = (
                f"{slugified_category}_indicators_{countryiso.lower()}.csv"
            )
            resourcedata = {
                "name": f"{category_name} Indicators for {countryname}",
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
        filename = f"health_indicators_{countryiso.lower()}.csv"
        resourcedata = {
            "name": f"All Health Indicators for {countryname}",
            "description": "See resource descriptions below for links "
            "to indicator metadata",
        }

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
            logger.error(f"{countryname} has no data!")
            return None, None, None

        # Move the all data resource to the beginning
        # TODO: this doesn't appear to work on dev
        resources = dataset.get_resources()
        resources.insert(0, resources.pop(-2))

        bites_disabled = results["bites_disabled"]

        showcase = Showcase(
            {
                "name": f"{slugified_name}-showcase",
                "title": f"Indicators for {countryname}",
                "notes": f"Health indicators for {countryname}",
                "url": f"http://www.who.int/countries/{countryiso.lower()}/en/",
                "image_url": f"http://www.who.int/sysmedia/images/countries/{countryiso.lower()}.gif",
            }
        )
        showcase.add_tags(alltags)

        return dataset, showcase, bites_disabled

    def _get_dimension_names(self):
        """The main API only provides the dimension codes. This method
        queries the dimensions in the API to get their names, that can
        be used for quickcharts, etc."""

        dimension_names = OrderedDict()
        all_dimensions_url = f"{self._configuration['base_url']}api/dimension"
        all_dimensions_result = self._retriever.download_json(
            all_dimensions_url
        )["value"]
        for all_dimensions_row in all_dimensions_result:
            dimension_url = (
                f"{self._configuration['base_url']}api/DIMENSION/"
                f"{all_dimensions_row['Code']}/DimensionValues"
            )
            dimension_result = self._retriever.download_json(dimension_url)[
                "value"
            ]
            for dimension_row in dimension_result:
                dimension_names[dimension_row["Code"]] = dimension_row["Title"]
        return dimension_names

    def _get_indicators_and_tags(self):
        # The indicators dictionary will use the indicator codes as a key,
        # where the values are another dictionary that contains the indicator
        # name and, if available, the indicator URL
        indicators = OrderedDict()
        # The categories dictionary contains all the category names as keys,
        # with a set of indicator codes as values. A set is used because
        # the API contains duplicate indicator / category pairs.
        # It would make sense to use defaultdict with a set, but that
        # does not preserve ordering.
        categories = OrderedDict()
        tags = list()

        # Query for the indicators and categories
        indicator_url = f"{self._configuration['base_url']}api/indicator"
        indicator_result = self._retriever.download_json(indicator_url)[
            "value"
        ]
        category_url = (
            f"{self._configuration['category_url']}"
            f"GHO_MODEL/SF_HIERARCHY_INDICATORS"
        )
        category_result = self._retriever.download_json(category_url)["value"]

        # Loop through all indicators, getting the codes to use as keys,
        # and saving the indicator names
        for indicator in indicator_result:
            indicators[indicator["IndicatorCode"]] = {
                "indicator_name": indicator["IndicatorName"]
            }

        # Loop through all categories, and add indicators to associated set.
        # Also add the indicator URL (which is not present in the indicator
        # query) to the indicators dict.
        replacements = {"(": "", ")": "", "/": "", ",": ""}
        for category in category_result:
            # Some indicator codes have "\t" in them on the category page
            # which isn't present in the indicator page, such as RADON_Q602,
            # so need to .strip()
            indicator_code = category["INDICATOR_CODE"].strip()
            indicator_url = f"https://www.who.int/data/gho/data/indicators/indicator-details/GHO/{quote(category['INDICATOR_URL_NAME'])}"
            category_title = category["THEME_TITLE"]

            # Add indicator URL to indicator dictionary
            try:
                indicators[indicator_code]["indicator_url"] = indicator_url
            except KeyError:
                logger.error(
                    f"Indicator code {indicator_code} was not found"
                    f"on the indicators page"
                )
                continue

            # Add indicator to categories. Use an OrderedDict (with values
            # set to None) instead of a set to maintain the order.
            if category_title not in categories:
                categories[category_title] = OrderedDict()
            categories[category_title][indicator_code] = None

            # Use the category title to create tags
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

        return indicators, tags, categories

    def _parse_indicator_row(
        self, row, indicator_code, indicator_name, indicator_url
    ):
        countryiso = row["SpatialDim"]
        countryname = Country.get_country_name_from_iso3(countryiso)

        startyear = datetime.fromisoformat(row["TimeDimensionBegin"]).strftime(
            "%Y"
        )
        endyear = datetime.fromisoformat(row["TimeDimensionEnd"]).strftime(
            "%Y"
        )

        return {
            "GHO (CODE)": indicator_code,
            "GHO (DISPLAY)": indicator_name,
            "GHO (URL)": indicator_url,
            "YEAR (DISPLAY)": row["TimeDim"],
            "STARTYEAR": startyear,
            "ENDYEAR": endyear,
            "REGION (CODE)": row["ParentLocationCode"],
            "REGION (DISPLAY)": row["ParentLocation"],
            "COUNTRY (CODE)": countryiso,
            "COUNTRY (DISPLAY)": countryname,
            "DIMENSION (TYPE)": row["Dim1Type"],
            "DIMENSION (CODE)": row["Dim1"],
            "DIMENSION (NAME)": self._dimension_names.get(row["Dim1"]),
            "Numeric": row["NumericValue"],
            "Value": row["Value"],
            "Low": row["Low"],
            "High": row["High"],
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
