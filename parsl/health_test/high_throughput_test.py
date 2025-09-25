import os
import parsl
import time

import argparse
from parsl import bash_app
from get_config import get_config
from concurrent.futures import TimeoutError

@bash_app
def hello_world(task_id=0, 
                sleep_time=10, 
                stdout="hello_affinity.out", 
                stderr="hello_affinity.err"):
    return f"sleep {sleep_time}; echo 'Hello from task {task_id}'"

def arg_parse():

    parser = argparse.ArgumentParser()    
    parser.add_argument("--provider_type", type=str, default="local",
                        help="Type of provider to use: local or pbs")
    parser.add_argument("--machine", type=str, default="polaris",
                        help="Machine type: polaris or aurora")
    parser.add_argument("--nodes_per_block", type=int, default=1,
                        help="Number of nodes per block")
    parser.add_argument("--queue", type=str, default=None,
                        help="Queue name for PBS provider")
    parser.add_argument("--project", type=str, default=None,
                        help="Project name for PBS provider")   
    
    return parser.parse_args()


# Main function
if __name__ == "__main__":

    args = arg_parse()

    config = get_config(args.provider_type,
                        args.machine,
                        args.nodes_per_block,
                        queue = args.queue,
                        project = args.project)
    
    if args.machine == "polaris":
        workers_per_node = 4
    elif args.machine == "aurora":
        workers_per_node = 12
    else:
        raise ValueError(f"Unknown machine type: {args.machine}")

    print("Testing with config:")
    print(config)
    print("")
    with parsl.load(config):
        
        print("Submitting tasks...")

        futures = []
        num_tasks = args.nodes_per_block * workers_per_node * 6
        for i in range(num_tasks):
            futures.append(hello_world(task_id=i, sleep_time=10))

        print("Waiting for tasks to complete...")

        for i, future in enumerate(futures):
            result = future.result(timeout=30)
            # print(f"Task {i} completed with result: {result}", flush=True)
            
        print("All tasks completed.")