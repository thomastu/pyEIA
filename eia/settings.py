from dynaconf import Dynaconf, constants

config = Dynaconf(
    envvar_prefix="EIA",
    load_dotenv=True,
    warn_dynaconf_global_settings=True,
    environments=True,
    default_env="eia",
    lowercase_read=False,
    default_settings_paths=constants.DEFAULT_SETTINGS_FILES,
)

APIKEY = config.get("APIKEY")
