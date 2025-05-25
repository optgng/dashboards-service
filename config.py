from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="SYSTEM_MONITORING",
    settings_files=['settings.toml', '.env'],
    environments=True,
    load_dotenv=True,
)
