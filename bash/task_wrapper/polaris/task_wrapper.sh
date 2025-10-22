#!/bin/bash

RANK=$PMI_RANK
SIZE=$N_WORKER_PROCS

INPUTS_LIST="inputs.txt"
APPLICATION="$@"

echo "Worker ${RANK} of ${SIZE} starting"
i=0
while read FN; do
if [[ ${RANK} -eq $(( i % SIZE )) ]]; then
${APPLICATION} ${FN}
fi
i=$((i+1))
done <$INPUTS_LIST
