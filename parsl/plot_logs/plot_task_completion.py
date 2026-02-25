from matplotlib import pyplot as plt
import numpy as np
import os
import glob
from datetime import datetime
from multiprocessing import Pool


format = 'png'

# Sample worker log:
# 2025-06-23 21:48:05.125 worker_log:640 77446 MainThread [INFO]  Worker 1 started
# 2025-06-23 21:48:05.126 worker_log:697 77446 MainThread [INFO]  Set worker CPU affinity to [9, 10, 11, 12, 13, 14, 15, 16, 113, 114, 115, 116, 117, 118, 119, 120]
# 2025-06-23 21:48:05.138 worker_log:725 77446 MainThread [INFO]  Pinned worker to accelerator: 0.1
# 2025-06-23 21:48:05.138 worker_log:753 77446 MainThread [INFO]  Received executor task 13
# 2025-06-23 21:48:15.337 worker_log:771 77446 MainThread [INFO]  Completed executor task 13
# 2025-06-23 21:48:15.338 worker_log:782 77446 MainThread [INFO]  All processing finished for executor task 13
# 2025-06-23 21:48:15.338 worker_log:753 77446 MainThread [INFO]  Received executor task 48
# 2025-06-23 21:48:25.491 worker_log:771 77446 MainThread [INFO]  Completed executor task 48
# 2025-06-23 21:48:25.492 worker_log:782 77446 MainThread [INFO]  All processing finished for executor task 48
# 2025-06-23 21:48:25.492 worker_log:753 77446 MainThread [INFO]  Received executor task 72
# 2025-06-23 21:48:35.597 worker_log:771 77446 MainThread [INFO]  Completed executor task 72
# 2025-06-23 21:48:35.598 worker_log:782 77446 MainThread [INFO]  All processing finished for executor task 72

def _get_run_task_times(worker_path):
    """ Get the task start and end times from a single worker log.
    Parameters
    -----------
    worker_path : str
        Path to the worker log file.
    -----------
    Returns
    recieve_lines : list
        List of lines indicating task receipt.
    finished_lines : list
        List of lines indicating task completion.
    -----------
    """

    recieve_lines = []
    finished_lines = []    

    with open(worker_path, "r") as wl:
        for line in wl:
            if "Received executor task" in line:
                recieve_lines.append(line)
            if "All processing finished for executor task" in line:
                finished_lines.append(line)
    return (recieve_lines, finished_lines)

def get_run_task_times(block_path, min_start_time=None):
    """ Get the task start and end times from worker logs in a block directory.
    Parameters
    ----------
    block_path : str
        Path to the block directory containing worker logs.
    min_start_time : datetime, optional
        Minimum start time to normalize task times. If None, uses the earliest task start time.
    -----------
    Returns
    task_times : dict
        Dictionary of task start and end times.
    num_workers : int
        Number of workers in the block.
    num_managers : int
        Number of managers in the block.
    -----------
    """


    print(f"{block_path}/*/worker_*.log")
    worker_log_paths = glob.glob(f"{block_path}/*/worker_*.log")
    manager_log_paths = glob.glob(f"{block_path}/*/manager.log")
    num_workers = len(worker_log_paths)
    num_managers = len(manager_log_paths)
    print(f"Number of workers: {num_workers}, Number of managers: {num_managers}")

    time_format = "%Y-%m-%d %H:%M:%S.%f"

    recieve_lines = []
    finished_lines = []

    with Pool(processes = 8) as pool:
        results = pool.map(_get_run_task_times, worker_log_paths)

    print(f"Processed logs for {len(results)} workers.")
    for r in results:
        recieve_lines += r[0]
        finished_lines += r[1]

    task_times = {}
    for line in recieve_lines:
        task_id = line.split("executor task")[-1].strip()
        time = line.split("worker_log")[0].strip()
        try:
            task_times[task_id] = {"start": datetime.strptime(time, time_format)}
        except ValueError:
            time = line.split()[1].strip()+" "+line.split()[2].strip()
            print(f"{line=}")
            print(f"{time=}")
            task_times[task_id] = {"start": datetime.strptime(time, "%Y-%m-%d %H:%M:%S")}
        except Exception as e:
            print("Exception!")
            print(line)
            print(time)
            print(e)
            
    for line in finished_lines:
        task_id = line.split("executor task")[-1].strip()
        time = line.split("worker_log")[0].strip()
        task_times[task_id]['end'] = datetime.strptime(time, time_format)
    
    task_ids = task_times.keys()
    if min_start_time is None:
        min_start_time = min([task_times[k]['start'] for k in task_ids])
    unfinished = 0
    for k in task_ids:
        task_times[k]['start'] = (task_times[k]['start'] - min_start_time).total_seconds()
        try:
            task_times[k]['end'] = (task_times[k]['end'] - min_start_time).total_seconds()
        except:
            #print(f"Task {k} has no end time logged.")
            unfinished += 1
    print(f"Total unfinished tasks: {unfinished} out of {len(task_ids)}")

    return task_times, num_workers, num_managers

