#!/bin/bash
# AI-KEN CentOS 一键初始化脚本
# 目标平台: CentOS / RHEL 9 / Rocky Linux 9
# 使用方法: bash scripts/setup_centos.sh
# 注意: 上传前必须用 dos2unix 转换行尾为 LF

set -uo pipefail

# ── 颜色 ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { printf "${GREEN}[INFO]${NC}  %s\n" "$1"; }
log_warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$1"; }
log_error() { printf "${RED}[ERROR]${NC} %s\n" "$1"; }
log_step()  { printf "${BLUE}[STEP]${NC}  %s\n" "$1"; }
log_ok()    { printf "${GREEN}[OK]${NC}    %s\n" "$1"; }
log_fail()  { printf "${RED}[FAIL]${NC}  %s\n" "$1"; }

# ── 路径 ──────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_FILE="$PROJECT_ROOT/.setup_state"

log_info "PROJECT_ROOT: $PROJECT_ROOT"

# ── 状态文件工具 ──────────────────────────────────────────────────
# 初始化状态文件（若不存在）
init_state() {
    if [ ! -f "$STATE_FILE" ]; then
        touch "$STATE_FILE"
        echo 'COMPLETED_STEPS=""' >> "$STATE_FILE"
    fi
    # shellcheck source=/dev/null
    source "$STATE_FILE"
    COMPLETED_STEPS="${COMPLETED_STEPS:-}"
}

# 持久化单个变量到状态文件（先删旧行再追加）
save_var() {
    local key="$1"
    local val="$2"
    grep -v "^${key}=" "$STATE_FILE" > "${STATE_FILE}.tmp" && \
        mv "${STATE_FILE}.tmp" "$STATE_FILE"
    printf '%s="%s"\n' "$key" "$val" >> "$STATE_FILE"
    # 同步到当前 shell
    eval "${key}=\"${val}\""
}

# 标记步骤完成
mark_done() {
    local step="$1"
    COMPLETED_STEPS="$COMPLETED_STEPS $step"
    grep -v '^COMPLETED_STEPS=' "$STATE_FILE" > "${STATE_FILE}.tmp" && \
        mv "${STATE_FILE}.tmp" "$STATE_FILE"
    printf 'COMPLETED_STEPS="%s"\n' "$COMPLETED_STEPS" >> "$STATE_FILE"
}

# 判断步骤是否已完成
is_done() {
    echo "$COMPLETED_STEPS" | grep -qw "$1"
}
