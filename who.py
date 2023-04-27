#!/usr/bin/python
"""
WHO:
------------

Reads WHO API and creates datasets

"""
import logging
from collections import OrderedDict
from time import sleep

from hdx.data.dataset import Dataset
from hdx.data.hdxobject import HDXError
from hdx.data.showcase import Showcase
from hdx.data.vocabulary import Vocabulary
from hdx.location.country import Country
from hdx.utilities.dateparse import parse_date_range
from hdx.utilities.dictandlist import dict_of_lists_add
from hdx.utilities.text import multiple_replace
from slugify import slugify

logger = logging.getLogger(__name__)

hxlate = "&header-row=1&tagger-match-all=on&tagger-01-header=gho+%28code%29&tagger-01-tag=%23indicator%2Bcode&tagger-02-header=gho+%28display%29&tagger-02-tag=%23indicator%2Bname&tagger-03-header=gho+%28url%29&tagger-03-tag=%23indicator%2Burl&tagger-05-header=datasource+%28display%29&tagger-05-tag=%23meta%2Bsource&tagger-07-header=publishstate+%28code%29&tagger-07-tag=%23status%2Bcode&tagger-08-header=publishstate+%28display%29&tagger-08-tag=%23status%2Bname&tagger-11-header=year+%28display%29&tagger-11-tag=%23date%2Byear&tagger-13-header=region+%28code%29&tagger-13-tag=%23region%2Bcode&tagger-14-header=region+%28display%29&tagger-14-tag=%23region%2Bname&tagger-16-header=country+%28code%29&tagger-16-tag=%23country%2Bcode&tagger-17-header=country+%28display%29&tagger-17-tag=%23country%2Bname&tagger-19-header=sex+%28code%29&tagger-19-tag=%23sex%2Bcode&tagger-20-header=sex+%28display%29&tagger-20-tag=%23sex%2Bname&tagger-23-header=numeric&tagger-23-tag=%23indicator%2Bvalue%2Bnum&filter01=sort&sort-tags01=%23indicator%2Bcode%2C%23date%2Byear%2C%23sex%2Bcode"
hxltags = {
    "GHO (CODE)": "#indicator+code",
    "GHO (DISPLAY)": "#indicator+name",
    "GHO (URL)": "#indicator+url",
    "DATASOURCE (DISPLAY)": "#meta+source",
    "PUBLISHSTATE (CODE)": "#status+code",
    "PUBLISHSTATE (DISPLAY)": "#status+name",
    "YEAR (DISPLAY)": "#date+year",
    "STARTYEAR": "#date+year+start",
    "ENDYEAR": "#date+year+end",
    "REGION (CODE)": "#region+code",
    "REGION (DISPLAY)": "#region+name",
    "COUNTRY (CODE)": "#country+code",
    "COUNTRY (DISPLAY)": "#country+name",
    "SEX (CODE)": "#sex+code",
    "SEX (DISPLAY)": "#sex+name",
    "Numeric": "#indicator+value+num",
}
indicator_limit = 200


def get_indicators_and_tags(base_url, retriever):
    indicators = OrderedDict()
    tags = list()
    json = retriever.download_json(f"{base_url}api/GHO?format=json")
    result = json["dimension"][0]["code"]

    replacements = {"(": "", ")": "", "/": ""}
    for indicator in result:
        indicator_code = indicator["label"]
        if indicator_code[-9:] == "_ARCHIVED":
            continue
        category = None
        for attr in indicator["attr"]:
            if attr["category"] == "CATEGORY":
                category = attr["value"]
        if category is None:
            continue
        dict_of_lists_add(
            indicators,
            category,
            (indicator_code, indicator["display"], indicator["url"]),
        )
        if " and " in category:
            tag_names = category.split(" and ")
            for tag_name in tag_names:
                tags.append(multiple_replace(tag_name.strip(), replacements))
        else:
            tags.append(multiple_replace(category.strip(), replacements))
    for category in indicators:
        indicators[category] = list(OrderedDict.fromkeys(indicators[category]).keys())
    tags = list(OrderedDict.fromkeys(tags).keys())
    tags, _ = Vocabulary.get_mapped_tags(tags)
    return indicators, tags


def get_countries(base_url, retriever):
    json = retriever.download_json(f"{base_url}api/COUNTRY?format=json")
    return json["dimension"][0]["code"]


class RowError(Exception):
    pass


