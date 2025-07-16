# JLCPCB ECAD Data Conversion Script

A Python script to convert Bill of Materials (BOM) and Component Placement List (CPL) files from common ECAD tools into the format required by JLCPCB for their SMT assembly service.

## Features

* **Supported ECAD Tools**:
  * KiCAD
  * Autodesk Fusion 360 / Eagle
* **Converts BOM and CPL files**
* **Smart Format Detection**:
  * Automatically detects and converts different KiCAD BOM formats.
  * For Fusion 360, it automatically finds and merges top and bottom placement files (`_front.csv` and `_back.csv`).
* **Simple and Dependency-Free**: A single-file Python script with no external libraries required.

## Requirements

* Python 3

## Usage

The script is run from the command line. You must specify the input format and at least one file type (BOM or CPL) to convert.

```bash
# General usage
python jlc_convert.py <format> --bom <file>
python jlc_convert.py <format> --pos <file>

# --- Parameters ---
#
# Formats: (One must be specified)
#   --fusion      Input format is Fusion/Eagle
#   --kicad       Input format is KiCAD
#
# Input files: (One or both must be specified)
#   --bom <file>  BOM file to convert
#   --pos <file>  Positions (CPL) file to convert
#
# Output files: (Optional)
#   --out <prefix> Output filename prefix (default: JLC)
```

## Examples

### Fusion 360 / Eagle Examples

Convert a BOM file. This will create `JLC_bom.csv`.  
`python jlc_convert.py --fusion --bom project_bom.csv`

Convert position files and set a custom output name. The script will look for `project_pnp_front.csv` and `project_pnp_back.csv` and merge them into `MyProject_pos.csv`.  
`python jlc_convert.py --fusion --pos project_pnp.csv --out MyProject`

### KiCAD Examples

Convert both BOM and position files, with a custom output name. This will create `MyProject_bom.csv` and `MyProject_pos.csv`.  
`python jlc_convert.py --kicad --bom my_bom.csv --pos my_pos.csv --out MyProject`

## ECAD Export Notes

### KiCAD Notes

For best results, export the BOM from the KiCAD Schematic Editor via **Tools → Generate Bill of Materials...**. The script is compatible with the output of most standard KiCAD BOM export tools.

### Fusion 360 / Eagle Notes

When providing the position file with `--pos`, you can point to either the `_front.csv` or `_back.csv` file. The script will automatically find its counterpart if it exists in the same directory.
