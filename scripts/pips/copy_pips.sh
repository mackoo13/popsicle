#!/usr/bin/env bash

rm -rf ${PIPS_PROC_PATH}
rsync -av --exclude=".*" --exclude="*.result" ${PIPS_KERNEL_PATH} ${PIPS_PROC_PATH}