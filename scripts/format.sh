#!/usr/bin/env bash
set -x

ruff check nexify scripts tests --fix
ruff format nexify scripts tests