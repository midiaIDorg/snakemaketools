import pathlib

from snakemake.api import SnakemakeApi
from snakemake.settings.types import OutputSettings, ResourceSettings, StorageSettings
from snakemake.workflow import Workflow

with SnakemakeApi(
    OutputSettings(
        verbose=False,
        show_failed_logs=True,
    ),
) as snakemake_api:
    workflow_api = snakemake_api.workflow(
        storage_settings=StorageSettings(),
        resource_settings=ResourceSettings(),
        snakefile=pathlib.Path("workflow/rules/helpers.smk"),
    )
    dag_api = workflow_api.dag()
    # Go on by calling methods of the dag api.
