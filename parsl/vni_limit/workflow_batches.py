import parsl
from parsl import Config
from parsl.executors import MPIExecutor
from parsl.providers import PBSProProvider
from parsl.launchers import SimpleLauncher
from parsl.app.app import bash_app

# This script demonstrates how to run mpiexec tasks in batches of 1000 on Aurora using Parsl.
# This is a workaround for the current bug in palsd that does not return VNIs 
# when mpiexec calls return


def make_config(num_executors,
                workers_per_block,
                nodes_per_block):

    base_executor = MPIExecutor(
        label='mpi_executor',
        provider=PBSProProvider(
            walltime='00:10:00',
            queue='prod',
            account='datascience',
            init_blocks=1,
            min_blocks=1,
            max_blocks=1,
            nodes_per_block=nodes_per_block,
            launcher=SimpleLauncher(),
            scheduler_options="#PBS -l filesystems=home:flare",
        ),
        max_workers_per_block=workers_per_block,
    )
    executors = []
    for i in range(num_executors):
        executor = base_executor.copy()
        executor.label = f'mpi_executor_{i}'
        executors.append(executor)  
    
    return Config(
        executors=executors,
        strategy=None,  # Use default strategy
    )   

@bash_app()
def hello_sleep(parsl_resource_specification, seconds, stdout='tasks.out', stderr='tasks.out'):
    MPI_call = f"$PARSL_MPI_PREFIX sleep {seconds}"
    return f"echo '{MPI_call}' && {MPI_call}"

if __name__ == "__main__":

    # Configuration parameters
    ntasks = 3000
    batch_size = 1000 # This is the per-job limit on mpiexecs calls allowed by pals on Aurora
    num_batches = ntasks // batch_size + (1 if ntasks % batch_size > 0 else 0)
    nodes_per_task = 2
    nodes_per_job = 32
    workers_per_job = nodes_per_job//nodes_per_task
    config = make_config(num_batches, 
                        workers_per_job,
                        nodes_per_job)

    resource_specification = {
        'num_nodes': nodes_per_task,        # Number of nodes required for the application instance
        'ranks_per_node': 12,   # Number of ranks / application elements to be launched per node
        'num_ranks': 12*nodes_per_task,        # Number of ranks in total
        }

    with parsl.load(config) as dfk:
        futures = []
        for i in range(num_batches):
            print(f"Submitting tasks to executor mpi_executor_{i}")
            for j in range(batch_size):
                if len(futures) < ntasks:
                    future = dfk.submit(hello_sleep,
                                        resource_specification, 
                                        10, 
                                        executor=f'mpi_executor_{i}')
                    futures.append(future)

        with open('tasks.out', 'w') as f:
            for i,future in enumerate(futures):
                f.write(f"Waiting for task {i} to complete\n")
                f.write(f"Task {i} completed with result: {future.result()}\n")

    