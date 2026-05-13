#!/bin/bash -l
#PBS -l select=2
#PBS -l walltime=0:10:00
#PBS -l filesystems=home:flare
#PBS -q debug
#PBS -A datascience

# Change to working directory
cd ${PBS_O_WORKDIR}

# Set the number of processes that run instances of my_script.py
NNODES=`wc -l < $PBS_NODEFILE`
WORKERS_PER_NODE=8
export N_WORKER_PROCS=$(( NNODES*WORKERS_PER_NODE ))
echo "Creating ${N_WORKER_PROCS} processes to run workers"

# Worker script
WORKER_SCRIPT=$PWD/worker_script.sh

#Task script
TASK_SCRIPT=$PWD/task_script.sh

# Destination directory on lustre
DEST_DIR="/flare/datascience/csimpson/toy_test/test/${host}/"

#Parameters
SLEEP_TIME=1 # in seconds
FILE_SIZE=1 # in MB

echo "Launching workers..."
# Launch $N_WORKER_PROCS processes to run task script with inputs on each rank:
mpiexec -n $N_WORKER_PROCS --ppn $WORKERS_PER_NODE $WORKER_SCRIPT $TASK_SCRIPT $SLEEP_TIME $FILE_SIZE $DEST_DIR
