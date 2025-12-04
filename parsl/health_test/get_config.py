import os
import sys
from parsl.config import Config

# This is just one example config, please see the Aurora documentation for parsl for more
# Config versions and options: https://docs.alcf.anl.gov/aurora/workflows/parsl/

# Use LocalProvider to launch workers within a submitted batch job
from parsl.providers import LocalProvider, PBSProProvider
# The high throughput executor is for scaling large single core/tile/gpu tasks on HPC system:
from parsl.executors import HighThroughputExecutor
# Use the MPI launcher to launch worker processes:
from parsl.launchers import MpiExecLauncher


def get_config(provider_type, 
               machine, 
               nodes_per_block,
               queue = None,
               project = None,):
    
    env_path = os.path.join(sys.prefix, "bin/activate")
    rundir = os.getcwd()

    # Set launcher
    launcher = MpiExecLauncher(bind_cmd="--cpu-bind", overrides="--ppn 1")
    
    # Set Provider
    if provider_type == "local":
        provider = LocalProvider()
    elif provider_type == "pbs":
        provider = PBSProProvider()
        provider.account = project
        provider.queue = queue
        provider.walltime = "00:10:00" 
        provider.worker_init = f"source {env_path}; cd {rundir}" 
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

    provider.max_blocks = 1
    provider.init_blocks = 1
    provider.nodes_per_block = nodes_per_block


    # Set executor
    executor = HighThroughputExecutor(provider=provider)

    # Set machine specific parameters
    if machine in ["polaris", "sirius"]:
        executor.available_accelerators = ['0','1','2','3']
        executor.max_workers_per_node = 4
        executor.cpu_affinity = "list:24-31,56-63:16-23,48-55:8-15,40-47:0-7,32-39"
        launcher.overrides += " --env TMPDIR=$TMPDIR"
        if provider_type == "pbs":
            executor.provider.cpus_per_node = 64
            if machine == "polaris": executor.provider.scheduler_options = "#PBS -l filesystems=home:eagle:grand"
            if machine == "sirius": executor.provider.scheduler_options = "#PBS -l filesystems=home:tegu"
    elif machine == "aurora":
        executor.available_accelerators = ['0.0','0.1','1.0','1.1','2.0','2.1','3.0','3.1','4.0','4.1','5.0','5.1']
        executor.max_workers_per_node = 12
        executor.cpu_affinity = "list:1-8,105-112:9-16,113-120:17-24,121-128:25-32,129-136:33-40,137-144:41-48,145-152:53-60,157-164:61-68,165-172:69-76,173-180:77-84,181-188:85-92,189-196:93-100,197-204",
        if provider_type == "pbs":
            executor.provider.scheduler_options = "#PBS -l filesystems=home:flare"
            executor.provider.cpus_per_node = 208
    else:
        raise ValueError(f"Unknown machine: {machine}")

    executor.provider.launcher = launcher

    config = Config(executors=[executor])
    return config
