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
