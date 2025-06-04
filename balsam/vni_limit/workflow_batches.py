from balsam.api import ApplicationDefinition,Job,BatchJob,Site

# This script demonstrates how to run mpiexec tasks in batches of 1000 on Aurora using Balsam.
# This is a workaround for the current bug in palsd that does not return VNIs 
# when mpiexec calls return

class hello_sleep(ApplicationDefinition):
    site = "aurora_testing"

    command_template = "sleep {{sleep_time}} && echo 'sleep for {{sleep_time}} seconds'"

hello_sleep.sync()

# Task parameters
ntasks = 3000
batch_size = 1000 # This is the per-job limit on mpiexecs calls allowed by pals on Aurora
num_batches = ntasks // batch_size + (1 if ntasks % batch_size > 0 else 0)
nodes_per_task = 2
nodes_per_job = 32

print(f"Running {ntasks} tasks in {num_batches} batches of size {batch_size} on {nodes_per_job} nodes per job.")

# Create balsam jobs
jobs = []
for i in range(num_batches):
    batch_tag = f"batch_{i}"
    for j in range(batch_size):
        if len(jobs) < ntasks:
            job = Job( app_id="hello_sleep",
                        site_name="aurora_testing",
                        workdir=f"{batch_tag}/task_{j}",
                        gpus_per_rank=1,
                        ranks_per_node=12,
                        node_packing_count=1,
                        num_nodes=2,
                        parameters={"sleep_time": 10},
                        tags={"batch": batch_tag},)
            jobs.append(job)

jobs = Job.objects.bulk_create(jobs)
for job in jobs:
    if type(job) is not Job:
        print(job)
print(f"Added {len(jobs)} to the site")

# Submit batch jobs for each batch
site = Site.objects.get("aurora_testing")

for i in range(num_batches):
    batch_tag = f"batch_{i}"
    BatchJob.objects.create(site_id=site.id,
                       num_nodes=32,
                       wall_time_min=60,
                       job_mode="mpi",
                       filter_tags={"batch":batch_tag},
                       project="datascience",
                       queue="prod",
    )
print(f"Submitted batch jobs")
