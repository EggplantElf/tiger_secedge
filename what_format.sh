#!/bin/bash

set -ue

INPUT=$1
OUTPUT=$2

sed 's/[0-9]*_//' $INPUT | cut -f 1-12 > tmp1
cut -f 4 tmp1 > tmp2
paste -d '\t' tmp1 tmp2 tmp2 tmp2 > $OUTPUT
rm tmp1 tmp2
