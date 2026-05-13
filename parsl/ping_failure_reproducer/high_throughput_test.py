import os
import parsl
import time

import argparse
from parsl import bash_app
from parsl.addresses import address_by_interface
from config import get_config
from concurrent.futures import TimeoutError, as_completed

@bash_app
def task_wrapper(task_id,
                sleep_time=60,
                file_size=1,
                dest_dir,
                stdout="stdout", 
                stderr="stderr"):
    rank = task_id
    return f"/flare/workflow_scaling/csimpson/workflow_examples/parsl/ping_failure_reproducer/task_script.sh {rank} {sleep_time} {file_size}"


def arg_parse():
    parser = argparse.ArgumentParser()    
    parser.add_argument('--num-tasks-per-worker', type=int, default=10,
                        help='number of tasks per worker')
    parser.add_argument('--dest-dir', type=str,
                        help='lustre directory where data are copied')
    return parser.parse_args()


# Main function
if __name__ == "__main__":

    args = arg_parse()
    for arg_name, arg_value in vars(args).items():
        print(f"Argument '{arg_name}': {arg_value}")

    num_nodes = 2

    use_config = get_config(num_nodes,
                            'datascience', 
                            'debug', 
                            '0:30:0',
                            'export TMPDIR=/tmp; source ~/_parsl/bin/activate')
    
    with parsl.load(use_config):

        print(f"Hello parsl",flush=True)

        # Set the number of tasks per worker
        n_tasks_per_worker = args.num_tasks_per_worker
        n_workers_per_node = 102


        # Set the number of tasks to run
        n_tasks = n_tasks_per_worker*n_workers_per_node*num_nodes
        print(f"Running {n_tasks} tasks on {num_nodes} nodes",flush=True)

        # Run the tasks
        start_time = time.perf_counter()
        
        # Create a list of futures
        futures = []
        for i in range(n_tasks):
            f = task_wrapper(task_id=i,
                            sleep_time=1,
                            file_size=1,
                            dest_dir=dest_dir)
            futures.append(f)

        # Wait for all tasks to finish
        wait_start_time = time.perf_counter()
        print(f"Waiting for {n_tasks} tasks to finish",flush=True)
        completed_tasks = []
        n_finished = 0
        for i,f in enumerate(as_completed(futures)):
            completed_tasks.append(f)
            n_finished += 1
            print(f"{round(time.perf_counter() - wait_start_time, 1)}s: Task {i} finished; {n_finished=}", flush=True)
    