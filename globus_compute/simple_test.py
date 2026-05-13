from globus_compute_sdk import Executor
from globus_compute_sdk.serialize import ComputeSerializer, CombinedCode

# This script is intended to be run from your remote machine

# First, define the function ...
def report_func():
    import sys
    import parsl
    return f"This endpoint is using env {sys.executable}\n Python version {sys.version}\n Parsl version {parsl.__version__}"

# Paste your endpoint id here, e.g.
# Sophia endpoint
# endpoint_id = 'fad4d968-8c9a-45ce-9fb4-60a9ab90be60'
# Edith endpoint
# endpoint_id = 'a01b9350-e57d-4c8e-ad95-b4cb3c4cd1bb'
# Polaris endpoint
endpoint_id = '9a947ba5-f537-4681-acf3-cc66485aadec'

serializer = ComputeSerializer(
    strategy_code=CombinedCode()
)

my_config = {
            'max_retries_on_system_failure': 0,
            'account': 'datascience',
            'queue': 'debug',
            # include the PATH update if your environment settings do not include globus-compute-endpoint
            'config_key': 'source /home/csimpson/polaris/_globus/bin/activate; echo "done!"',
            }


# ... then create the executor, ...
with Executor(endpoint_id=endpoint_id,
                user_endpoint_config=my_config,
                serializer=serializer,
                ) as gce:
    # ... then submit for execution, ...
    future = gce.submit(report_func)
    
    print("Submitted task to remote endpoint, waiting for result...")

    # ... and finally, wait for the result
    print(f"Remote result returned: {future.result()}")