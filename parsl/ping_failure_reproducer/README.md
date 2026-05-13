# Distributed Lustre I/O with Parsl & MPI

This test aims to distribute worker processes across multiple nodes of a job.  Each worker will repeatedly execute the task script, which writes a file of a given size to on-node /tmp and the move or copy it to a destination directory on lustre.

Two methods are used for distributing workers.

## MPI

To execute the MPI only solution submit the script submit_test.sh

```
qsub submit_test.sh
```

Edit parameters for sleep time, file size and/or lustre destination directory.

## Parsl

This version should be run from a login node.  It will execute a workflow that uses Parsl's PBSProProvdider to provision nodes and the MpiExecLauncher to distribute workers.  To launch:

```
source ~/_parsl/bin/activate
python high_throughput_test.py --dest_dir /destination/path/on/lustre
```