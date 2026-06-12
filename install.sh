#!/bin/bash
#
# Google-ADK-Skills Installation Script
# IDE-agnostic: supports Codex, OpenCode, Claude, Cline, Cursor, Gemini CLI,
# Windsurf, and any custom skills directory.
#
# Usage:
#   bash install.sh                           # auto-detect IDE
#   bash install.sh --target claude            # specific IDE
#   bash install.sh --target all               # all detected IDEs
#   bash install.sh --target gemini-cli --copy # copy instead of symlink
#
# Public, no-auth: when run from a clone it installs that local checkout; when
# streamed with curl/npx it clones over HTTPS and falls back to a tarball.

set -e

# ── Colors ──────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ── Configuration ───────────────────────────────────
REPO_OWNER="OMIXEC"
REPO_NAME="Google-ADK-Skills"
INSTALL_DIR="${HOME}/.google-adk-skills"
VENV_DIR="${INSTALL_DIR}/venv"
INSTALL_DIR_SET=false
MIN_PYTHON_VERSION="3.11"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR=""

# IDE skills directories (bash 3.2 compatible — use functions, not associative arrays)

ALL_IDES="${GOOGLE_ADK_TARGETS:-codex opencode claude cline cursor gemini-cli windsurf}"
SKILLS_FILTER="all"
CUSTOM_SKILLS_DIR=""
INSTALL_SCOPE="user"

get_skills_dir() {
    local target
    target=$(normalize_target "$1")

    if [[ "$target" == "custom" ]]; then
        echo "$CUSTOM_SKILLS_DIR"
        return 0
    fi

    if [[ "$INSTALL_SCOPE" == "global" ]]; then
        case "$target" in
            codex) echo "/usr/local/share/codex/skills" ;;
            opencode) echo "/usr/local/share/opencode/skills" ;;
            claude) echo "/usr/local/share/claude/skills" ;;
            cline) echo "/usr/local/share/cline/skills" ;;
            cursor) echo "/usr/local/share/cursor/skills" ;;
            gemini-cli) echo "/usr/local/share/gemini/skills" ;;
            windsurf) echo "/usr/local/share/windsurf/skills" ;;
            *) echo "" ;;
        esac
        return 0
    fi

    case "$target" in
        claude) echo "${HOME}/.claude/skills" ;;
        gemini-cli) echo "${HOME}/.gemini/skills" ;;
        opencode) echo "${HOME}/.opencode/skills" ;;
        cursor) echo "${HOME}/.cursor/skills" ;;
        windsurf) echo "${HOME}/.windsurf/skills" ;;
        codex) echo "${HOME}/.codex/skills" ;;
        cline) echo "${HOME}/.cline/skills" ;;
        *) echo "" ;;
    esac
}

get_cli_cmd() {
    case "$(normalize_target "$1")" in
        claude) echo "claude" ;;
        gemini-cli) echo "gemini" ;;
        opencode) echo "opencode" ;;
        cursor) echo "cursor" ;;
        codex) echo "codex" ;;
        cline) echo "cline" ;;
        *) echo "" ;;
    esac
}

# ── Parse arguments ─────────────────────────────────
TARGET_IDE="auto"
LINK_METHOD="symlink"
VERBOSE=false
SKIP_DEPS=false
FORCE=false
GIT_REF="main"
WITH_EVALS=false
WITH_RUNTIME=false
SHELL_INTEGRATION=false
INTERACTIVE=false

print_banner() {
    echo -e "${BLUE}"
    echo "======================================"
    echo "  Google-ADK-Skills Installer"
    echo "  ADK skills for AI coding tools"
    echo "======================================"
    echo -e "${NC}"
}

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "${BLUE}[STEP]${NC} $1"; }

normalize_target() {
    case "$1" in
        claude-code) echo "claude" ;;
        *) echo "$1" ;;
    esac
}

is_known_target() {
    local target
    target=$(normalize_target "$1")
    [[ "$target" == "auto" || "$target" == "all" || "$target" == "custom" ]] && return 0
    [[ " $ALL_IDES " =~ " $target " ]]
}

default_install_dir() {
    case "$1" in
        global) echo "/usr/local/share/google-adk-skills" ;;
        *) echo "${HOME}/.google-adk-skills" ;;
    esac
}

skill_selected() {
    local skill_name="$1"
    [[ "$SKILLS_FILTER" == "all" ]] && return 0

    local old_ifs="$IFS"
    IFS=','
    for selected in $SKILLS_FILTER; do
        selected=$(echo "$selected" | tr -d '[:space:]')
        if [[ "$selected" == "$skill_name" ]]; then
            IFS="$old_ifs"
            return 0
        fi
    done
    IFS="$old_ifs"
    return 1
}

