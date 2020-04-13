#!/bin/sh

PROTOCMD=protoc
OUTDIR=generated

PROTOOPT="-I proto --python_out=${OUTDIR}"

if [ ! -d ${OUTDIR} ]
then
    echo "Creating output dir: ${OTUDIR}" ...
    mkdir ${OUTDIR}
fi

set -x
for proto in proto/*
do
    ${PROTOCMD} ${PROTOOPT} ${proto}
done
set +x
