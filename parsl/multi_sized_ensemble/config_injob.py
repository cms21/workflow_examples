import os
from parsl.config import Config
from parsl import bash_app
import parsl
import sys
import time
from concurrent.futures import TimeoutError
# Use LocalProvider to launch workers within a submitted batch job
from parsl.providers import LocalProvider, PBSProProvider
# The high throughput executor is for scaling large single core/tile/gpu tasks on HPC system:
from parsl.executors import HighThroughputExecutor, MPIExecutor
# Use the MPI launcher to launch worker processes:
from parsl.launchers import MpiExecLauncher, SimpleLauncher


resource_specification_1node = {
  'num_nodes': 1,        # Number of nodes required for the application instance
  'ranks_per_node': 12,          # Number of ranks / application elements to be launched per node
  'num_ranks': 1 * 12,   # Number of ranks in total
}

resource_specification_2node = {
  'num_nodes': 2,        # Number of nodes required for the application instance
  'ranks_per_node': 12,          # Number of ranks / application elements to be launched per node
  'num_ranks': 2 * 12,   # Number of ranks in total
}

resource_specification_4node = {
  'num_nodes': 4,        # Number of nodes required for the application instance
  'ranks_per_node': 12,          # Number of ranks / application elements to be launched per node
  'num_ranks': 4 * 12,   # Number of ranks in total
}

resource_specification_8node = {
  'num_nodes': 8,        # Number of nodes required for the application instance
  'ranks_per_node': 12,          # Number of ranks / application elements to be launched per node
  'num_ranks': 8 * 12,   # Number of ranks in total
}

resource_specifications = {1: resource_specification_1node,
                           2: resource_specification_2node,
                           4: resource_specification_4node,
                           8: resource_specification_8node}

tile_names = [f'{gid}.{tid}' for gid in range(6) for tid in range(2)]

def get_config(nnodes,walltime="0:30:00",parent_dir=os.getcwd()):
    config = Config(
        executors=[
            MPIExecutor(
                label="mpi_executor",
                max_workers_per_block=max(1, nnodes//8),
                provider=LocalProvider(
                    # Number of nodes job
                    nodes_per_block=nnodes,
                    launcher=SimpleLauncher(),
                    init_blocks=1,
                    max_blocks=1,
                    worker_init=f"export ZE_FLAT_DEVICE_HIERARCHY=COMPOSITE"
                ),
            ),
        ]
    )
    return config