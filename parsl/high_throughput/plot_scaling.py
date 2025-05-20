from matplotlib import pyplot as plt
import numpy as np
import os

# Plots to make:
# 1. Plot the elapsed time vs. number of nodes
# 2. Plot the parsl overhead time vs. number of nodes
# 3. Plot the task rate vs. number of nodes

format = 'png'

def get_elapsed_time(n, io_type):
    """
    Get the elapsed time from the log file
    """
    elapsed_time_run = []
    # Get the elapsed times from the log file
    log_file = f"{n}/elapsed_time.txt"
    with open(log_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if io_type in line:
                elapsed_time_run.append(float(line.split()[-2]))
                    
    elapsed_time = np.mean(elapsed_time_run) 
    return elapsed_time

def get_parsl_time(n, io_type):

    """
    Get the parsl time from the log file
    """
    parsl_time_run = []
    # Get the elapsed times from the log file
    log_file = f"{n}/{'-'.join(io_type.split())}.txt"
    with open(log_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if "All tasks finished" in line:
                parsl_time_run.append(float(line.split()[-2]))
    parsl_time = np.mean(parsl_time_run)
    return parsl_time


def get_task_rate(n, io_type):

    """
    Get the parsl time from the log file
    """
    rate_run = []
    # Get the elapsed times from the log file
    log_file = f"{n}/{'-'.join(io_type.split())}.txt"
    with open(log_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if "Tasks per second per node:" in line:
                rate_run.append(float(line.split()[-1]))
    rate = np.mean(rate_run)
    return rate

def plot_elapsed_time(nnodes, 
                     io_types=['no io','by node','by task']):

    """
    Plot the elapsed time vs. number of nodes
    """

    fig, ax = plt.subplots()
    
    for io_type in io_types:
        elapsed_time = []
        for nn in nnodes:    
            elapsed_time.append(get_elapsed_time(nn,io_type))
        ax.plot(nnodes, elapsed_time, 'o-', label=io_type)

    ax.set_xlabel('Number of nodes')
    ax.set_ylabel('Elapsed time (s)')
    ax.legend(loc=0) 
    ax.set_xscale('log', base=2)

    fig.tight_layout()
    fig.savefig(f'elapsed_time.{format}')



def plot_weak_scaling(nnodes, 
                     io_types=['no io','by node','by task'],
                     comp_run=2):

    """
    Plot the weak scaling vs. number of nodes
    """

    fig, ax = plt.subplots()
    
    for io_type in io_types:
        weak_ratio = []
        comp_time = get_elapsed_time(comp_run, io_type)
        for nn in nnodes:    
            weak_ratio.append(comp_time/get_elapsed_time(nn,io_type))
        ax.plot(nnodes, weak_ratio, 'o-', label=io_type)

    ax.set_xlabel('Number of nodes')
    ax.set_ylabel('Elapsed time (2 nodes) / Elapsed time')
    ax.legend(loc=0) 
    ax.set_xscale('log', base=2)

    fig.tight_layout()
    fig.savefig(f'weak_scaling.{format}')


def plot_parsl_overhead(nnodes, 
                     io_types=['no io','by node','by task'],
                     ):

    """
    Plot the parsl overhead vs. number of nodes
    """

    fig, ax = plt.subplots()
    
    for io_type in io_types:
        overhead = []
        for nn in nnodes:
            elapsed_time = get_elapsed_time(nn, io_type)
            parsl_time = get_parsl_time(nn, io_type)
            overhead.append(elapsed_time - parsl_time)
        ax.plot(nnodes, overhead, 'o-', label=io_type)

    ax.set_xlabel('Number of nodes')
    ax.set_ylabel('Parsl overhead (s)')
    ax.legend(loc=0) 
    ax.set_xscale('log', base=2)

    fig.tight_layout()
    fig.savefig(f'parsl_overhead.{format}')


def plot_task_rate(nnodes, 
                     io_types=['no io','by node','by task'],
                     n_workers_per_node=12.,
                     task_time=10):

    """
    Plot the task rate vs. number of nodes
    """

    fig, ax = plt.subplots()
    
    for io_type in io_types:
        task_rate = []
        for nn in nnodes:    
            task_rate_per_node = get_task_rate(nn, io_type)
            task_rate_per_worker = task_rate_per_node / n_workers_per_node
            print(f"Task rate per node: {task_rate_per_worker:.5f} tasks/s")
            task_rate.append(task_rate_per_worker)
        ax.plot(nnodes, task_rate, 'o-', label=io_type)

    #ax.plot(nnodes, [1/task_time for i in range(len(nnodes))], '--k', label='1/task_time')
    ax.set_xlabel('Number of nodes')
    ax.set_ylabel('Task rate per worker (tasks/second/worker)')
    ax.legend(loc=0) 
    ax.set_xscale('log', base=2)

    fig.tight_layout()
    fig.savefig(f'task_rate.{format}')
    # Set the number of nodes to test

nnodes = [2,32,128,512,1024,2048]

plot_elapsed_time(nnodes,)
plot_weak_scaling(nnodes,)
plot_parsl_overhead(nnodes,)
plot_task_rate(nnodes,task_time=11)
