from dynaconf import Dynaconf
from pathlib import Path

settings = Dynaconf(
    envvar_prefix="ENV",
    settings_files=['configs/settings.toml'],
    environments=True,
    load_dotenv=True,
)

from utils.pub_funs import load_json_file, get_test_paths

# 初始化特使用例目录
paths = get_test_paths(settings.TEST_PATH)
CHUNK_NAME = f'chunk_{settings.CHUNK_SIZE}_{settings.CHUNK_OVERLAP}'
TARGET_DIR = paths["target_dir"]
PROJECT_ROOT = paths["project_root"]
QUESTION_PATH = paths["questions"]
DOC_DIR = paths["docs_dir"]
LS_LABELED_CHUNKS_DIR = str(Path(paths["ls_labeled_chunks_dir"]) / CHUNK_NAME)
ZLPT_CHUNKS_DIR = str(Path(paths["lzpt_chunks_dir"]) / CHUNK_NAME)
# 创建chunk归档目录
Path(LS_LABELED_CHUNKS_DIR).mkdir(parents=True, exist_ok=True)
Path(ZLPT_CHUNKS_DIR).mkdir(parents=True, exist_ok=True)

QUESTION_TYPE_MAP = {  # 问题类型映射
    "BASIC": 'basic_question.json',
    "DETAILED": 'detailed_question.json',
    "MECHANISM": 'mechanism_question.json',
    "THEMATIC": 'thematic_question.json',
}
q_dir = Path(QUESTION_PATH)
q_path = str(q_dir / QUESTION_TYPE_MAP[settings.QUESTION_TYPE])
# 问题的JSON
QUESTION_JSON = load_json_file(q_path)
# knowledge_dict
KNOWLEDGE_PATH = str(
    Path(PROJECT_ROOT) / 'tests' / fr'{settings.TEST_PATH}' / f'knowledge_{settings.CHUNK_SIZE}_{settings.CHUNK_OVERLAP}.json')
