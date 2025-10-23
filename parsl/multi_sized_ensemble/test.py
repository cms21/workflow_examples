import os
import parsl
import time

import argparse
from parsl import bash_app
from config_injob import *
from concurrent.futures import TimeoutError


@bash_app
def Simulation(sim_id: int, run_time:float, parsl_resource_specification: dict, stdout: str = None, stderr: str = None):
    return f"$PARSL_MPI_PREFIX gpu_tile_compact.sh /lus/flare/projects/datascience/hari/task_launch_scaling/pattern2/parsl/mpi_example {run_time} false"

def arg_parse():

    parser = argparse.ArgumentParser()    
    parser.add_argument('--sleep-time', type=int, default=10,
                        help='sleep time for tasks in seconds')
    parser.add_argument('--num-tasks-per-worker', type=int, default=10,
                        help='number of tasks per worker')
    parser.add_argument('--io-type', type=str, default='false',
                        help='file output strategy for task stdout/err')
    
    return parser.parse_args()


# Main function
if __name__ == "__main__":

    args = arg_parse()
    for arg_name, arg_value in vars(args).items():
        print(f"Argument '{arg_name}': {arg_value}")

    io = args.io_type.lower() == 'true'
    os.makedirs(f"{os.getcwd()}/output", exist_ok=True)

    with open(os.getenv("PBS_NODEFILE","/dev/null"),"r") as f:
        nodes = f.readlines()
    
    nnodes = len(nodes)
    config = get_config(nnodes)
    ntasks = (nnodes//2)*args.num_tasks_per_worker
    max_timeout = args.sleep_time * args.num_tasks_per_worker * 10

    sleep_times = {
        1:30,
        2:60,
        4:120,
        8:240
    }

    ntasks_dict = {
        1:nnodes,
        2:nnodes//2,
        4:nnodes//4,
        8:nnodes//8
    }

    with parsl.load(config):
        print(f"Hello parsl",flush=True)
        start_time = time.perf_counter()
        # Run the tasks
        # Create a list of futures
        futures = []
        ntasks = 0
        for task_nnodes, sleep_time in sleep_times.items():
            for sim_id in range(ntasks_dict[task_nnodes]):
                f = Simulation(sim_id=ntasks,
                               run_time=sleep_time,
                               parsl_resource_specification=resource_specifications[task_nnodes],
                               stdout=f"{os.getcwd()}/output/sim_{ntasks}.out" if io else None,
                               stderr=f"{os.getcwd()}/output/sim_{ntasks}.err" if io else None
                )
                futures.append(f)
                ntasks += 1

        # Wait for all tasks to finish
        print(f"Waiting for {ntasks} tasks to finish",flush=True)
        finished = []
        failed = []
        tstart = time.time()
        while len(finished) + len(failed) < ntasks:
            for i,f in enumerate(futures):
                if i in finished:
                    continue
                try:
                    f.result(timeout=max_timeout)
                    finished.append(i)
                except TimeoutError:
                    failed.append(i)
        end_time = time.perf_counter()
        if len(finished) == ntasks:
            print(f"All tasks finished in {end_time - start_time:.2f} seconds",flush=True)
            print("Goodbye parsl",flush=True)
        else:
            print(f"Not all tasks finished, only {len(finished)} out of {ntasks} tasks",flush=True)
            print(f"Runtime is {end_time - start_time:.2f} seconds",flush=True)