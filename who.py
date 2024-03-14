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
from hdx.utilities.dateparse import parse_date_range
from hdx.utilities.dictandlist import dict_of_lists_add
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
        "Numeric": "#indicator+value+num",
        "Value": "#indicator+value",
        "Low": "#indicator+value+low",
        "High": "#indicator+value+high",
    }

    def __init__(self, configuration, retriever, folder):
        self.configuration = configuration
        self.retriever = retriever
        self.folder = folder

    def get_indicators_and_tags(self):
        indicators = OrderedDict()
        tags = list()
        category_url = self.configuration["category_url"]
        json = self.retriever.download_json(
            f"{category_url}GHO_MODEL/SF_HIERARCHY_INDICATORS"
        )
        result = json["value"]

        replacements = {"(": "", ")": "", "/": "", ",": ""}
        for indicator in result:
            indicator_code = indicator["INDICATOR_CODE"]
            indicator_url = f"https://www.who.int/data/gho/data/indicators/indicator-details/GHO/{quote(indicator['INDICATOR_URL_NAME'])}"
            category = indicator["THEME_TITLE"]
            dict_of_lists_add(
                indicators,
                category,
                (indicator_code, indicator["INDICATOR_TITLE"], indicator_url),
            )

            if " and " in category:
                tag_names = category.split(" and ")
                for tag_name in tag_names:
                    tags.append(
                        multiple_replace(tag_name.strip(), replacements)
                    )
            else:
                tags.append(multiple_replace(category.strip(), replacements))

        for category in indicators:
            indicators[category] = list(
                OrderedDict.fromkeys(indicators[category]).keys()
            )
        tags = list(OrderedDict.fromkeys(tags).keys())
        tags, _ = Vocabulary.get_mapped_tags(tags)

        return indicators, tags

    def get_countries(self):
        base_url = self.configuration["base_url"]
        json = self.retriever.download_json(
            f"{base_url}api/DIMENSION/COUNTRY/DimensionValues"
        )
        return json["value"]

    def generate_dataset_and_showcase(
        self, country, indicators, tags, quickcharts
    ):
        """
        https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim
        eq 'AFG'
        """
        base_url = self.configuration["base_url"]
        countryiso = country["Code"]
        countryname = Country.get_country_name_from_iso3(countryiso)

        title = f"{countryname} - Health Indicators"
        logger.info(f"Creating dataset: {title}")
        slugified_name = slugify(f"WHO data for {countryname}").lower()
        cat_str = ", ".join(indicators)
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
        alltags.extend(tags)
        dataset.add_tags(alltags)

        def yearcol_function(row):
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
                    _, result["enddate"] = parse_date_range(
                        endyear, date_format="%Y"
                    )
                else:
                    result["startdate"], result["enddate"] = parse_date_range(
                        year, date_format="%Y"
                    )
            return result

        all_rows = list()
        bites_disabled = [True, True, True]

        # i = 0
        for category in indicators:
            # if i >= 3:
            #     break  # for testing
            # i += 1
            logger.info(f"Category: {category}")
            category_data = list()
            indicator_codes = list()
            indicator_links = list()
            # count = 0

            for indicator_code, indicator_name, indicator_url in indicators[
                category
            ]:
                # if count >= 10:
                #     break  # for testing
                # count += 1
                logger.info(f"Indicator name: {indicator_name}")
                indicator_codes.append(indicator_code)
                indicator_links.append(f"[{indicator_name}]({indicator_url})")

                if indicator_code:
                    url = (
                        f"{base_url}api/{indicator_code}"
                        f"?$filter=SpatialDim eq '{countryiso}'"
                    )
                else:
                    continue

                try:
                    jsonresponse = self.retriever.download_json(url)
                # TODO: find exception
                except:  # noqa: E722
                    logger.warning(f"{url} has no data!")
                    continue

                for row in jsonresponse["value"]:
                    countryiso = row["SpatialDim"]
                    countryname = Country.get_country_name_from_iso3(
                        countryiso
                    )

                    startyear = datetime.fromisoformat(
                        row["TimeDimensionBegin"]
                    ).strftime("%Y")
                    endyear = datetime.fromisoformat(
                        row["TimeDimensionEnd"]
                    ).strftime("%Y")

                    obj = {
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
                        "Numeric": row["NumericValue"],
                        "Value": row["Value"],
                        "Low": row["Low"],
                        "High": row["High"],
                    }
                    category_data.append(obj)

            all_rows.extend(category_data)

            category_link = f"*{category}:*\n{', '.join(indicator_links)}"
            slugified_category = slugify(category, separator="_")
            filename = (
                f"{slugified_category}_indicators_{countryiso.lower()}.csv"
            )
            resourcedata = {
                "name": f"{category} Indicators for {countryname}",
                "description": category_link,
            }

            try:
                success, results = dataset.generate_resource_from_iterator(
                    list(self.hxltags.keys()),
                    category_data,
                    self.hxltags,
                    self.folder,
                    filename,
                    resourcedata,
                    date_function=yearcol_function,
                    quickcharts=None,
                )
            # TODO: find exception
            except:  # noqa: E722
                logger.warning(f"{category} has no data!")
                continue

        filename = f"health_indicators_{countryiso.lower()}.csv"
        resourcedata = {
            "name": f"All Health Indicators for {countryname}",
            "description": "See resource descriptions below for links "
            "to indicator metadata",
        }

        success, results = dataset.generate_resource_from_iterator(
            list(self.hxltags.keys()),
            all_rows,
            self.hxltags,
            self.folder,
            filename,
            resourcedata,
            date_function=None,
            quickcharts=quickcharts,
        )

        if success is False:
            logger.error(f"{countryname} has no data!")
            return None, None, None

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
