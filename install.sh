#!/bin/bash
#
# Claude-ADK-Skills Installation Script
#
# Supports:
#   - GitHub Personal Access Token (PAT) authentication
#   - SSH key authentication
#   - Interactive mode
#
# Usage:
#   # With PAT
#   curl -sSL https://raw.githubusercontent.com/OMIXEC/Claude-ADK-Skills/main/install.sh | bash -s -- --token YOUR_PAT
#
#   # With SSH
#   curl -sSL https://raw.githubusercontent.com/OMIXEC/Claude-ADK-Skills/main/install.sh | bash -s -- --ssh
#
#   # Interactive
#   curl -sSL https://raw.githubusercontent.com/OMIXEC/Claude-ADK-Skills/main/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="OMIXEC"
REPO_NAME="Claude-ADK-Skills"
INSTALL_DIR="${HOME}/.claude-adk-skills"
VENV_DIR="${INSTALL_DIR}/venv"
SKILLS_DIR="${HOME}/.claude/skills"
MIN_PYTHON_VERSION="3.11"

# Parse arguments
AUTH_METHOD="interactive"
GITHUB_TOKEN=""
VERBOSE=false
SKIP_DEPS=false
FORCE=false

print_banner() {
    echo -e "${BLUE}"
    echo "======================================"
    echo "  Claude-ADK-Skills Installer"
    echo "======================================"
    echo -e "${NC}"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

show_help() {
    echo "Usage: install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --token TOKEN    Use GitHub Personal Access Token for authentication"
    echo "  --ssh            Use SSH key authentication (git@github.com)"
    echo "  --install-dir    Custom installation directory (default: ~/.claude-adk-skills)"
    echo "  --skip-deps      Skip Python dependency installation"
    echo "  --force          Force reinstall even if already installed"
    echo "  --verbose        Enable verbose output"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Install with PAT (recommended for CI/CD)"
    echo "  curl -sSL .../install.sh | bash -s -- --token ghp_xxxx"
    echo ""
    echo "  # Install with SSH (recommended for developers)"
    echo "  curl -sSL .../install.sh | bash -s -- --ssh"
    echo ""
    echo "  # Interactive installation"
    echo "  curl -sSL .../install.sh | bash"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --token)
            GITHUB_TOKEN="$2"
            AUTH_METHOD="pat"
            shift 2
            ;;
        --ssh)
            AUTH_METHOD="ssh"
            shift
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            VENV_DIR="${INSTALL_DIR}/venv"
            shift 2
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Detect OS
detect_os() {
    log_step "Detecting operating system..."

    case "$(uname -s)" in
        Darwin*)
            OS="macos"
            log_info "Detected macOS"
            ;;
        Linux*)
            OS="linux"
            log_info "Detected Linux"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            OS="windows"
            log_warn "Windows detected. Some features may not work correctly."
            ;;
        *)
            log_error "Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac
}

# Check for required dependencies
check_dependencies() {
    log_step "Checking dependencies..."

    local missing_deps=()

    # Check git
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    else
        log_info "Found git: $(git --version)"
    fi

    # Check Python
    local python_cmd=""
    for cmd in python3.12 python3.11 python3; do
        if command -v "$cmd" &> /dev/null; then
            python_cmd="$cmd"
            break
        fi
    done

    if [[ -z "$python_cmd" ]]; then
        missing_deps+=("python3.11+")
    else
        local python_version=$($python_cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        local required_major=3
        local required_minor=11
        local actual_major=$(echo "$python_version" | cut -d. -f1)
        local actual_minor=$(echo "$python_version" | cut -d. -f2)

        if [[ $actual_major -lt $required_major ]] || [[ $actual_major -eq $required_major && $actual_minor -lt $required_minor ]]; then
            log_error "Python $MIN_PYTHON_VERSION+ required, found $python_version"
            missing_deps+=("python3.11+")
        else
            PYTHON_CMD="$python_cmd"
            log_info "Found Python: $python_version"
        fi
    fi

    # Check pip
    if ! $PYTHON_CMD -m pip --version &> /dev/null 2>&1; then
        missing_deps+=("pip")
    else
        log_info "Found pip"
    fi

    # Check curl (usually needed for the script itself)
    if ! command -v curl &> /dev/null; then
        log_warn "curl not found (not required if running script directly)"
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install the missing dependencies:"

        if [[ "$OS" == "macos" ]]; then
            echo "  brew install ${missing_deps[*]}"
        elif [[ "$OS" == "linux" ]]; then
            echo "  sudo apt-get install ${missing_deps[*]}  # Debian/Ubuntu"
            echo "  sudo yum install ${missing_deps[*]}      # CentOS/RHEL"
        fi
        exit 1
    fi

    log_info "All dependencies satisfied"
}

# Setup authentication
setup_auth() {
    log_step "Setting up authentication..."

    if [[ "$AUTH_METHOD" == "interactive" ]]; then
        echo ""
        echo "Choose authentication method:"
        echo "  1) GitHub Personal Access Token (PAT) - Recommended for most users"
        echo "  2) SSH Key - Recommended if you have SSH configured"
        echo ""
        read -p "Enter choice [1/2]: " auth_choice

        case $auth_choice in
            1)
                AUTH_METHOD="pat"
                read -sp "Enter your GitHub Personal Access Token: " GITHUB_TOKEN
                echo ""
                ;;
            2)
                AUTH_METHOD="ssh"
                ;;
            *)
                log_error "Invalid choice"
                exit 1
                ;;
        esac
    fi

    # Validate authentication
    if [[ "$AUTH_METHOD" == "pat" ]]; then
        if [[ -z "$GITHUB_TOKEN" ]]; then
            log_error "GitHub token is required for PAT authentication"
            exit 1
        fi
        REPO_URL="https://${GITHUB_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"
        log_info "Using PAT authentication"
    else
        # Check SSH key exists
        if [[ ! -f "$HOME/.ssh/id_rsa" ]] && [[ ! -f "$HOME/.ssh/id_ed25519" ]]; then
            log_warn "No SSH key found. Make sure SSH is configured for GitHub."
        fi
        REPO_URL="git@github.com:${REPO_OWNER}/${REPO_NAME}.git"
        log_info "Using SSH authentication"
    fi
}

