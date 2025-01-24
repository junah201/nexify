#!/usr/bin/env bash
set -x

ruff check nexify scripts --fix
ruff format nexify scripts