list_available_skills() {
    local source="${INSTALL_DIR}/skills"
    [[ -d "$SCRIPT_DIR/skills" ]] && source="${SCRIPT_DIR}/skills"
    find "$source" -maxdepth 2 -name "SKILL.md" -print 2>/dev/null | \
        sed 's#.*/skills/##; s#/SKILL.md##' | sort
}

run_interactive_setup() {
    if [[ ! -t 0 ]]; then
        log_warn "Interactive mode needs a terminal. Continuing with flags/defaults."
        return 0
    fi

    echo ""
    echo "Interactive install"
    echo "Targets: codex, opencode, claude, cline, cursor, gemini-cli, windsurf, all, auto, custom"
    printf "Target [%s]: " "$TARGET_IDE"
    read answer
    [[ -n "$answer" ]] && TARGET_IDE="$answer"
    TARGET_IDE=$(normalize_target "$TARGET_IDE")

    printf "Install scope user or global [%s]: " "$INSTALL_SCOPE"
    read answer
    [[ -n "$answer" ]] && INSTALL_SCOPE="$answer"

    if [[ "$TARGET_IDE" == "custom" ]]; then
        printf "Custom skills directory: "
        read answer
        CUSTOM_SKILLS_DIR="$answer"
    fi

    printf "Use copy instead of symlink? [y/N]: "
    read answer
    case "$answer" in
        y|Y|yes|YES) LINK_METHOD="copy" ;;
    esac

    printf "Replace existing copied skill directories? [y/N]: "
    read answer
    case "$answer" in
        y|Y|yes|YES) FORCE=true ;;
    esac

    printf "Install Python runtime dependencies? [y/N]: "
    read answer
    case "$answer" in
        y|Y|yes|YES) WITH_RUNTIME=true; SKIP_DEPS=false ;;
    esac

    printf "Keep eval/test assets? [y/N]: "
    read answer
    case "$answer" in
        y|Y|yes|YES) WITH_EVALS=true ;;
    esac

    printf "Add shell integration for runtime helpers? [y/N]: "
    read answer
    case "$answer" in
        y|Y|yes|YES) SHELL_INTEGRATION=true ;;
    esac

    echo ""
    echo "Skills available:"
    list_available_skills | sed 's/^/  - /'
    echo ""
    printf "Skills to install [all or comma-separated names]: "
    read answer
    [[ -n "$answer" ]] && SKILLS_FILTER="$answer"

    if [[ "$INSTALL_DIR_SET" != true ]]; then
        INSTALL_DIR=$(default_install_dir "$INSTALL_SCOPE")
        VENV_DIR="${INSTALL_DIR}/venv"
    fi
}

show_help() {
    echo "Usage: install.sh [OPTIONS]"
    echo ""
    echo "Public, no-auth installer. Clones over HTTPS; falls back to a tarball"
    echo "download when git is missing or the clone fails."
    echo ""
    echo "IDE Target:"
    echo "  --target IDE       Install for specific target"
    echo "                     Values: codex, opencode, claude, cline, cursor,"
    echo "                             gemini-cli, windsurf, all, auto (default)"
    echo "  --copy             Copy files instead of symlinking (default: symlink)"
    echo ""
    echo "Other:"
    echo "  --install-dir DIR  Custom install directory (default: ~/.google-adk-skills)"
    echo "  --skills-dir DIR   Install into a custom skills directory"
    echo "  --scope SCOPE      user or global install scope (default: user)"
    echo "  --ref REF          Git branch/tag to install (default: main)"
    echo "  --skills LIST      Comma-separated skills to install, or all (default: all)"
    echo "  --interactive      Prompt for target, method, runtime, evals, and skills"
    echo "  --with-evals       Keep eval/test assets in the install checkout"
    echo "  --with-runtime     Create a Python venv and install runtime dependencies"
    echo "  --shell-integration Add adk alias/PATH entry to your shell rc file"
    echo "  --skip-deps        Compatibility alias for the default no-runtime install"
    echo "  --force            Force reinstall"
    echo "  --verbose          Verbose output"
    echo "  --help             Show this help"
    echo ""
    echo "Examples:"
    echo "  npx skills add ${REPO_OWNER}/${REPO_NAME}       # Canonical skills.sh install"
    echo "  bash install.sh                              # Auto-detect IDE"
    echo "  bash install.sh --interactive                 # Guided install"
    echo "  bash install.sh --target claude               # Claude only"
    echo "  bash install.sh --target all --copy           # All IDEs, copy mode"
    echo "  curl -fsSL https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/main/install.sh | bash"
    echo ""
    echo "Alternative — install as a Claude Code plugin (no clone needed):"
    echo "  /plugin marketplace add ${REPO_OWNER}/${REPO_NAME}"
    echo "  /plugin install google-adk-skills"
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
            INSTALL_DIR="$2"; VENV_DIR="${INSTALL_DIR}/venv"; INSTALL_DIR_SET=true; shift 2 ;;
        --skills-dir)
            CUSTOM_SKILLS_DIR="$2"; TARGET_IDE="custom"; shift 2 ;;
        --scope)
            INSTALL_SCOPE="$2"; shift 2 ;;
        --skills)
            SKILLS_FILTER="$2"; shift 2 ;;
        --interactive|-i)
            INTERACTIVE=true; shift ;;
        --skip-deps)
            SKIP_DEPS=true; shift ;;
        --with-evals)
            WITH_EVALS=true; shift ;;
        --with-runtime)
            WITH_RUNTIME=true; SKIP_DEPS=false; shift ;;
        --shell-integration)
            SHELL_INTEGRATION=true; shift ;;
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

