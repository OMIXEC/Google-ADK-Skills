#!/bin/bash
#
# Claude-ADK-Skills Installation Script
# IDE-agnostic: supports Claude Code, Gemini CLI, OpenCode, Cursor, and more.
#
# Usage:
#   bash install.sh                           # auto-detect IDE
#   bash install.sh --target claude-code       # specific IDE
#   bash install.sh --target all               # all detected IDEs
#   bash install.sh --target gemini-cli --copy # copy instead of symlink
#
# Public, no-auth: clones over HTTPS, falls back to a tarball download when
# git is unavailable. Downloads skills, evals (tests/) and scripts.

set -e

# ── Colors ──────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ── Configuration ───────────────────────────────────
REPO_OWNER="OMIXEC"
REPO_NAME="Claude-ADK-Skills"
INSTALL_DIR="${HOME}/.claude-adk-skills"
VENV_DIR="${INSTALL_DIR}/venv"
MIN_PYTHON_VERSION="3.11"

# IDE skills directories (bash 3.2 compatible — use functions, not associative arrays)

ALL_IDES="claude-code gemini-cli opencode cursor windsurf codex"

get_skills_dir() {
    case "$1" in
        claude-code) echo "${HOME}/.claude/skills" ;;
        gemini-cli)  echo "${HOME}/.gemini/skills" ;;
        opencode)    echo "${HOME}/.opencode/skills" ;;
        cursor)      echo "${HOME}/.cursor/skills" ;;
        windsurf)    echo "${HOME}/.windsurf/skills" ;;
        codex)       echo "${HOME}/.codex/skills" ;;
        *)           echo "" ;;
    esac
}

get_cli_cmd() {
    case "$1" in
        claude-code) echo "claude" ;;
        gemini-cli)  echo "gemini" ;;
        opencode)    echo "opencode" ;;
        cursor)      echo "cursor" ;;
        codex)       echo "codex" ;;
        *)           echo "" ;;
    esac
}

# ── Parse arguments ─────────────────────────────────
TARGET_IDE="auto"
LINK_METHOD="symlink"
VERBOSE=false
SKIP_DEPS=false
FORCE=false
GIT_REF="main"

print_banner() {
    echo -e "${BLUE}"
    echo "======================================"
    echo "  Claude-ADK-Skills Installer"
    echo "  IDE-Agnostic Skill Template"
    echo "======================================"
    echo -e "${NC}"
}

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "${BLUE}[STEP]${NC} $1"; }

show_help() {
    echo "Usage: install.sh [OPTIONS]"
    echo ""
    echo "Public, no-auth installer. Clones over HTTPS; falls back to a tarball"
    echo "download when git is missing or the clone fails."
    echo ""
    echo "IDE Target:"
    echo "  --target IDE       Install for specific IDE"
    echo "                     Values: claude-code, gemini-cli, opencode, cursor,"
    echo "                             windsurf, codex, all, auto (default)"
    echo "  --copy             Copy files instead of symlinking (default: symlink)"
    echo ""
    echo "Other:"
    echo "  --install-dir DIR  Custom install directory (default: ~/.claude-adk-skills)"
    echo "  --ref REF          Git branch/tag to install (default: main)"
    echo "  --skip-deps        Skip Python dependency installation"
    echo "  --force            Force reinstall"
    echo "  --verbose          Verbose output"
    echo "  --help             Show this help"
    echo ""
    echo "Examples:"
    echo "  bash install.sh                              # Auto-detect IDE"
    echo "  bash install.sh --target claude-code          # Claude Code only"
    echo "  bash install.sh --target all --copy           # All IDEs, copy mode"
    echo "  curl -fsSL https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/main/install.sh | bash"
    echo ""
    echo "Alternative — install as a Claude Code plugin (no clone needed):"
    echo "  /plugin marketplace add ${REPO_OWNER}/${REPO_NAME}"
    echo "  /plugin install claude-adk-skills"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET_IDE="$2"; shift 2 ;;
        --copy)
            LINK_METHOD="copy"; shift ;;
        --ref)
            GIT_REF="$2"; shift 2 ;;
        --install-dir)
            INSTALL_DIR="$2"; VENV_DIR="${INSTALL_DIR}/venv"; shift 2 ;;
        --skip-deps)
            SKIP_DEPS=true; shift ;;
        --force)
            FORCE=true; shift ;;
        --verbose)
            VERBOSE=true; shift ;;
        --help|-h)
            show_help; exit 0 ;;
        *)
            log_error "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

