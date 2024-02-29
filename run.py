#!/usr/bin/python
"""
Top level script. Calls other functions that generate datasets that this script then creates in HDX.

"""
import logging
from os import remove
from os.path import expanduser, join

from hdx.api.configuration import Configuration
from hdx.data.hdxobject import HDXError
from hdx.facades.infer_arguments import facade
from hdx.utilities.downloader import Download, DownloadError
from hdx.utilities.path import progress_storing_folder, wheretostart_tempdir_batch
from hdx.utilities.retriever import Retrieve
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)
from who import generate_dataset_and_showcase, get_countries, get_indicators_and_tags

logger = logging.getLogger(__name__)

lookup = "hdx-scraper-who"


def main(save: bool = False, use_saved: bool = False) -> None:
    """Generate datasets and create them in HDX

    Args:
        save (bool): Save downloaded data. Defaults to False.
        use_saved (bool): Use saved data. Defaults to False.

    Returns:
        None
    """
    configuration = Configuration.read()
    base_url = configuration["base_url2"]
    category_url = configuration["category_url"]
    qc_indicators = configuration["qc_indicators"]
    with wheretostart_tempdir_batch(lookup) as info:
        folder = info["folder"]
        with Download(rate_limit={"calls": 1, "period": 1}) as downloader:
            retriever = Retrieve(
                downloader, folder, "saved_data", folder, save, use_saved
            )

            indicators, tags = get_indicators_and_tags(category_url, retriever)
            #countries_temp = get_countries(base_url, retriever)
            #print(countries_temp[0])
            #countries = [countries_temp[0]]
            countries = get_countries(base_url, retriever)
            logger.info(f"Number of datasets to upload: {len(countries)}")

            @retry(
                retry=(
                    retry_if_exception_type(DownloadError)
                    | retry_if_exception_type(HDXError)
                ),
                stop=stop_after_attempt(5),
                wait=wait_fixed(3600),
                after=after_log(logger, logging.INFO),
            )
            def process_country(country):
                print('hi', country)
                (dataset, showcase, bites_disabled,) = generate_dataset_and_showcase(
                    base_url,
                    info["folder"],
                    country,
                    indicators,
                    tags,
                    qc_indicators,
                    retriever,
                )
                if dataset:
                    dataset.update_from_yaml()
                    dataset.generate_quickcharts(
                        -1, bites_disabled=bites_disabled, indicators=qc_indicators
                    )
                    paths = [x.get_file_to_upload() for x in dataset.get_resources()]
                    dataset.create_in_hdx(
                        remove_additional_resources=True,
                        match_resource_order=True,
                        hxl_update=False,
                        updated_by_script="HDX Scraper: WHO",
                        batch=info["batch"],
                    )
                    showcase.create_in_hdx()
                    showcase.add_dataset(dataset)

                    for path in paths:
                        try:  # Needed while there are duplicate categories
                            remove(path)
                        except OSError:
                            pass

            print('1', info)
            print('2', progress_storing_folder)
            print('3', countries)
            for _, country in progress_storing_folder(info, countries, "Code"):
                print('-',country)
                process_country(country)


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yml"),
        user_agent_lookup=lookup,
        project_config_yaml=join("config", "project_configuration.yml"),
    )