if ! is_known_target "$TARGET_IDE"; then
    log_error "Unknown target: $TARGET_IDE"
    echo "Valid targets: codex, opencode, claude, cline, cursor, gemini-cli, windsurf, all, auto"
    exit 1
fi

if [[ "$INSTALL_SCOPE" != "user" && "$INSTALL_SCOPE" != "global" ]]; then
    log_error "Unknown scope: $INSTALL_SCOPE"
    echo "Valid scopes: user, global"
    exit 1
fi

if [[ "$(normalize_target "$TARGET_IDE")" == "custom" && -z "$CUSTOM_SKILLS_DIR" && "$INTERACTIVE" != true ]]; then
    log_error "--target custom requires --skills-dir <path>"
    exit 1
fi

if [[ "$INSTALL_DIR_SET" != true ]]; then
    INSTALL_DIR=$(default_install_dir "$INSTALL_SCOPE")
    VENV_DIR="${INSTALL_DIR}/venv"
fi

validate_config() {
    if ! is_known_target "$TARGET_IDE"; then
        log_error "Unknown target: $TARGET_IDE"
        echo "Valid targets: codex, opencode, claude, cline, cursor, gemini-cli, windsurf, all, auto, custom"
        exit 1
    fi

    if [[ "$INSTALL_SCOPE" != "user" && "$INSTALL_SCOPE" != "global" ]]; then
        log_error "Unknown scope: $INSTALL_SCOPE"
        echo "Valid scopes: user, global"
        exit 1
    fi

    if [[ "$(normalize_target "$TARGET_IDE")" == "custom" && -z "$CUSTOM_SKILLS_DIR" ]]; then
        log_error "Custom target requires --skills-dir <path> or an interactive custom skills directory"
        exit 1
    fi
}

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

nearest_existing_parent() {
    local path="$1"
    while [[ ! -e "$path" && "$path" != "/" ]]; do
        path=$(dirname "$path")
    done
    echo "$path"
}

