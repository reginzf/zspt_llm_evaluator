from dynaconf import Dynaconf
settings = Dynaconf(
    envvar_prefix="ENV",
    settings_files=['configs/settings.toml'],
    environments=True,
    load_dotenv=True,
)





