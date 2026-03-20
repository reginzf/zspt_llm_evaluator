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

# ── 变量收集（启动阶段，所有步骤共用）────────────────────────────
collect_inputs() {
    # 若已有变量（断点续跑）则跳过询问
    PYTHON_BIN="${PYTHON_BIN:-}"
    FRONTEND_PORT="${FRONTEND_PORT:-}"
    BACKEND_PORT="${BACKEND_PORT:-}"

    if [ -z "$PYTHON_BIN" ] && [ -z "$FRONTEND_PORT" ] && [ -z "$BACKEND_PORT" ]; then
        log_step "配置信息收集"
        printf "\n"

        printf "请输入 Python 3.12 可执行路径（留空则自动下载编译安装）: "
        read -r input_python
        save_var PYTHON_BIN "$input_python"

        printf "前端端口（默认 5002）: "
        read -r input_fe
        save_var FRONTEND_PORT "${input_fe:-5002}"

        printf "后端端口（默认 5001）: "
        read -r input_be
        save_var BACKEND_PORT "${input_be:-5001}"

        printf "\n"
        log_info "配置已保存到 $STATE_FILE"
    else
        log_info "使用已保存配置: Python=${PYTHON_BIN:-<自动安装>}, 前端端口=$FRONTEND_PORT, 后端端口=$BACKEND_PORT"
    fi
}

# ── Wheel 文件提示（每次启动都执行）──────────────────────────────
prompt_wheels() {
    # 动态从 requirements 文件中提取 file:// 条目的文件名
    local req_file="$PROJECT_ROOT/scripts/requirements_centos.txt"
    local wheel_files
    wheel_files=$(grep 'file:///' "$req_file" | sed 's|.*file:///[^/]*/||;s|#.*||' | tr -d ' ')

    printf "\n"
    log_info "requirements_centos.txt 中有以下本地 wheel 文件依赖，请确认已放置到以下位置之一："
    printf "  - %s/scripts/wheels/  （推荐）\n" "$PROJECT_ROOT"
    printf "  - %s/models/\n" "$PROJECT_ROOT"
    printf "  - /tmp/\n\n"
    printf "需要的文件:\n"
    while IFS= read -r whl; do
        [ -z "$whl" ] && continue
        printf "  - %s\n" "$whl"
    done <<< "$wheel_files"
    printf "\n按 Enter 继续，或 Ctrl+C 退出后上传文件..."
    read -r
    printf "\n"
}
