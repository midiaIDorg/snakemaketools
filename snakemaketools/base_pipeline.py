"""
This script is meant to be executed by "scripts/run_pipeline.py"
It provides 'create_path_templates' function.

Wildcards and wishlist are specified seperately.
"""
from pathlib import Path
from types import SimpleNamespace


def create_path_templates(
    wildcards: dict,
    forward_rules: SimpleNamespace,
    path_templates: SimpleNamespace = SimpleNamespace(),
) -> SimpleNamespace:
    # path template roots
    # will be filled by an external script. needs to be this way.

    path_templates.precursor_clustering_script = Path(
        "configs/clustering/{precursor_clusterer}/{precursor_clusterer_version}/{precursor_clusterer_version}.py"
    )
    path_templates.precursor_clustering_config = (
        path_templates.precursor_clustering_script.parent
        / "{precursor_clusterer_config}.toml"
    )

    path_templates.precursor_stats_script = Path(
        "configs/cluster_stats/precursor_stats_script={precursor_stats_script}/{precursor_stats_script}.py"
    )
    path_templates.precursor_stats_config = (
        path_templates.precursor_stats_script.parent
        / "precursor_stats_config={precursor_stats_config}.toml"
    )

    (
        path_templates.fragment_clustering_script,
        path_templates.fragment_clustering_config,
        path_templates.fragment_stats_script,
        path_templates.fragment_stats_config,
    ) = (
        Path(str(path).replace("precursor", "fragment"))
        for path in (
            path_templates.precursor_clustering_script,
            path_templates.precursor_clustering_config,
            path_templates.precursor_stats_script,
            path_templates.precursor_stats_config,
        )
    )

    path_templates.rough_matching_script = Path(
        "configs/matching/{matches}/{matches}.py"
    )
    path_templates.rough_matching_config = (
        path_templates.rough_matching_script.parent / "{matches_config}.toml"
    )

    path_templates.rough_mgf_config = Path("configs/mgf/{rough_mgf_config}.toml")
    path_templates.refined_mgf_config = Path("configs/mgf/{refined_mgf_config}.toml")
    path_templates.first_gen_fasta = Path("fastas/{first_gen_fasta}.fasta")
    path_templates.first_gen_sage = Path(
        "software/sage/{first_gen_search_engine_version}/sage"
    )
    path_templates.first_gen_sage_script = Path(
        "configs/search/sage/run/{first_gen_sage_script}.py"
    )
    path_templates.first_gen_search_config_toml = Path(
        "configs/search/{first_gen_search_engine}/run/{first_gen_search_engine_config}.toml"
    )
    path_templates.first_gen_sage_postprocessing_script = Path(
        "configs/search/{first_gen_search_engine}/postprocessing/{first_gen_search_post}/{first_gen_search_post}.py"
    )
    path_templates.first_gen_sage_postprocessing_config = (
        path_templates.first_gen_sage_postprocessing_script.parent
        / "{first_gen_search_post_config}.toml"
    )

    path_templates.node_refinement_script = Path(
        "configs/refinement/nodes/{node_refinement}/{node_refinement}.py"
    )
    path_templates.node_refinement_config = (
        path_templates.node_refinement_script.parent / "{node_refinement_config}.toml"
    )
    path_templates.edge_refinement_script = Path(
        "configs/refinement/edges/{edge_refinement}/{edge_refinement}.py"
    )
    path_templates.edge_refinement_config = (
        path_templates.edge_refinement_script.parent / "{edge_refinement_config}.toml"
    )

    (
        path_templates.second_gen_fasta,
        path_templates.second_gen_sage_script,
        path_templates.second_gen_search_config_toml,
        path_templates.second_gen_sage_postprocessing_script,
        path_templates.second_gen_sage_postprocessing_config,
        path_templates.second_gen_sage,
    ) = (
        Path(str(first_gen_path).replace("first_gen", "second_gen"))
        for first_gen_path in (
            path_templates.first_gen_fasta,
            path_templates.first_gen_sage_script,
            path_templates.first_gen_search_config_toml,
            path_templates.first_gen_sage_postprocessing_script,
            path_templates.first_gen_sage_postprocessing_config,
            path_templates.first_gen_sage,
        )
    )

    path_templates.dataset = Path("spectra/{dataset}.d")

    # path_templates.ms2rescore = Path("software/ms2rescore/{ms2rescore_version}")
    # path_templates.ms2rescore_venv = Path(f"{path_templates.ms2rescore}/venv_ms2rescore")
    # path_templates.ms2rescore_exe = Path(f"{path_templates.ms2rescore_venv}/bin/ms2rescore")
    # path_templates.ms2rescore_config = Path(
    #     "configs/ms2rescore/{ms2rescore_version}/{ms2rescore_config}.json"
    # )

    path_templates.dataset = forward_rules.new_spectra_path_format(
        path_templates.dataset
    )
    path_templates.dataset_analysis_tdf_hash = forward_rules.hash(
        path_templates.dataset / "analysis.tdf"
    )
    path_templates.dataset_analysis_tdf_bin_hash = forward_rules.hash(
        path_templates.dataset / "analysis.tdf_bin"
    )
    if (
        "substract_baseline_dataset" in wildcards
        and wildcards["substract_baseline_dataset"]
    ):
        path_templates.dataset = forward_rules.substract_background(
            dataset=path_templates.dataset
        )

    path_templates.analysis_tdf = path_templates.dataset / "analysis.tdf"

    path_templates.raw_events_dataset_precursor_marginals = (
        forward_rules.raw_data_marginals_plots_folder(dataset=path_templates.dataset)
    )

    if "calibration" in wildcards and wildcards["calibration"] != "none":
        path_templates.calibration = Path("spectra/{calibration}.d")
        path_templates.calibration = forward_rules.new_spectra_path_format(
            path_templates.calibration
        )
        path_templates.calibration_analysis_tdf_hash = forward_rules.hash(
            path_templates.calibration / "analysis.tdf"
        )
        path_templates.calibration_analysis_tdf_bin_hash = forward_rules.hash(
            path_templates.calibration / "analysis.tdf_bin"
        )
        if wildcards["report_if_dataset_and_calibration_comply"]:
            path_templates.report_on_dataset_calibration_compliance = (
                forward_rules.report_if_dataset_and_calibration_comply(
                    dataset=path_templates.dataset,
                    calibration=path_templates.calibration,
                )
            )
        if (
            "substract_baseline_calibration" in wildcards
            and wildcards["substract_baseline_calibration"]
        ):
            path_templates.calibration = forward_rules.substract_background(
                dataset=path_templates.calibration
            )
        path_templates.calibration_results = forward_rules.new_precompute_calibration(
            calibration=path_templates.calibration
        )

        path_templates.raw_events_calibration_precursor_marginals = (
            forward_rules.raw_data_marginals_plots_folder(
                dataset=path_templates.calibration
            )
        )
    else:
        # path_templates.calibration = "none"
        path_templates.calibration_results = "none"

    path_templates.cached_dataset = forward_rules.cache_tdf(path_templates.dataset)

    (
        path_templates.precursor_clusters,
        path_templates.precursor_clusters_QC,
        path_templates.additional_precursor_cluster_stats,
    ) = forward_rules.cluster(
        dataset=path_templates.dataset
        if wildcards["precursor_clusterer"] == "tims"
        else path_templates.cached_dataset,
        config=path_templates.precursor_clustering_config,
        script=path_templates.precursor_clustering_script,
    )

    (
        path_templates.fragment_clusters,
        path_templates.fragment_clusters_QC,
        path_templates.additional_fragment_cluster_stats,
    ) = forward_rules.cluster(
        dataset=path_templates.dataset
        if wildcards["precursor_clusterer"] == "tims"
        else path_templates.cached_dataset,
        config=path_templates.fragment_clustering_config,
        script=path_templates.fragment_clustering_script,
    )

    path_templates.precursor_stats = forward_rules.get_MS1_stats(
        precursor_clusters=path_templates.precursor_clusters,
        config=path_templates.precursor_stats_config,
        script=path_templates.precursor_stats_script,
        additional_cluster_stats=path_templates.additional_precursor_cluster_stats,
    )

    path_templates.precursor_stats_summary = forward_rules.summarize_table(
        table=path_templates.precursor_stats
    )
    path_templates.precursors_histogram_config = Path(
        "configs/plots/histograms_config.toml"
    )
    path_templates.precursor_stats_histograms = (
        forward_rules.table_columns_to_histograms(
            config=path_templates.precursors_histogram_config,
            table=path_templates.precursor_stats,
        )
    )

    path_templates.fragment_stats = forward_rules.get_MS2_stats(
        script=path_templates.fragment_stats_script,
        fragment_clusters=path_templates.fragment_clusters,
        analysis_tdf=path_templates.analysis_tdf,
        calibration_results=path_templates.calibration_results,
        config=path_templates.fragment_stats_config,
        additional_cluster_stats=path_templates.additional_fragment_cluster_stats,
    )
    path_templates.fragment_stats_summary = forward_rules.summarize_table(
        table=path_templates.fragment_stats
    )

    path_templates.fragments_histogram_config = Path(
        "configs/plots/histograms_config.toml"
    )
    path_templates.fragment_stats_histograms = (
        forward_rules.table_columns_to_histograms(
            config=path_templates.fragments_histogram_config,
            table=path_templates.fragment_stats,
        )
    )

    path_templates.rough_matches = forward_rules.match_precursors_and_fragments(
        script=path_templates.rough_matching_script,
        config=path_templates.rough_matching_config,
        precursor_stats=path_templates.precursor_stats,
        fragment_stats=path_templates.fragment_stats,
        precursor_clusters=path_templates.precursor_clusters,
        fragment_clusters=path_templates.fragment_clusters,
    )

    if (
        "compare_raw_precursor_and_fragment_clusters" in wildcards
        and wildcards["compare_raw_precursor_and_fragment_clusters"]
    ):
        path_templates.score_rough_edges_config = Path(
            "configs/raw_matching/{score_rough_edges_config}.toml"
        )
        path_templates.rough_matches = forward_rules.score_rough_edges(
            edges=path_templates.rough_matches,
            calibration_results=path_templates.calibration_results,
            analysis_tdf=path_templates.analysis_tdf,
            precursor_clusters=path_templates.precursor_clusters,
            fragment_clusters=path_templates.fragment_clusters,
            config=path_templates.score_rough_edges_config,
        )

    if "filter_rough_matches" in wildcards and wildcards["filter_rough_matches"]:
        path_templates.filter_rough_matches_config = Path(
            "configs/edge_filters/{filter_rough_matches_config}.toml"
        )
        path_templates.rough_matches = forward_rules.filter_rough_matches(
            edges=path_templates.rough_matches,
            config=path_templates.filter_rough_matches_config,
        )
    path_templates.rough_matches_summary = forward_rules.summarize_table(
        table=path_templates.rough_matches
    )

    path_templates.rough_mgf = forward_rules.make_sage_mgf(
        precursor_stats=path_templates.precursor_stats,
        fragment_stats=path_templates.fragment_stats,
        edges=path_templates.rough_matches,
        config=path_templates.rough_mgf_config,
    )

    (
        path_templates.first_gen_results_json,
        path_templates.first_gen_results_sage,
        path_templates.first_gen_matched_fragments_sage_parquet,
        path_templates.first_gen_results_sage_pin,
        path_templates.first_gen_sage_stderr,
        path_templates.first_gen_sage_stdout,
        path_templates.first_gen_sage_config_json,
    ) = forward_rules.SAGE_search(
        script=path_templates.first_gen_sage_script,
        mgf=path_templates.rough_mgf,
        fasta=path_templates.first_gen_fasta,
        config=path_templates.first_gen_search_config_toml,
        sage=path_templates.first_gen_sage,
    )

    path_templates.first_gen_results_sage_summary = forward_rules.summarize_table(
        table=path_templates.first_gen_results_sage
    )
    path_templates.first_gen_matched_fragments_sage_parquet_summary = (
        forward_rules.summarize_table(
            table=path_templates.first_gen_matched_fragments_sage_parquet
        )
    )

    # FDR filtering, sanity checks, remapping
    (
        path_templates.first_gen_filtered_sage_precursors,
        path_templates.first_gen_filtered_sage_fragments,
        path_templates.first_gen_matches,
        path_templates.first_gen_postprocess_QC,
    ) = forward_rules.postprocess_SAGE(
        script=path_templates.first_gen_sage_postprocessing_script,
        config=path_templates.first_gen_sage_postprocessing_config,
        found_precursors=path_templates.first_gen_results_sage,
        found_fragments=path_templates.first_gen_matched_fragments_sage_parquet,
        fragment_stats=path_templates.fragment_stats,
        edges=path_templates.rough_matches,
    )
    path_templates.first_gen_filtered_sage_precursors_summary = (
        forward_rules.summarize_table(
            table=path_templates.first_gen_filtered_sage_precursors
        )
    )
    path_templates.first_gen_filtered_sage_fragments_summary = (
        forward_rules.summarize_table(
            table=path_templates.first_gen_filtered_sage_fragments
        )
    )

    path_templates.first_gen_filtered_stats = forward_rules.stat_sage_results(
        sage_precursors=path_templates.first_gen_filtered_sage_precursors,
        sage_fragments=path_templates.first_gen_filtered_sage_fragments,
    )

    # # these include optional m/z recalibration
    (
        path_templates.refined_precursor_stats,
        path_templates.refined_fragment_stats,
        path_templates.mz_recalibrated_distributions,
        path_templates.node_refinement_QC,
    ) = forward_rules.refine_nodes(
        script=path_templates.node_refinement_script,
        config=path_templates.node_refinement_config,
        found_precursors=path_templates.first_gen_filtered_sage_precursors,
        found_edges=path_templates.first_gen_matches,
        uncalibrated_precursor_stats=path_templates.precursor_stats,
        uncalibrated_fragment_stats=path_templates.fragment_stats,
    )

    path_templates.refined_precursor_stats_summary = forward_rules.summarize_table(
        table=path_templates.refined_precursor_stats
    )
    path_templates.refined_fragment_stats_summary = forward_rules.summarize_table(
        table=path_templates.refined_fragment_stats
    )

    if wildcards["mz_recalibration_quantiles"] != "original":
        # here add more options (low upper frag m/z)
        path_templates.second_gen_search_config_toml = forward_rules.refine_sage_config(
            path_templates.second_gen_search_config_toml,
            path_templates.mz_recalibrated_distributions,
            wildcards["mz_recalibration_quantiles"],
        )

    # if wildcards["node_refined_search"]:
    #     path_templates.refined_mgf = forward_rules.make_sage_mgf(
    #         precursor_stats=path_templates.refined_precursor_stats,
    #         fragment_stats=path_templates.refined_fragment_stats,
    #         edges=path_templates.rough_matches,
    #         config=path_templates.rough_mgf_config,
    #     )

    #     (
    #         path_templates.node_refined_results_json,
    #         path_templates.node_refined_results_sage,
    #         path_templates.node_refined_matched_fragments_sage_parquet,
    #         path_templates.node_refined_results_sage_pin,
    #         path_templates.node_refined_sage_stderr,
    #         path_templates.node_refined_sage_stdout,
    #     ) = forward_rules.SAGE_search(
    #         script=path_templates.refined_sage_script,
    #         mgf=path_templates.refined_mgf,
    #         fasta=path_templates.first_gen_fasta,
    #         config=path_templates.second_gen_search_config_toml,
    #         sage=path_templates.second_gen_sage,
    #     )

    (
        path_templates.refined_matches,
        path_templates.refined_matches_stats,
        path_templates.refined_matches_qc,
        path_templates.random_subset_of_edges_used_for_ML_refinement,
    ) = forward_rules.refine_edges(
        # includes drawing edges at random
        script=path_templates.edge_refinement_script,
        config=path_templates.edge_refinement_config,
        precursor_stats=path_templates.refined_precursor_stats,
        fragment_stats=path_templates.refined_fragment_stats,
        all_edges=path_templates.rough_matches,
        filtered_edges=path_templates.first_gen_matches,
    )
    path_templates.refined_matches_summary = forward_rules.summarize_table(
        table=path_templates.refined_matches
    )

    path_templates.refined_mgf = forward_rules.make_sage_mgf(
        precursor_stats=path_templates.refined_precursor_stats,
        fragment_stats=path_templates.refined_fragment_stats,
        edges=path_templates.refined_matches,
        config=path_templates.refined_mgf_config,
    )

    (
        path_templates.second_gen_results_json,
        path_templates.second_gen_results_sage,
        path_templates.second_gen_matched_fragments_sage_parquet,
        path_templates.second_gen_results_sage_pin,
        path_templates.second_gen_sage_stderr,
        path_templates.second_gen_sage_stdout,
        path_templates.second_gen_sage_config_json,
    ) = forward_rules.SAGE_search(
        script=path_templates.second_gen_sage_script,
        mgf=path_templates.refined_mgf,
        fasta=path_templates.second_gen_fasta,
        config=path_templates.second_gen_search_config_toml,
        sage=path_templates.second_gen_sage,
    )

    path_templates.second_gen_results_sage_summary = forward_rules.summarize_table(
        table=path_templates.second_gen_results_sage
    )
    path_templates.second_gen_matched_fragments_sage_parquet_summary = (
        forward_rules.summarize_table(
            table=path_templates.second_gen_matched_fragments_sage_parquet
        )
    )

    (
        path_templates.second_gen_filtered_sage_precursors,
        path_templates.second_gen_filtered_sage_fragments,
        path_templates.second_gen_matches,
        path_templates.second_gen_postprocess_QC,
    ) = forward_rules.postprocess_SAGE(
        script=path_templates.second_gen_sage_postprocessing_script,
        config=path_templates.second_gen_sage_postprocessing_config,
        found_precursors=path_templates.second_gen_results_sage,
        found_fragments=path_templates.second_gen_matched_fragments_sage_parquet,
        fragment_stats=path_templates.refined_fragment_stats,
        edges=path_templates.rough_matches,
    )

    path_templates.second_gen_filtered_sage_precursors_summary = (
        forward_rules.summarize_table(
            table=path_templates.second_gen_filtered_sage_precursors
        )
    )
    path_templates.second_gen_filtered_sage_fragments_summary = (
        forward_rules.summarize_table(
            table=path_templates.second_gen_filtered_sage_fragments
        )
    )

    path_templates.second_gen_filtered_stats = forward_rules.stat_sage_results(
        sage_precursors=path_templates.second_gen_filtered_sage_precursors,
        sage_fragments=path_templates.second_gen_filtered_sage_fragments,
    )

    path_templates.combined_csv_stats = forward_rules.combine_csvs(
        path_templates.first_gen_filtered_stats,
        path_templates.second_gen_filtered_stats,
    )

    # path_templates.second_gen_rescored_findings = forward_rules.rescore(
    #     script=path_templates.second_gen_rescoring_script,
    #     config=path_templates.second_gen_rescoring_config,
    #     pin=path_templates.second_gen_results_sage_pin,
    # )
    return path_templates
