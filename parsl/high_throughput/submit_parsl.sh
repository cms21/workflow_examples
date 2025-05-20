#!/bin/bash -l
#PBS -l select=2
#PBS -l walltime=0:60:00
#PBS -q debug
#PBS -A datascience
#PBS -l filesystems=home:flare

cd ${PBS_O_WORKDIR}
export ZE_FLAT_DEVICE_HIERARCHY=COMPOSITE

source $HOME/_parsl/bin/activate
LAUNCH_SCRIPT=/flare/datascience/csimpson/workflow_examples/parsl/high_throughput/high_throughput_test.py

NNODES=`wc -l < $PBS_NODEFILE`
echo "Number of nodes: ${NNODES}" > nnodes.txt
SLEEPTIME=10
NUMTASKS=10

echo "*** Run a pre-test with no io ***"
EXE="python ${LAUNCH_SCRIPT} \
    --sleep-time=${SLEEPTIME} \
    --num-tasks-per-worker=3 \
    --io-type=none"
echo ${EXE}
${EXE}
echo ""

> no-io.txt
> by-node.txt
> by-task.txt

echo "*** Running performance tests ***"
for i in $(seq 1 3); do
    # No io
    SECONDS=0
    echo "* Run no io test *"
    EXE="python ${LAUNCH_SCRIPT} \
        --sleep-time=${SLEEPTIME} --num-tasks-per-worker=${NUMTASKS} --io-type=none"
    echo ${EXE}
    ${EXE} >> no-io.txt
    echo "Elapsed time for no io test: ${SECONDS} seconds"
    echo ""
    
    # io by node
    SECONDS=0
    echo "* Run io by node test *"
    EXE="python ${LAUNCH_SCRIPT} \
        --sleep-time=${SLEEPTIME} --num-tasks-per-worker=${NUMTASKS} --io-type=by-node"
    echo ${EXE}
    ${EXE} >> by-node.txt
    echo "Elapsed time for io by node test: ${SECONDS} seconds"
    echo ""

    # io by task
    SECONDS=0
    echo "* Run io by task test *"
    EXE="python ${LAUNCH_SCRIPT} \
        --sleep-time=${SLEEPTIME} --num-tasks-per-worker=${NUMTASKS} --io-type=by-task"
    echo ${EXE}
    ${EXE} >> by-task.txt
    echo "Elapsed time for io by task test: ${SECONDS} seconds"
    echo ""
done

SPLIT=$(echo ${PBS_JOBID} | tr "." "\n")
JUST_ID=$(echo $SPLIT | awk '{print $1}')

grep Elapsed "submit_parsl.sh.o${JUST_ID}" > elapsed_time.txt