def get_start_end_times(task_times):
    """ Get arrays of start and end times from task_times dictionary.
    Parameters
    ----------
    task_times : dict
        Dictionary of task start and end times.
    -----------
    Returns
    start_times : np.array
        Array of task start times.
    end_times : np.array
        Array of task end times.
    -----------
    """
    start_times = np.array([task_times[k]['start'] for k in task_times.keys()])
    end_times = np.array([task_times[k]['end'] for k in task_times.keys() if 'end' in task_times[k]])
    return start_times, end_times

def plot_occupied_workers(block_dir=None,
                         task_times=None,
                         num_workers=None,
                         num_managers=None):

    """ Plot the number of occupied workers over time.
    Parameters
    ----------
    block_dir : str
        Path to the block directory containing worker logs.
    task_times : dict
        Dictionary of task start and end times.
    num_workers : int
        Number of workers in the block.
    num_managers : int
        Number of managers in the block.
    -----------
    Returns
    None
    -----------
    Saves a plot of occupied workers over time as 'occupied_workers.png'.
    """

    fig = plt.figure()
    if task_times is None:
        task_times, num_workers, num_managers = get_run_task_times(block_dir)
    start_times, end_times = get_start_end_times(task_times)
    
    if len(end_times) < len(start_times):
        print("Warning: Some tasks are unfinished")
    y = np.concatenate((np.ones_like(start_times), -1.*np.ones_like(end_times)))
    x = np.concatenate((start_times,end_times))
    isort = np.argsort(x)
    x = x[isort]
    y = y[isort]
    print(f"Number of available workers per manager: {num_workers/num_managers}")
    plt.plot(x/60,np.cumsum(y)/num_managers,drawstyle='steps-pre', label = f"Occupied workers")
    plt.axhline(num_workers/num_managers, ls='--', color='gray', label='Total workers')
    plt.legend(loc=0)
    plt.xlabel("Elapsed time (minutes)")
    plt.ylabel("Occupied workers / Number of Nodes")
    fig.savefig(f"occupied_workers.{format}",format=format)

def plot_task_throughput(block_dir=None,
                        task_times=None,
                        num_workers=None,
                        num_managers=None):

    """ Plot the task throughput over time. 
    Parameters
    ----------
    block_dir : str
        Path to the block directory containing worker logs.
    task_times : dict
        Dictionary of task start and end times.
    num_workers : int
        Number of workers in the block.
    num_managers : int
        Number of managers in the block.
    -----------
    Returns
    None
    -----------
    Saves a plot of task throughput over time as 'task_throughput.png'.
    """

    if task_times is None:
        task_times, num_workers, num_managers = get_run_task_times(block_dir)
    start_times, end_times = get_start_end_times(task_times)
    
    fig = plt.figure()
    y = np.ones_like(end_times)
    x = end_times
    isort = np.argsort(x)
    x = x[isort]
    y = y[isort]
    plt.plot(x/60,np.cumsum(y)/num_managers,drawstyle='steps-pre', label = f"Finished tasks")
    y = np.ones_like(start_times)
    x = start_times
    isort = np.argsort(x)
    x = x[isort]
    y = y[isort]
    plt.plot(x/60,np.cumsum(y)/num_managers,ls='--',drawstyle='steps-pre', label = f"Started tasks")

    plt.legend(loc=0)
    plt.xlabel("Elapsed time (minutes)")
    plt.ylabel("Task Count / Number of Nodes")
    fig.savefig(f"task_throughput.{format}",format=format)                    

def make_task_plots(block_dir):
    
    task_times, num_workers, num_managers = get_run_task_times(block_dir)
    
    plot_occupied_workers(task_times=task_times,
                          num_workers=num_workers,
                          num_managers=num_managers)

    plot_task_throughput(task_times=task_times,
                         num_workers=num_workers,
                         num_managers=num_managers)

#block_dir='/lus/flare/projects/neutrinoGPU/twester/icarus_run4_mc_prod/runinfo/003/htex/block-0'
block_dir = "/flare/neutrinoGPU/csimpson_testing/scaling_workflow/outputs/runinfo/003/htex/block-0"

#block_dir = "/flare/workflow_scaling/csimpson/workflow_examples/parsl/ping_failure_reproducer/512nodes/runinfo/002/HighThroughputExecutor/block-0"
make_task_plots(block_dir)

