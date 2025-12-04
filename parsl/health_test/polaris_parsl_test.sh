#!/bin/bash

# Script to test functionality of Parsl on ALCF machines Polaris and Sirius
# This script installs Parsl with the default conda environment on the system
# and tests Parsl's PBSProProivder and HighThroughputExecutor with the MpiexecLauncher
# to run tasks first in a 1 node job and then in a 2 node job.

# Start by resetting modules
module reset

# Set machine specific settings for either Polaris or Sirius

#MACHINE="polaris"
#PROJECT="datascience"
#QUEUE="debug"

MACHINE="sirius"
PROJECT="datascience"
QUEUE="workq"

# Create a virtual environment and install parsl
echo "Running parsl tests on $MACHINE with project $PROJECT in queue $QUEUE"
module use /soft/modulefiles
module load conda
conda activate base
python --version
python -m venv _parsl_test_env
source _parsl_test_env/bin/activate
pip install --no-cache-dir parsl
echo "Environment setup complete"

# Run test with parsl submitting a 1 node job
echo "Submitting 1 node parsl test job to queue $QUEUE with project $PROJECT"
python high_throughput_test.py --provider_type pbs \
                                --machine $MACHINE \
                                --nodes_per_block 1 \
				--timeout 30 \
                                --queue $QUEUE \
                                --project $PROJECT
RET_CODE_1=$?

# Run test with parsl submitting a 2 node job
echo "Submitting 2 node parsl test job to queue $QUEUE with project $PROJECT"
python high_throughput_test.py --provider_type pbs \
                                --machine $MACHINE \
                                --nodes_per_block 2 \
				--timeout 30 \
                                --queue $QUEUE \
                                --project $PROJECT
RET_CODE_2=$?

# Check for failures
if [ $RET_CODE_1 -eq 0 ] && [ $RET_CODE_2 -eq 0 ]; then
    echo "Parsl tests completed successfully"
    exit 0
else
    echo "Parsl tests failed with return codes: $RET_CODE_1, $RET_CODE_2"
    exit 1
fi

