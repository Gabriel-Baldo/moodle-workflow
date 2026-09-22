#!/usr/bin/env bash
# Atalho legado: setup da UTFPR (padrão). Para outro Moodle, use setup-moodle.sh --url ...
set -e
exec bash "$(cd "$(dirname "$0")" && pwd)/setup-moodle.sh" --url https://moodle.utfpr.edu.br
