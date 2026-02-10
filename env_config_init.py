from dynaconf import Dynaconf
from pathlib import Path

settings = Dynaconf(
    envvar_prefix="ENV",
    settings_files=['configs/settings.toml'],
    environments=True,
    load_dotenv=True,
)
PROJECT_ROOT = Path(settings.PROJECT_ROOT)
# report的目录
REPORT_PATH = PROJECT_ROOT / 'reports' / 'report_data'
# config的目录
CONFIG_PATH = PROJECT_ROOT / 'configs'