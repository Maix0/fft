#!/bin/sh
set -x
dbml_sqlite -p -f -t -i schema.dbml -w schema.sql