def generate_dataset_and_showcase(
    base_url, folder, country, indicators, tags, qc_indicators, retriever
):
    """
    http://apps.who.int/gho/athena/api/GHO/WHOSIS_000001.csv?filter=COUNTRY:BWA&profile=verbose
    """
    countryiso = country["label"]
    for attr in country["attr"]:
        if attr["category"] == "ISO":
            countryiso = attr["value"]
    countryname = Country.get_country_name_from_iso3(countryiso)
    if countryname is None:
        logger.warning(
            f"Ignoring ISO3 {country['display']} (WHO name: {countryiso}) for which HDX country name not found!"
        )
        return None, None, None
    title = f"{countryname} - Health Indicators"
    logger.info(f"Creating dataset: {title}")
    slugified_name = slugify(f"WHO data for {countryname}").lower()
    cat_str = ", ".join(indicators)
    dataset = Dataset(
        {
            "name": slugified_name,
            "notes": "Contains data from World Health Organization's [data portal](http://www.who.int/gho/en/) covering the following categories:  \n"
            f"{cat_str}  \n  \nFor links to individual indicator metadata, see resource descriptions.",
            "title": title,
        }
    )
    try:
        dataset.add_country_location(countryiso)
    except HDXError as e:
        logger.exception(f"{countryname} has a problem! {e}")
        return None, None, None
    dataset.set_maintainer("35f7bb2c-4ab6-4796-8334-525b30a94c89")
    dataset.set_organization("c021f6be-3598-418e-8f7f-c7a799194dba")
    dataset.set_expected_update_frequency("Every month")
    dataset.set_subnational(False)
    alltags = ["hxl", "indicators"]
    alltags.extend(tags)
    dataset.add_tags(alltags)

    def process_row(_, row):
        if "PUBLISHSTATE (CODE)" not in row:
            raise RowError("No PUBLISHSTATE (CODE)!")
        publishstate = row["PUBLISHSTATE (CODE)"]
        if publishstate is None:
            return None
        if "VOID" in publishstate:
            return None
        return row

    def process_date(row):
        year = row["YEAR (DISPLAY)"]
        result = dict()
        if not year:
            return result
        if "-" in year:
            yearrange = year.split("-")
            startyear = yearrange[0]
            endyear = yearrange[1]
            startdate, _ = parse_date_range(startyear)
            _, enddate = parse_date_range(endyear)
            row["STARTYEAR"] = int(startyear)
            row["ENDYEAR"] = int(endyear)
        else:
            startdate, enddate = parse_date_range(year)
            year = int(year)
            row["STARTYEAR"] = year
            row["ENDYEAR"] = year
        result["startdate"] = startdate
        result["enddate"] = enddate
        return result

    all_rows = list()
    qc_all_rows = list()
    insertions = [(13, "ENDYEAR"), (13, "STARTYEAR")]
    values = [x["code"] for x in qc_indicators]
    quickcharts = {
        "hashtag": "#indicator+code",
        "values": values,
        "numeric_hashtag": "#indicator+value+num",
        "cutdown": 1,
        "cutdownhashtags": [
            "#indicator+code",
            "#country+code",
            "#date+year+end",
            "#sex+name",
        ],
    }
    headers = None
    qcheaders = None
    bites_disabled = [True, True, True]
    for category in indicators:
        logger.info(f"Category: {category}")
        indicator_codes = list()
        indicator_links = list()
        for indicator_code, indicator_name, indicator_url in indicators[category]:
            indicator_codes.append(indicator_code)
            indicator_links.append(f"[{indicator_name}]({indicator_url})")
        category_link = f"*{category}:*\n{', '.join(indicator_links)}"
        slugified_category = slugify(category, separator="_")
        filename = f"{slugified_category}_indicators_{countryiso}.csv"
        resourcedata = {
            "name": f"{category} Indicators for {countryname}",
            "description": category_link,
        }
        indicator_list_len = len(indicator_codes)
        tries = 0
        error = False
        while tries < 5:
            i = 0
            rows = []
            while i < indicator_list_len:
                ie = min(i + indicator_limit, indicator_list_len)
                ic_str = ",".join(indicator_codes[i:ie])
                url = f"{base_url}data/data-verbose.csv?target=GHO/{ic_str}&filter=COUNTRY:{countryiso}&profile=verbose"
                ind_filename = filename.replace(".csv", f"_{i}.csv")
                fileheaders, iterator = retriever.get_tabular_rows(
                    url,
                    dict_form=True,
                    filename=ind_filename,
                    header_insertions=insertions,
                    row_function=process_row,
                    format="csv",
                    encoding="utf-8",
                )
                rows.extend(list(iterator))
                i += indicator_limit
            try:
                success, results = dataset.generate_resource_from_iterator(
                    fileheaders,
                    rows,
                    hxltags,
                    folder,
                    filename,
                    resourcedata,
                    date_function=process_date,
                    quickcharts=quickcharts,
                )
                error = False
                break
            except RowError:
                logger.warning("No PUBLISHSTATE (CODE)!")
                error = True
                sleep(600)
        if error is True:
            raise HDXError("WHO API has a problem!")
        if success is True:
            if len(all_rows) == 0:
                headers = fileheaders
                qcheaders = results["qcheaders"]
                all_rows.extend(results["rows"])
                qc_all_rows.extend(results["qcrows"])
            else:
                all_rows.extend(results["rows"][1:])
                qc_all_rows.extend(results["qcrows"][1:])
            for i, bite_disabled in enumerate(results["bites_disabled"]):
                if bite_disabled is False:
                    bites_disabled[i] = False
    if len(all_rows) == 0:
        logger.error(f"{countryname} has no data!")
        return None, None, None

    filename = f"health_indicators_{countryiso}.csv"
    resourcedata = {
        "name": f"All Health Indicators for {countryname}",
        "description": "See resource descriptions below for links to indicator metadata",
    }
    dataset.generate_resource_from_rows(
        folder, filename, all_rows, resourcedata, headers
    )

    resources = dataset.get_resources()
    resources.insert(0, resources.pop())

    filename = f"qc_health_indicators_{countryiso}.csv"
    resourcedata = {
        "name": f"QuickCharts Indicators for {countryname}",
        "description": "Cut down data for QuickCharts",
    }
    dataset.generate_resource_from_rows(
        folder, filename, qc_all_rows, resourcedata, qcheaders
    )

    isolower = countryiso.lower()
    showcase = Showcase(
        {
            "name": f"{slugified_name}-showcase",
            "title": f"Indicators for {countryname}",
            "notes": f"Health indicators for {countryname}",
            "url": f"http://www.who.int/countries/{isolower}/en/",
            "image_url": f"http://www.who.int/sysmedia/images/countries/{isolower}.gif",
        }
    )
    showcase.add_tags(alltags)
    return dataset, showcase, bites_disabled
