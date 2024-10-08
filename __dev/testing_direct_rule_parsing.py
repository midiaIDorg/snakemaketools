import os

from snakemake.api import SnakemakeApi, Workflow
from snakemake.dag import DAG
from snakemake.parser import parse
from snakemake.workflow import Workflow

snakemake_file = (
    "/home/matteo/Projects/midia/pipelines/devel/midia_pipe/workflow/rules/spectra.smk"
)
snakemake_file = "workflow/rules/spectra.smk"


def parse_snakemake(snakemake_file):
    # Initialize a workflow and DAG to capture rules
    workflow = Workflow(snakemake_file)
    workflow.include(snakemake_file)

    # Create a DAG object to retrieve the rules and their details
    dag = DAG(workflow)

    rules_dict = {}

    # Loop through each rule in the workflow
    for rule in workflow.rules:
        rule_name = rule.name
        rule_inputs = list(rule.input)
        rule_outputs = list(rule.output)

        # Build the nested dictionary
        rules_dict[rule_name] = {
            "inputs": rule_inputs,
            "outputs": rule_outputs,
        }

    return rules_dict


# Example usage
snakemake_file = "workflow.smk"
parsed_rules = parse_snakemake(snakemake_file)
print(parsed_rules)


with SnakemakeApi(
    settings.OutputSettings(
        verbose=True,
        show_failed_logs=True,
    ),
) as snakemake_api:
    workflow_api = snakemake_api.workflow(
        storage_settings=settings.StorageSettings(),
        resource_settings=settings.ResourceSettings(),
        snakefile=Path("path/to/Snakefile"),
    )
    dag_api = workflow_api.dag()
    # Go on by calling methods of the dag api.
