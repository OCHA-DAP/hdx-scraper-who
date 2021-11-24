#!/usr/bin/python
"""
Top level script. Calls other functions that generate datasets that this script then creates in HDX.

"""
import logging
from os.path import expanduser, join

from hdx.api.configuration import Configuration
from hdx.facades.simple import facade
from hdx.utilities.downloader import Download, DownloadError
from hdx.utilities.path import progress_storing_tempdir
from retry import retry
from who import generate_dataset_and_showcase, get_countries, get_indicators_and_tags

logger = logging.getLogger(__name__)

lookup = "hdx-scraper-who"


def main():
    """Generate dataset and create it in HDX"""

    configuration = Configuration.read()
    base_url = configuration["base_url"]
    qc_indicators = configuration["qc_indicators"]
    with Download(rate_limit={"calls": 1, "period": 1}) as downloader:
        indicators, tags = get_indicators_and_tags(base_url, downloader)
        countries = get_countries(base_url, downloader)
        logger.info(f"Number of datasets to upload: {len(countries)}")

        @retry(DownloadError, tries=5, delay=3600)
        def process_country(info, country):
            (dataset, showcase, bites_disabled,) = generate_dataset_and_showcase(
                base_url,
                info["folder"],
                country,
                indicators,
                tags,
                qc_indicators,
                downloadclass=Download,
            )
            if dataset:
                dataset.update_from_yaml()
                dataset.generate_resource_view(
                    -1, bites_disabled=bites_disabled, indicators=qc_indicators
                )
                dataset.create_in_hdx(
                    remove_additional_resources=True,
                    match_resource_order=True,
                    hxl_update=False,
                    updated_by_script="HDX Scraper: WHO",
                    batch=info["batch"],
                )
                showcase.create_in_hdx()
                showcase.add_dataset(dataset)

        for info, country in progress_storing_tempdir("WHO", countries, "label"):
            process_country(info, country)


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yml"),
        user_agent_lookup=lookup,
        project_config_yaml=join("config", "project_configuration.yml"),
    )