check_scope_permissions() {
    [[ "$INSTALL_SCOPE" != "global" ]] && return 0

    local parent
    parent=$(nearest_existing_parent "$INSTALL_DIR")
    if [[ ! -w "$parent" ]]; then
        log_error "Global install root is not writable: $parent"
        echo "Re-run with sudo/admin permissions, or use --scope user."
        exit 1
    fi

    local target dir target_parent targets_to_check
    if [[ ${#TARGETS[@]} -gt 0 ]]; then
        targets_to_check="${TARGETS[*]}"
    elif [[ "$(normalize_target "$TARGET_IDE")" == "all" ]]; then
        targets_to_check="$ALL_IDES"
    elif [[ "$(normalize_target "$TARGET_IDE")" != "auto" ]]; then
        targets_to_check="$(normalize_target "$TARGET_IDE")"
    else
        targets_to_check=""
    fi

    for target in $targets_to_check; do
        [[ "$target" == "custom" && -z "$CUSTOM_SKILLS_DIR" ]] && continue
        dir=$(get_skills_dir "$target")
        [[ -z "$dir" ]] && continue
        target_parent=$(nearest_existing_parent "$dir")
        if [[ ! -w "$target_parent" ]]; then
            log_error "Global skills directory parent is not writable: $target_parent"
            echo "Re-run with sudo/admin permissions, or use --scope user."
            exit 1
        fi
    done
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

    if [[ "$WITH_RUNTIME" != true ]]; then
        log_info "Runtime dependency install disabled (use --with-runtime to enable)"
        log_info "All required installer dependencies satisfied"
        return 0
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

    if [[ -z "$PYTHON_CMD" ]] || ! "$PYTHON_CMD" -m pip --version &> /dev/null 2>&1; then
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

copy_local_checkout() {
    log_info "Installing from local checkout: $SOURCE_DIR"
    if [[ -d "$INSTALL_DIR" ]]; then
        if [[ "$FORCE" == true ]]; then
            rm -rf "$INSTALL_DIR"
        else
            log_info "Refreshing existing install directory"
            rm -rf "$INSTALL_DIR"
        fi
    fi
    mkdir -p "$INSTALL_DIR"

    if command -v rsync &> /dev/null; then
        rsync -a \
            --exclude '.git/' \
            --exclude 'venv/' \
            --exclude '.venv/' \
            "$SOURCE_DIR/" "$INSTALL_DIR/"
    else
        (cd "$SOURCE_DIR" && tar --exclude='.git' --exclude='venv' --exclude='.venv' -cf - .) | \
            (cd "$INSTALL_DIR" && tar -xf -)
    fi
    log_info "Copied checkout to $INSTALL_DIR"
}

prune_optional_assets() {
    if [[ "$WITH_EVALS" == true ]]; then
        log_info "Keeping eval/test assets (--with-evals)"
        return 0
    fi

    rm -rf "$INSTALL_DIR/tests"
    log_info "Skipped eval/test assets (use --with-evals to keep tests/)"
}

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

    if [[ -d "$SCRIPT_DIR/skills" ]] && [[ -f "$SCRIPT_DIR/README.md" ]]; then
        SOURCE_DIR="$SCRIPT_DIR"
        copy_local_checkout
        return 0
    fi

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
    [[ "$WITH_RUNTIME" != true || "$SKIP_DEPS" == true ]] && { log_info "Skipping Python runtime deps"; return 0; }
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
        log_warn "No IDEs detected — defaulting to codex"
        DETECTED_IDES=("codex")
    fi
}

# ── Resolve target IDEs ─────────────────────────────
resolve_targets() {
    detect_ides
    TARGET_IDE=$(normalize_target "$TARGET_IDE")

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
        skill_selected "$skill_name" || continue

        local link_path="$skills_target/$skill_name"

        if [[ "$LINK_METHOD" == "symlink" ]]; then
            if [[ -e "$link_path" || -L "$link_path" ]]; then
                if [[ -L "$link_path" ]]; then
                    rm "$link_path"
                elif [[ "$FORCE" == true ]]; then
                    rm -rf "$link_path"
                else
                    log_warn "Skipping existing non-symlink skill: $link_path (use --force to replace)"
                    continue
                fi
            fi
            ln -s "$skill_dir" "$link_path" 2>/dev/null || {
                log_warn "Symlink failed for $skill_name — trying copy"
                rm -rf "$link_path"
                cp -r "$skill_dir" "$link_path"
            }
        else
            if [[ -e "$link_path" || -L "$link_path" ]]; then
                if [[ "$FORCE" == true ]]; then
                    rm -rf "$link_path"
                else
                    log_warn "Skipping existing skill: $link_path (use --force to replace)"
                    continue
                fi
            fi
            cp -r "$skill_dir" "$link_path"
        fi
        ((skill_count+=1))
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
    [[ "$SHELL_INTEGRATION" != true ]] && { log_info "Skipping shell integration (use --shell-integration to enable)"; return 0; }
    log_step "Setting up shell integration..."
    local shell_rc=""

    case "$SHELL" in
        */zsh)  shell_rc="$HOME/.zshrc" ;;
        */bash) shell_rc="$HOME/.bashrc" ;;
        *)      log_warn "Unknown shell: $SHELL — skipping"; return 0 ;;
    esac

    grep -q "google-adk-skills" "$shell_rc" 2>/dev/null && {
        log_info "Shell integration already configured"; return 0
    }

    cat >> "$shell_rc" << EOF

# Google-ADK-Skills
export PATH="$INSTALL_DIR/venv/bin:\$PATH"
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
    if [[ "$SHELL_INTEGRATION" == true ]]; then
        echo "  2. Restart terminal or source your shell rc file"
        echo "  3. Start using skills in your IDE — they auto-discover"
    else
        echo "  2. Restart your IDE so it reloads installed skills"
        echo "  3. Optional runtime setup: rerun with --with-runtime --shell-integration"
    fi
    echo ""
}

# ── Main ────────────────────────────────────────────
main() {
    print_banner
    [[ "$INTERACTIVE" == true ]] && run_interactive_setup
    validate_config
    detect_os
    check_dependencies
    check_scope_permissions
    fetch_repo
    prune_optional_assets
    install_python_deps
    resolve_targets
    check_scope_permissions

    for ide in "${TARGETS[@]}"; do
        install_skills_for_ide "$ide"
    done

    configure_env
    create_shell_integration
    verify_installation
    print_completion
}

main
