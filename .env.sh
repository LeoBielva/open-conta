#!/bin/bash
# Local env loader for this project (not global)
export PATH="/opt/homebrew/bin:$HOME/.pyenv/shims:$PATH"
[ -d ".venv" ] && source .venv/bin/activate
