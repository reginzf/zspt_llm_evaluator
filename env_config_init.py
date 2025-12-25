from dynaconf import Dynaconf
from pathlib import Path

settings = Dynaconf(
    envvar_prefix="ENV",
    settings_files=['configs/settings.toml'],
    environments=True,
    load_dotenv=True,
)

PROJECT_ROOT = settings.PROJECT_ROOT

QUESTION_TYPE_MAP = {  # 问题类型映射
    "BASIC": 'basic_question.json',
    "DETAILED": 'detailed_question.json',
    "MECHANISM": 'mechanism_question.json',
    "THEMATIC": 'thematic_question.json',
}
TYPE_DISPLAY_NAMES = {
    "factual": "事实型",
    "contextual": "上下文型",
    "conceptual": "概念型",
    "reasoning": "推理型",
    "application": "应用型"
}
# report的目录
REPORT_PATH = Path(PROJECT_ROOT) / 'reports' / 'report_data'
