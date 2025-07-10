from matplotlib import pyplot as plt
import numpy as np
import os
import glob
from datetime import datetime
from multiprocessing import Pool

# Plots to make:
# 1. Plot the elapsed time vs. number of nodes
# 2. Plot the parsl overhead time vs. number of nodes
# 3. Plot the task rate vs. number of nodes

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

    recieve_lines = []
    finished_lines = []    

    with open(worker_path, "r") as wl:
        for line in wl:
            if "Received executor task" in line:
                recieve_lines.append(line)
            if "All processing finished for executor task" in line:
                finished_lines.append(line)
    return (recieve_lines, finished_lines)

def get_run_task_times(runinfo_path):
    print(f"{runinfo_path}/HighThroughputExecutor/block-0/*/worker_*.log")
    worker_log_paths = glob.glob(f"{runinfo_path}/HighThroughputExecutor/block-0/*/worker_*.log")
    time_format = "%Y-%m-%d %H:%M:%S.%f"

    recieve_lines = []
    finished_lines = []

    with Pool(processes = 8) as pool:
        results = pool.map(_get_run_task_times, worker_log_paths)

    for r in results:
        recieve_lines += r[0]
        finished_lines += r[1]

    task_times = {}
    for line in recieve_lines:
        task_id = line.split("executor task")[-1].strip()
        time = line.split("worker_log")[0].strip()
        task_times[task_id] = {"start": datetime.strptime(time, time_format)}

    for line in finished_lines:
        task_id = line.split("executor task")[-1].strip()
        time = line.split("worker_log")[0].strip()
        task_times[task_id]['end'] = datetime.strptime(time, time_format)
    
    task_ids = task_times.keys()
    min_start_time = min([task_times[k]['start'] for k in task_ids])
    for k in task_ids:
        task_times[k]['start'] = (task_times[k]['start'] - min_start_time).total_seconds()
        task_times[k]['end'] = (task_times[k]['end'] - min_start_time).total_seconds()

    return task_times


def get_experiment_task_times(nnodes, run_iter):
    runinfo_path = glob.glob(f"{nnodes}/runinfo/{run_iter}")
    task_times = get_run_task_times(runinfo_path[0])
    return task_times


def plot_task_completion(nnodes, run_iter='001'):
    
    fig = plt.figure()

    for nn in nnodes:
        task_times = get_experiment_task_times(nn, run_iter)
        start_times = np.array([task_times[k]['start'] for k in task_times.keys()])
        end_times = np.array([task_times[k]['end'] for k in task_times.keys()])
        y = np.concatenate((np.ones_like(start_times), -1.*np.ones_like(end_times)))
        x = np.concatenate((start_times,end_times))
        isort = np.argsort(x)
        x = x[isort]
        y = y[isort]
        plt.plot(x,np.cumsum(y)/nn,drawstyle='steps-pre', label = f"{nn} nodes")
    plt.legend(loc=0)
    plt.xlabel("Elapsed time (s)")
    plt.ylabel("Occupied workers / Number of Nodes")
    fig.savefig(f"occupied_workers_{run_iter}.png",format='png')

    fig = plt.figure()
    for nn in nnodes:
        task_times = get_experiment_task_times(nn, run_iter)
        start_times = np.array([task_times[k]['start'] for k in task_times.keys()])
        end_times = np.array([task_times[k]['end'] for k in task_times.keys()])
        y = np.ones_like(end_times)
        x = end_times
        isort = np.argsort(x)
        x = x[isort]
        y = y[isort]
        plt.plot(x,np.cumsum(y)/nn,drawstyle='steps-pre', label = f"{nn} nodes")
    plt.legend(loc=0)
    plt.xlabel("Elapsed time (s)")
    plt.ylabel("Finished tasks / Number of Nodes")
    fig.savefig(f"task_throughput_{run_iter}.png",format='png')

nnodes = [2,32,128,512,1024,2048]

plot_task_completion(nnodes, run_iter='003')
plot_task_completion(nnodes, run_iter='002')
plot_task_completion(nnodes, run_iter='001')
