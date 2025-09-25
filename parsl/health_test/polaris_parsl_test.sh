#!/bin/bash

module reset

PROJECT="datascience"
QUEUE="debug"

echo "Running parsl tests with project $PROJECT on queue $QUEUE"
# Create a virtual environment and install parsl
module use /soft/modulefiles
module load conda
conda activate base
python -m venv _parsl_test_env
source _parsl_test_env/bin/activate
pip install parsl

echo "Environment setup complete"


echo "Submitting 1 node parsl test job to queue $QUEUE with project $PROJECT"
# Run test with parsl submitting to scheduler directly
python high_throughput_test.py --provider_type pbs \
                                --machine polaris \
                                --nodes_per_block 1 \
                                --queue $QUEUE \
                                --project $PROJECT
RET_CODE_1=$?

echo "Submitting 2 node parsl test job to queue $QUEUE with project $PROJECT"
# Run test with parsl submitting to scheduler directly
python high_throughput_test.py --provider_type pbs \
                                --machine polaris \
                                --nodes_per_block 2 \
                                --queue $QUEUE \
                                --project $PROJECT
RET_CODE_2=$?

if [ $RET_CODE_1 -eq 0 ] && [ $RET_CODE_2 -eq 0 ]; then
    echo "Parsl tests completed successfully"
    exit 0
else
    echo "Parsl tests failed with return codes: $RET_CODE_1, $RET_CODE_2"
    exit 1
fi