# ── Detect OS ───────────────────────────────────────
detect_os() {
    log_step "Detecting operating system..."
    case "$(uname -s)" in
        Darwin*) OS="macos"; log_info "Detected macOS" ;;
        Linux*)  OS="linux"; log_info "Detected Linux" ;;
        CYGWIN*|MINGW*|MSYS*)
            OS="windows"; log_warn "Windows detected — symlinks may not work, use --copy" ;;
        *) log_error "Unsupported OS: $(uname -s)"; exit 1 ;;
    esac
}

# ── Check dependencies ──────────────────────────────
check_dependencies() {
    log_step "Checking dependencies..."
    local missing_deps=()

    # Need a way to fetch the repo: git (preferred) OR curl/wget for the tarball.
    if command -v git &> /dev/null; then
        log_info "Found git: $(git --version)"
    elif command -v curl &> /dev/null || command -v wget &> /dev/null; then
        log_info "No git — will download tarball via curl/wget"
    else
        missing_deps+=("git or curl/wget")
    fi

    local python_cmd=""
    for cmd in python3.12 python3.11 python3; do
        if command -v "$cmd" &> /dev/null; then
            python_cmd="$cmd"; break
        fi
    done

    if [[ -z "$python_cmd" ]]; then
        missing_deps+=("python3.11+")
    else
        local ver=$($python_cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        local major=$(echo "$ver" | cut -d. -f1)
        local minor=$(echo "$ver" | cut -d. -f2)
        if [[ $major -lt 3 ]] || [[ $major -eq 3 && $minor -lt 11 ]]; then
            log_error "Python $MIN_PYTHON_VERSION+ required, found $ver"
            missing_deps+=("python3.11+")
        else
            PYTHON_CMD="$python_cmd"
            log_info "Found Python: $ver"
        fi
    fi

    if ! $PYTHON_CMD -m pip --version &> /dev/null 2>&1; then
        missing_deps+=("pip")
    else
        log_info "Found pip"
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing: ${missing_deps[*]}"
        echo "Install with:"
        [[ "$OS" == "macos" ]] && echo "  brew install ${missing_deps[*]}"
        [[ "$OS" == "linux" ]] && echo "  sudo apt-get install ${missing_deps[*]}"
        exit 1
    fi
    log_info "All dependencies satisfied"
}

# ── Fetch repo (public, no-auth) ────────────────────
# Tries a public HTTPS git clone first; falls back to a tarball download so the
# installer works on machines without git (e.g. `curl | bash`). No PAT/SSH.
REPO_HTTPS="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
REPO_TARBALL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${GIT_REF}.tar.gz"

fetch_via_tarball() {
    log_info "Downloading tarball (${GIT_REF})..."
    local downloader=""
    if command -v curl &> /dev/null; then
        downloader="curl -fsSL"
    elif command -v wget &> /dev/null; then
        downloader="wget -qO-"
    else
        log_error "Need git, curl, or wget to download the repo"; exit 1
    fi

    mkdir -p "$INSTALL_DIR"
    # GitHub tarballs nest everything under <repo>-<ref>/ — strip that level.
    $downloader "$REPO_TARBALL" | tar -xz -C "$INSTALL_DIR" --strip-components=1 || {
        log_error "Tarball download failed"; exit 1
    }
    log_info "Downloaded to $INSTALL_DIR"
}

fetch_repo() {
    log_step "Fetching repository (public, no auth)..."

    if [[ -d "$INSTALL_DIR" ]]; then
        if [[ "$FORCE" == true ]]; then
            log_warn "Removing existing installation..."
            rm -rf "$INSTALL_DIR"
        elif [[ -d "$INSTALL_DIR/.git" ]] && command -v git &> /dev/null; then
            log_info "Updating existing installation..."
            cd "$INSTALL_DIR"
            git pull --ff-only origin "$GIT_REF" && log_info "Updated successfully" && return 0
            log_warn "git pull failed — re-fetching fresh"
            cd - > /dev/null; rm -rf "$INSTALL_DIR"
        else
            log_info "Refreshing existing (non-git) installation..."
            rm -rf "$INSTALL_DIR"
        fi
    fi

    if command -v git &> /dev/null; then
        log_info "Cloning $REPO_HTTPS (ref: $GIT_REF)..."
        if git clone --depth 1 --branch "$GIT_REF" "$REPO_HTTPS" "$INSTALL_DIR" 2>/dev/null; then
            log_info "Repository cloned"
            return 0
        fi
        log_warn "git clone failed — falling back to tarball"
    else
        log_warn "git not found — using tarball download"
    fi
    fetch_via_tarball
}

# ── Python dependencies ─────────────────────────────
install_python_deps() {
    [[ "$SKIP_DEPS" == true ]] && { log_info "Skipping Python deps"; return 0; }
    log_step "Installing Python dependencies..."

    if [[ ! -d "$VENV_DIR" ]]; then
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip -q

    if [[ -f "$INSTALL_DIR/requirements.txt" ]]; then
        pip install -r "$INSTALL_DIR/requirements.txt"
    fi
    if [[ -f "$INSTALL_DIR/adk-python/requirements.txt" ]]; then
        pip install -r "$INSTALL_DIR/adk-python/requirements.txt"
    fi

    deactivate
    log_info "Python dependencies installed"
}

# ── IDE Detection ───────────────────────────────────
detect_ides() {
    log_step "Detecting installed IDEs..."
    DETECTED_IDES=()

    for ide in $ALL_IDES; do
        local cmd
        cmd=$(get_cli_cmd "$ide")
        if [[ -n "$cmd" ]] && command -v "$cmd" &> /dev/null; then
            DETECTED_IDES+=("$ide")
            log_info "Detected: $ide ($cmd)"
        fi
    done

    # Also check for config directories (some IDEs don't have CLI tools)
    for ide in $ALL_IDES; do
        local skills_dir
        skills_dir=$(get_skills_dir "$ide")
        local parent_dir
        parent_dir=$(dirname "$skills_dir")
        if [[ -d "$parent_dir" ]]; then
            if [[ ! " ${DETECTED_IDES[*]} " =~ " ${ide} " ]]; then
                DETECTED_IDES+=("$ide")
                log_info "Detected config dir: $ide ($parent_dir)"
            fi
        fi
    done

    if [[ ${#DETECTED_IDES[@]} -eq 0 ]]; then
        log_warn "No IDEs detected — defaulting to claude-code"
        DETECTED_IDES=("claude-code")
    fi
}

# ── Resolve target IDEs ─────────────────────────────
resolve_targets() {
    detect_ides

    case "$TARGET_IDE" in
        auto)
            TARGETS=("${DETECTED_IDES[@]}")
            log_info "Auto-detected targets: ${TARGETS[*]}" ;;
        all)
            TARGETS=($ALL_IDES)
            log_info "Installing for all supported IDEs: ${TARGETS[*]}" ;;
        *)
            local test_dir
            test_dir=$(get_skills_dir "$TARGET_IDE")
            if [[ -n "$test_dir" ]]; then
                TARGETS=("$TARGET_IDE")
                log_info "Target: $TARGET_IDE"
            else
                log_error "Unknown IDE: $TARGET_IDE"
                echo "Valid targets: $ALL_IDES"
                exit 1
            fi ;;
    esac
}

# ── Link skills into IDE ────────────────────────────
install_skills_for_ide() {
    local ide=$1
    local skills_target
    skills_target=$(get_skills_dir "$ide")

    log_step "Installing skills for $ide → $skills_target"
    mkdir -p "$skills_target"

    local skill_count=0
    for skill_dir in "$INSTALL_DIR/skills/"*/; do
        local skill_name
        skill_name=$(basename "$skill_dir")

        # Skip non-directories and non-SKILL.md entries
        [[ ! -f "$skill_dir/SKILL.md" ]] && continue

        local link_path="$skills_target/$skill_name"

        if [[ "$LINK_METHOD" == "symlink" ]]; then
            if [[ -L "$link_path" ]]; then
                [[ "$FORCE" == true ]] && rm "$link_path"
            fi
            ln -sf "$skill_dir" "$link_path" 2>/dev/null || {
                log_warn "Symlink failed for $skill_name — trying copy"
                cp -r "$skill_dir" "$link_path"
            }
        else
            cp -r "$skill_dir" "$link_path"
        fi
        ((skill_count++))
        [[ "$VERBOSE" == true ]] && log_info "  $skill_name"
    done

    log_info "Linked $skill_count skills for $ide"
}

# ── Configure environment ───────────────────────────
configure_env() {
    log_step "Configuring environment..."
    local env_file="$INSTALL_DIR/.env"
    local env_example="$INSTALL_DIR/.env.example"

    [[ -f "$env_file" ]] && { log_info "Env file exists"; return 0; }

    cat > "$env_example" << 'EOF'
# ADK Skills — Environment Configuration
# Copy to .env and fill in your values

# Required: Google AI / Gemini API
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CLOUD_PROJECT=your_project_id

# Optional: Pinecone (RAG features)
PINECONE_API_KEY=
PINECONE_INDEX_HOST=

# Optional: MCP Servers
BRAVE_API_KEY=
GITHUB_TOKEN=
EOF
    log_info "Created .env.example — copy to .env and add keys"
}

# ── Shell integration ───────────────────────────────
create_shell_integration() {
    log_step "Setting up shell integration..."
    local shell_rc=""

    case "$SHELL" in
        */zsh)  shell_rc="$HOME/.zshrc" ;;
        */bash) shell_rc="$HOME/.bashrc" ;;
        *)      log_warn "Unknown shell: $SHELL — skipping"; return 0 ;;
    esac

    grep -q "claude-adk-skills" "$shell_rc" 2>/dev/null && {
        log_info "Shell integration already configured"; return 0
    }

    cat >> "$shell_rc" << 'EOF'

