from dynaconf import Dynaconf
from pathlib import Path
settings = Dynaconf(
    envvar_prefix="ENV",
    settings_files=['configs/settings.toml'],
    environments=True,
    load_dotenv=True,
)

from utils.pub_funs import load_json_file, get_test_paths

# 问题的JSON
paths = get_test_paths(settings.TEST_PATH)

TARGET_DIR = paths["target_dir"]
PROJECT_ROOT = paths["project_root"]
QUESTION_PATH = paths["questions"]
DOC_DIR = paths["docs_dir"]
LS_LABELED_CHUNKS_DIR = paths["ls_labeled_chunks_dir"]
ZLPT_CHUNKS_DIR = paths["lzpt_chunks_dir"]

QUESTION_TYPE_MAP = {
    "BASIC": 'basic_question.json',
    "DETAILED": 'detailed_question.json',
    "MECHANISM": 'mechanism_question.json',
    "THEMATIC": 'thematic_question.json',
}
q_dir = Path(QUESTION_PATH)
q_path = str(q_dir / QUESTION_TYPE_MAP[settings.QUESTION_TYPE])
QUESTION_JSON = load_json_file(q_path)