# Clone or update repository
clone_repo() {
    log_step "Setting up repository..."

    if [[ -d "$INSTALL_DIR" ]]; then
        if [[ "$FORCE" == true ]]; then
            log_warn "Removing existing installation..."
            rm -rf "$INSTALL_DIR"
        else
            log_info "Installation directory exists. Pulling latest changes..."
            cd "$INSTALL_DIR"

            # Update remote URL if auth method changed
            git remote set-url origin "$REPO_URL" 2>/dev/null || true

            if git pull origin main; then
                log_info "Repository updated successfully"
                return 0
            else
                log_error "Failed to update repository"
                exit 1
            fi
        fi
    fi

    log_info "Cloning repository to $INSTALL_DIR..."

    if git clone "$REPO_URL" "$INSTALL_DIR"; then
        log_info "Repository cloned successfully"
    else
        log_error "Failed to clone repository. Check your authentication."
        if [[ "$AUTH_METHOD" == "pat" ]]; then
            log_error "Make sure your PAT has 'repo' scope for private repositories."
        else
            log_error "Make sure your SSH key is added to GitHub."
        fi
        exit 1
    fi
}

# Install Python dependencies
install_python_deps() {
    if [[ "$SKIP_DEPS" == true ]]; then
        log_info "Skipping Python dependency installation"
        return 0
    fi

    log_step "Installing Python dependencies..."

    # Create virtual environment
    if [[ ! -d "$VENV_DIR" ]]; then
        log_info "Creating virtual environment..."
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi

    # Activate venv and install deps
    source "$VENV_DIR/bin/activate"

    log_info "Upgrading pip..."
    pip install --upgrade pip

    # Install from requirements.txt if exists
    if [[ -f "$INSTALL_DIR/requirements.txt" ]]; then
        log_info "Installing from requirements.txt..."
        pip install -r "$INSTALL_DIR/requirements.txt"
    else
        # Install core dependencies
        log_info "Installing core dependencies..."
        pip install \
            "google-adk>=1.0.0" \
            "pinecone>=5.0.0" \
            "langgraph>=0.2.0" \
            "langchain-core>=0.3.0" \
            "vertexai>=1.0.0" \
            "fastapi>=0.100.0" \
            "uvicorn>=0.20.0" \
            "websockets>=12.0" \
            "pydantic>=2.0.0" \
            "pyyaml>=6.0"
    fi

    # Install the adk_bidi package in editable mode
    if [[ -f "$INSTALL_DIR/setup.py" ]] || [[ -f "$INSTALL_DIR/pyproject.toml" ]]; then
        log_info "Installing adk_bidi package..."
        pip install -e "$INSTALL_DIR"
    fi

    deactivate
    log_info "Python dependencies installed"
}

# Setup Claude Code plugin
setup_claude_plugin() {
    log_step "Setting up Claude Code integration..."

    # Create skills directory
    mkdir -p "$SKILLS_DIR"

    # Symlink skill files
    if [[ -d "$INSTALL_DIR/skills" ]]; then
        log_info "Symlinking skills to $SKILLS_DIR..."
        for skill in "$INSTALL_DIR/skills/"*.md; do
            if [[ -f "$skill" ]]; then
                skill_name=$(basename "$skill")
                ln -sf "$skill" "$SKILLS_DIR/$skill_name"
                log_info "  Linked: $skill_name"
            fi
        done
    fi

    # Try to register with Claude Code if available
    if command -v claude &> /dev/null; then
        log_info "Attempting to register with Claude Code..."
        if claude plugins add "$INSTALL_DIR" --local 2>/dev/null; then
            log_info "Registered with Claude Code"
        else
            log_warn "Could not auto-register. Add manually with: claude plugins add $INSTALL_DIR --local"
        fi
    else
        log_warn "Claude Code CLI not found. Skills are symlinked to $SKILLS_DIR"
    fi
}

