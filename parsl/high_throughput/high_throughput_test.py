import os
import parsl
import time

import argparse
from parsl import bash_app
from config_injob import aurora_single_tile_config
from concurrent.futures import TimeoutError

@bash_app
def hello_world(task_id=0, 
                sleep_time=10, 
                stdout="hello_affinity.out", 
                stderr="hello_affinity.err"):
    return f'echo "task {task_id} start: $(date)" && echo "task {task_id}: $($HOME/GettingStarted/Examples/Aurora/affinity_gpu/sycl/hello_affinity)" && sleep {sleep_time} && echo "task {task_id} end: $(date)"'


def arg_parse():

    parser = argparse.ArgumentParser()    
    parser.add_argument('--verbose', default=False, action='store_true',
                        help=f'Verbose output')
    parser.add_argument('--sleep-time', type=int, default=10,
                        help='sleep time for tasks in seconds')
    parser.add_argument('--num-tasks-per-worker', type=int, default=10,
                        help='number of tasks per worker')
    parser.add_argument('--io-type', type=str, default='per-node',
                        help='file output strategy for task stdout/err')
    
    return parser.parse_args()


# Main function
if __name__ == "__main__":

    args = arg_parse()
    for arg_name, arg_value in vars(args).items():
        print(f"Argument '{arg_name}': {arg_value}")

    use_config = aurora_single_tile_config
        
    with parsl.load(use_config):

        print(f"Hello parsl",flush=True)

        # Set the number of tasks per worker and the sleep time
        n_tasks_per_worker = args.num_tasks_per_worker
        sleep_time = args.sleep_time
        n_workers_per_node = 12
        zero_latency_runtime = sleep_time*n_tasks_per_worker

        # Get the number of nodes from the PBS_NODEFILE environment variable
        nodefile = os.getenv("PBS_NODEFILE")
        n_nodes = len(open(nodefile).readlines())
        cwd = os.getcwd()

        # Set the number of logs to the number of nodes
        n_logs = n_nodes

        # Set the number of tasks to run
        n_tasks = n_tasks_per_worker*n_workers_per_node*n_nodes
        print(f"Running {n_tasks} tasks on {n_nodes} nodes",flush=True)

        # Run the tasks
        start_time = time.perf_counter()
        
        # Create a list of futures
        futures = []
        for i in range(n_tasks):
            # Set stdout and stderr files
            if args.io_type == 'by-node':
                stdout = f"{cwd}/output-by-node/{i%n_nodes}/hello_affinity_{i%n_nodes}.out"
                stderr = f"{cwd}/output-by-node/{i%n_nodes}/hello_affinity_{i%n_nodes}.err"
            elif args.io_type == 'by-task':
                stdout = f"{cwd}/output-by-task/{i}/hello_affinity_{i}.out"
                stderr = f"{cwd}/output-by-task/{i}/hello_affinity_{i}.err"
            else:
                stdout = stderr = '/dev/null'

            f = hello_world(task_id=i,
                            sleep_time=sleep_time,
                            stdout=stdout,
                            stderr=stderr)
            futures.append(f)

        # Wait for all tasks to finish
        print(f"Waiting for {n_tasks} tasks to finish",flush=True)
        if args.verbose:
            n_finished = 0
            polling_time_max = n_tasks_per_worker*sleep_time*1000
            polling_time = 0
            completed_tasks = []
            while n_finished < n_tasks and polling_time < polling_time_max:
                for i,f in enumerate(futures):
                    if f in completed_tasks: 
                        continue
                    if f.done():
                        completed_tasks.append(f)
                        n_finished += 1
                        print(f"Task {i} finished: {f.result()}",flush=True)
                time.sleep(0.1)
                polling_time += 0.1
        else:
            n_finished = 0
            for i,f in enumerate(futures):
                try:
                    timeout = zero_latency_runtime*10
                    f.result(timeout=timeout)
                    n_finished += 1
                except TimeoutError:
                    print(f"Task {i} timed out",flush=True)
        end_time = time.perf_counter()
        if n_finished == n_tasks:
            print(f"All tasks finished in {end_time - start_time:.2f} seconds",flush=True)
            print(f"Tasks per second per node: {n_tasks/(end_time - start_time)/n_nodes:.2f}",flush=True)
            print(f"Runtime - Zero latency runtime: {end_time - start_time - zero_latency_runtime:.2f} seconds",flush=True)
            print("Goodbye parsl",flush=True)
        else:
            print(f"Not all tasks finished, only {n_finished} out of {n_tasks} tasks",flush=True)
            print(f"Runtime is {end_time - start_time:.2f} seconds",flush=True)
