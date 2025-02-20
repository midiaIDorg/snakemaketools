### snakemaketools

A Python module with tools to extend snakemake to long pipelines.



## Storing results in a database

For database connections, we make use of Pony ORM.
By default, all csv and json files placed in the desidered outputs folder, in `stats/` subfolder, will be opened and combined into one big JSon file sent out to the DB of choice.

To retrieve results, do the following:


```python
from snakemaketools.results_db import results_db
from snakemaketools.results_db import get_results

results_db.bind(
    provider="mysql",
    host="your_ip",
    user="your_user_name",
    passwd="your_password",
    db="your_database",
)
results_db.generate_mapping()
res = get_results()
```

We leave the parsing of res to you.
For SQLite DBs:

```python
from snakemaketools.results_db import results_db
from snakemaketools.results_db import get_results

results_db.bind(
	provider="sqlite",
	filename="relative_path_to_the_db",
)
results_db.generate_mapping()
res = get_results()
```

Inspect the Results class and [Pony ORM manual](https://docs.ponyorm.org/):
```ipython
from snakemaketools.results_db import Result

??Result
```
This will allow you to make more specific queries then getting all results.


If you want to put more stats in the DB automatically, make sure they are in either ".json", ".csv", ".tsv", ".startrek", or ".parquet" format and select the final path of the file/folder to be such as to lay in the `stats` subfolder, e.g.
```toml
[wishlist] # a list of all targets is available in configs/wishlist.toml

first_gen_fdr_filtered_search_stats = "stats/first_gen_fdr_filtered_search_stats.json"
fasta_stats = "stats/{fasta}.json"
```
Above, `first_gen_fdr_filtered_search_stats` and `fasta_stats` will be saved in the location you want. The `{fasta}` in `"stats/{fasta}.json"` will be replaced directly by entry `fasta` from that configs `[wildcards]`, or by that entry once the the user provided value is parsed out when he is using the `diff_parametrization` mechanism actively.


To empty a DB:

```python
from snakemaketools.results_db import results_db

results_db.drop_all_tables(with_all_data=True)
```