#!/usr/bin/env bash
D="`realpath $0 | xargs dirname`"
$D/setup/juicer.sh
$D/setup/beautifulsoup.sh