# Configure environment
configure_env() {
    log_step "Configuring environment..."

    local env_file="$INSTALL_DIR/.env"
    local env_example="$INSTALL_DIR/.env.example"

    if [[ -f "$env_file" ]]; then
        log_info "Environment file already exists"
        return 0
    fi

    # Create .env.example template
    cat > "$env_example" << 'EOF'
# Claude-ADK-Skills Environment Configuration
# Copy this file to .env and fill in your values

# Required: Google Cloud / Gemini API
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CLOUD_PROJECT=your_project_id

# Optional: Pinecone (for RAG features)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_HOST=your_index_host

# Optional: MCP Servers
BRAVE_API_KEY=your_brave_api_key
GITHUB_TOKEN=your_github_token
NOTION_TOKEN=your_notion_token
SLACK_BOT_TOKEN=your_slack_token

# Optional: Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
EOF

    log_info "Created .env.example template"
    log_info "Copy to .env and add your API keys: cp $env_example $env_file"
}

# Create shell integration
create_shell_integration() {
    log_step "Setting up shell integration..."

    local shell_rc=""
    case "$SHELL" in
        */zsh)
            shell_rc="$HOME/.zshrc"
            ;;
        */bash)
            shell_rc="$HOME/.bashrc"
            ;;
        *)
            log_warn "Unknown shell: $SHELL. Skipping shell integration."
            return 0
            ;;
    esac

    # Check if already configured
    if grep -q "claude-adk-skills" "$shell_rc" 2>/dev/null; then
        log_info "Shell integration already configured"
        return 0
    fi

    # Add to shell rc
    cat >> "$shell_rc" << EOF

# Claude-ADK-Skills
export PATH="\$HOME/.claude-adk-skills/venv/bin:\$PATH"
alias adk='python -m adk_bidi'
alias adk-voice='python -m adk_bidi --mode voice'
alias adk-multimodal='python -m adk_bidi --mode multimodal'
EOF

    log_info "Added to $shell_rc"
    log_info "Run 'source $shell_rc' or restart your terminal"
}

# Verify installation
verify_installation() {
    log_step "Verifying installation..."

    local errors=0

    # Check installation directory
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_error "Installation directory not found"
        ((errors++))
    fi

    # Check skills
    if [[ ! -d "$INSTALL_DIR/skills" ]]; then
        log_error "Skills directory not found"
        ((errors++))
    else
        local skill_count=$(ls -1 "$INSTALL_DIR/skills/"*.md 2>/dev/null | wc -l)
        log_info "Found $skill_count skill files"
    fi

    # Check adk_bidi module
    if [[ ! -d "$INSTALL_DIR/adk_bidi" ]]; then
        log_error "adk_bidi module not found"
        ((errors++))
    fi

    # Check Python import
    if [[ "$SKIP_DEPS" != true ]]; then
        source "$VENV_DIR/bin/activate"
        if $PYTHON_CMD -c "from adk_bidi import BidiAgent; print('OK')" 2>/dev/null; then
            log_info "Python module imports successfully"
        else
            log_warn "Python module import failed (may need dependencies)"
        fi
        deactivate
    fi

    # Check skills symlinks
    if [[ -d "$SKILLS_DIR" ]]; then
        local linked_count=$(ls -1 "$SKILLS_DIR/"*.md 2>/dev/null | wc -l)
        log_info "Found $linked_count skills linked in Claude Code"
    fi

    if [[ $errors -gt 0 ]]; then
        log_error "Verification completed with $errors error(s)"
        return 1
    fi

    log_info "Verification completed successfully"
    return 0
}

# Print completion message
print_completion() {
    echo ""
    echo -e "${GREEN}======================================"
    echo "  Installation Complete!"
    echo "======================================${NC}"
    echo ""
    echo "Installation directory: $INSTALL_DIR"
    echo "Skills directory: $SKILLS_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Configure your API keys:"
    echo "     cp $INSTALL_DIR/.env.example $INSTALL_DIR/.env"
    echo "     # Edit .env with your API keys"
    echo ""
    echo "  2. Restart your terminal or run:"
    echo "     source ~/.zshrc  # or ~/.bashrc"
    echo ""
    echo "  3. Start using Claude-ADK-Skills:"
    echo "     # In Claude Code"
    echo "     /adk-adaptive-agent-generator Build a voice assistant"
    echo ""
    echo "     # Standalone orchestrator"
    echo "     adk --mode voice"
    echo "     adk --config root_agent.yaml"
    echo ""
    echo "Documentation: https://github.com/${REPO_OWNER}/${REPO_NAME}"
    echo ""
}

# Main installation flow
main() {
    print_banner
    detect_os
    check_dependencies
    setup_auth
    clone_repo
    install_python_deps
    setup_claude_plugin
    configure_env
    create_shell_integration
    verify_installation
    print_completion
}

# Run main
main
