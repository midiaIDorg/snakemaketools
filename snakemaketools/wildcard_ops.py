def update_wildcards(wildcards: dict, wildcard_diffs: dict):
    for wildcard_name in wildcard_diffs:
        assert (
            wildcard_name in wildcards
        ), f"YOU ARE TRYING TO UPDATE A NONEXISTING (FORWARD) WILDCARD {wildcard_name}"
        print(
            f"updating wildcard '{wildcard_name}'.\ndefault={wildcards[wildcard_name]}\nnew={wildcard_diffs[wildcard_name]}\n"
        )
        wildcards[wildcard_name] = wildcard_diffs[wildcard_name]
