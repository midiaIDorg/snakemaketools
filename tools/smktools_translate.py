import argparse
from pathlib import Path
from midia_schemes import MIDIA_scheme

parser = argparse.ArgumentParser(
    description="Precalculate quadrupole settings."
)
parser.add_argument(
    "input_path",
    metavar="<input.ext>",
    help="Path to translate.",
    type=Path,
)

args = parser.parse_args()

import pprint
import snakemaketools
import binascii
import brotli


for part in str(args.input_path).split('/'):
    print(f"{part}:")
    try:
        dec = snakemaketools.decompress(part)
        pprint.pprint(dec)
    except (binascii.Error, brotli.error):
        pass
#print(snakemaketools.decompress(args.input_path))