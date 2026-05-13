import os
from parsl.config import Config

# This is just one example config, please see the Aurora documentation for parsl for more
# Config versions and options: https://docs.alcf.anl.gov/aurora/workflows/parsl/

# Use LocalProvider to launch workers within a submitted batch job
from parsl.providers import PBSProProvider
# The high throughput executor is for scaling large single core/tile/gpu tasks on HPC system:
from parsl.executors import HighThroughputExecutor
from parsl.addresses import address_by_interface
# Use the MPI launcher to launch worker processes:
from parsl.launchers import MpiExecLauncher

#tile_names = [f'{gid}.{tid}' for gid in range(6) for tid in range(2)]
#start_threads = [1,9,17,25,33,41,53,61,69,77,85,93]
#threads_by_tile = [f"{st}-{st+7},{st+104}-{st+111}" for st in start_threads]

threads_by_tile = [f"{1+st},{st+105}" for st in range(51)] +[f"{53+st},{st+157}" for st in range(51)]
print(f"Number of workers with assigned threads: {len(threads_by_tile)}")
cpu_affinity = "list:"+":".join(threads_by_tile)


def get_config(num_nodes,
                project,
                queue,
                walltime,
                worker_init,
                workers_per_node=102,
                scheduler_options="#PBS -l filesystems=home:flare"):
    return Config(
            initialize_logging=False,
            executors=[
                HighThroughputExecutor(
                    # Ensures one worker per GPU tile on each node
                    #available_accelerators=tile_names,
                    # Specify interface for manager-interchange communication
                    address=address_by_interface('hsn0'),
                    max_workers_per_node=workers_per_node,
                    # Distributes threads to workers/tiles in a way optimized for Aurora
                    cpu_affinity=cpu_affinity,
                    # Increase if you have many more tasks than workers
                    prefetch_capacity=0,
                    # Options that specify properties of PBS Jobs
                    provider=PBSProProvider(
                        # Project name
                        account=project,
                        # Submission queue
                        queue=queue,
                        # Commands run before workers launched
                        # Make sure to activate your environment where Parsl is installed
                        worker_init=worker_init,
                        # Wall time for batch jobs
                        walltime=walltime,
                        # Change if data/modules located on other filesystem
                        scheduler_options=scheduler_options,
                        # Ensures 1 manger per node; the manager will distribute work to its 12 workers, one per tile
                        launcher=MpiExecLauncher(bind_cmd="--cpu-bind", overrides="--ppn 1"),
                        # options added to #PBS -l select aside from ncpus
                        select_options="",
                        # Number of nodes per PBS job
                        nodes_per_block=num_nodes,
                        # Minimum number of concurrent PBS jobs running workflow
                        min_blocks=0,
                        # Maximum number of concurrent PBS jobs running workflow
                        max_blocks=1,
                        init_blocks=1,
                    ),
                ),
            ],
        )
