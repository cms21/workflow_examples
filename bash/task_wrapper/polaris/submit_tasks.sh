#!/bin/bash -l
#PBS -l select=4
#PBS -l walltime=0:60:00
#PBS -l filesystems=home:eagle:grand
#PBS -q debug-scaling
#PBS -A <your-project-name>

# Change to working directory
cd ${PBS_O_WORKDIR}

# Set the number of processes that run instances of my_script.py
NNODES=`wc -l < $PBS_NODEFILE`
WORKERS_PER_NODE=8
export N_WORKER_PROCS=$(( NNODES*WORKERS_PER_NODE ))

# Modify this block to activate your environment, this activates default conda module on Polaris
module use /soft/modulefiles
module load conda
conda activate base # <-- modify to activate your environment

# Make a file inputs.txt that contains a list of input files contained in ./input_files
ls input_files/* > inputs.txt

echo "Creating ${N_WORKER_PROCS} processes to run postprocessing tasks"

# Launch $N_WORKER_PROCS processes to run script my_script.py on input files:
mpiexec -n $N_WORKER_PROCS --ppn $WORKERS_PER_NODE ./task_wrapper.sh python ./my_script.py