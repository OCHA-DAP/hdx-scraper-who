### Collector for WHO's Datasets
[![Run tests](https://github.com/OCHA-DAP/hdx-scraper-who/actions/workflows/run-python-tests.yml/badge.svg)](https://github.com/OCHA-DAP/hdx-scraper-who/actions/workflows/run-python-tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-scraper-who/badge.svg?branch=main&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-scraper-who?branch=main)

This script connects to the [World Health Organization](http://apps.who.int/gho/data/node.resources.api) and extracts data country by country creating a dataset per country in HDX. It makes around 32000 reads from WHO and then 1000 read/writes (API calls) to HDX in a one hour period. It creates a temporary file of less than 1Mb per country. It runs every month.


### Usage

    python run.py

For the script to run, you will need to have a file called .hdx_configuration.yml in your home directory containing your HDX key eg.

    hdx_key: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    hdx_read_only: false
    hdx_site: prod

 You will also need to supply the universal .useragents.yml file in your home directory as specified in the parameter *user_agent_config_yaml* passed to facade in run.py. The collector reads the key **hdx-scraper-who** as specified in the parameter *user_agent_lookup*.

 Alternatively, you can set up environment variables: USER_AGENT, HDX_KEY, HDX_SITE, EXTRA_PARAMS, TEMP_DIR, LOG_FILE_ONLY


## Development

Be sure to install `pre-commit`, which is run every time
you make a git commit:

```shell
pip install pre-commit
pre-commit install
```

The configuration file for this project is in a
non-start location. Thus, you will need to edit your
`.git/hooks/pre-commit` file to reflect this. Change
the first line that begins with `ARGS` to:

```shell
ARGS=(hook-impl --config=.config/pre-commit-config.yaml --hook-type=pre-commit)
```

With pre-commit, all code is formatted according to
[black]("https://github.com/psf/black") and
[ruff]("https://github.com/charliermarsh/ruff") guidelines.

To check if your changes pass pre-commit without committing, run:

```shell
pre-commit run --all-files --config=.config/pre-commit-config.yaml
