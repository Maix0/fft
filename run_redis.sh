#!/usr/bin/env bash

COL_RESET="\x1b[0m"
COL_BOLD="\x1b[1m"
COL_WEAK="\x1b[2m"
COL_ITALIC="\x1b[3m"
COL_UNDERLINE="\x1b[4m"

COL_BLACK="\x1b[30m"
COL_RED="\x1b[31m"
COL_GREEN="\x1b[32m"
COL_YELLOW="\x1b[33m"
COL_BLUE="\x1b[34m"
COL_MAGENTA="\x1b[35m"
COL_CYAN="\x1b[36m"
COL_WHITE="\x1b[37m"

COLB_BLACK="\x1b[90m"
COLB_RED="\x1b[91m"
COLB_GREEN="\x1b[92m"
COLB_YELLOW="\x1b[93m"
COLB_BLUE="\x1b[94m"
COLB_MAGENTA="\x1b[95m"
COLB_CYAN="\x1b[96m"
COLB_WHITE="\x1b[97m"

COLBG_BLACK="\x1b[40m"
COLBG_RED="\x1b[41m"
COLBG_GREEN="\x1b[42m"
COLBG_YELLOW="\x1b[43m"
COLBG_BLUE="\x1b[44m"
COLBG_MAGENTA="\x1b[45m"
COLBG_CYAN="\x1b[46m"
COLBG_WHITE="\x1b[47m"

COLBBG_BLACK="\x1b[10m0"
COLBBG_RED="\x1b[10m1"
COLBBG_GREEN="\x1b[10m2"
COLBBG_YELLOW="\x1b[10m3"
COLBBG_BLUE="\x1b[10m4"
COLBBG_MAGENTA="\x1b[10m5"
COLBBG_CYAN="\x1b[10m6"
COLBBG_WHITE="\x1b[10m7"

log() {
	COLOR="$COL_WHITE"
	LVL="TRACE"
	case ${1,,} in
	"err")
		COLOR="$COL_RED"
		LVL="E"
		;;
	"warn")
		COLOR="$COL_YELLOW"
		LVL="W"
		;;
	"info")
		COLOR="$COL_GREEN"
		LVL="I"
		;;
	"debug")
		COLOR="$COL_MAGENTA"
		LVL="D"
		;;
	esac
	shift 1
	echo -e "[$COL_RESET$COLOR$LVL$COL_RESET] $*$COL_RESET"
}

if [ -r ./.env ]; then
	log DEBUG "Sourcing .env file"
	. ./.env
fi

REDIS="$(which redis-server 2>/dev/null)"
if [ $? = 1 ]; then
	REDIS="$(nix shell nixpkgs\#redis --command sh -c 'which redis-server')"
fi
log DEBUG "Using redis-server: $REDIS"

log INFO "Mkdir redis directory: $(realpath ./redis)"

mkdir -p ./redis
cd ./redis || exit
log INFO "Start redis-server in $(pwd)"
exec $REDIS
