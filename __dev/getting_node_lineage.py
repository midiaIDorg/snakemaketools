%load_ext autoreload
%autoreload 2
from collections import defaultdict
from snakemaketools.db_config import setup_db
from snakemaketools.models import Node
from snakemaketools.models import Storable

db = setup_db()

# node_path = "tmp/configs/mgf_config/70.toml"
node_path = "tmp/mgfs/124/midia.mgf"

Node.GET_LINEAGE(node_path)

