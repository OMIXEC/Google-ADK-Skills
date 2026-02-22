#!/bin/bash

# Claude ADK Skills Plugin Installer
# Downloads and installs the unified ADK Claude plugin

set -e

echo "🚀 Claude ADK Skills Plugin Installer"
echo "======================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is required but not installed. Please install git first."
    exit 1
fi

# Get installation directory
INSTALL_DIR="${1:-.}"
PLUGIN_NAME="claude-adk-skills"
PLUGIN_PATH="$INSTALL_DIR/$PLUGIN_NAME"

# Clone or download repository
if [ -d "$PLUGIN_PATH" ]; then
    echo "📂 Plugin directory already exists at: $PLUGIN_PATH"
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PLUGIN_PATH"
        git pull
    fi
else
    echo "📥 Downloading Claude ADK Skills plugin..."
    git clone https://github.com/OMIXEC/Claude-ADK-Skills.git "$PLUGIN_PATH"
    cd "$PLUGIN_PATH"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "📍 Plugin location: $PLUGIN_PATH"
echo ""
echo "🎯 Next steps:"
echo "  1. Open Claude Code"
echo "  2. Run: cc --plugin-dir $PLUGIN_PATH"
echo "  3. Or add to Claude Code plugins directory"
echo ""
echo "📖 For quick start:"
echo "  - Ask: 'What can I build with ADK?'"
echo "  - Try: /adk:init my-project"
echo "  - Check: /adk:status"
echo ""
