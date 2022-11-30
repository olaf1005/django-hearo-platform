#!/bin/bash
source scripts/settings.sh
if [ -f "scripts/settings.local.sh" ]; then
    source scripts/settings.local.sh
fi
source scripts/bash-colors.sh
source scripts/helpers.sh
source scripts/lib.sh
source scripts/update.sh
source scripts/main.sh
startup