# Claude-ADK-Skills
export PATH="$HOME/.claude-adk-skills/venv/bin:$PATH"
alias adk='python -m adk_bidi'
EOF
    log_info "Added to $shell_rc — run 'source $shell_rc' to activate"
}

# ── Verify ──────────────────────────────────────────
verify_installation() {
    log_step "Verifying..."
    local errors=0

    [[ ! -d "$INSTALL_DIR" ]] && { log_error "Install dir not found"; ((errors++)); }
    [[ ! -d "$INSTALL_DIR/skills" ]] && { log_error "Skills dir not found"; ((errors++)); }

    local skill_count=$(find "$INSTALL_DIR/skills" -name "SKILL.md" -maxdepth 2 | wc -l | tr -d ' ')
    log_info "Found $skill_count skills"

    for ide in "${TARGETS[@]}"; do
        local dir
        dir=$(get_skills_dir "$ide")
        local linked=$(find "$dir" -name "SKILL.md" -maxdepth 2 2>/dev/null | wc -l | tr -d ' ')
        log_info "  $ide: $linked skills linked"
    done

    [[ $errors -gt 0 ]] && { log_error "Verification failed: $errors errors"; return 1; }
    log_info "Verification passed"
}

# ── Done ────────────────────────────────────────────
print_completion() {
    echo ""
    echo -e "${GREEN}======================================"
    echo "  Installation Complete!"
    echo "======================================${NC}"
    echo ""
    echo "Install dir:  $INSTALL_DIR"
    for ide in "${TARGETS[@]}"; do
        echo "  $ide → $(get_skills_dir "$ide")"
    done
    echo ""
    echo "Next steps:"
    echo "  1. Configure API keys: cp $INSTALL_DIR/.env.example $INSTALL_DIR/.env"
    echo "  2. Restart terminal or: source ~/.zshrc"
    echo "  3. Start using skills in your IDE — they auto-discover"
    echo ""
}

# ── Main ────────────────────────────────────────────
main() {
    print_banner
    detect_os
    check_dependencies
    fetch_repo
    install_python_deps
    resolve_targets

    for ide in "${TARGETS[@]}"; do
        install_skills_for_ide "$ide"
    done

    configure_env
    create_shell_integration
    verify_installation
    print_completion
}

main
