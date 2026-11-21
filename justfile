# Orrery tasks. Run `just` to list them.
set shell := ["bash", "-euo", "pipefail", "-c"]
export PATH := env_var("HOME") + "/.local/bin:" + env_var("PATH")

# List the tasks
default:
    @just --list

# Install and check every pinned tool (safe to repeat)
setup:
    tools/setup/setup.sh

# Run the first-run checks only
check-env:
    tools/setup/check.sh

# Open Blender 5.2 with the MCP bridge on localhost:9876 (a window on the desktop)
blender *args:
    blender-5.2 --online-mode {{args}}

# Blender with the MCP bridge in a hidden gamescope display; run it in the background
blender-agent:
    gamescope --backend headless -W 1920 -H 1080 -- blender-5.2 --online-mode
