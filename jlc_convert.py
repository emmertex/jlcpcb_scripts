#!/usr/bin/env python3
import argparse
import csv
import os
import sys
from pathlib import Path


def show_help():
    help_text = """
JLC Convert - Convert BOM and Positions files from ECAD to JLCPCB format

Example:
    jlc_convert.py --fusion --bom prj_bom.csv
    jlc_convert.py --kicad --bom prj_bom.csv --pos prj_pos.csv --out project_jlc

Usage:
    jlc_convert.py <format> --bom <file>     - Convert BOM file
    jlc_convert.py <format> --pos <file>     - Convert Positions file(s)
    
Parameters:
    Formats: [One must be specified]
        --fusion      Input format (Fusion/Eagle)
        --kicad       Input format (KiCAD)
    Input files: [One or both must be specified]
        --bom         BOM file to convert
        --pos         Positions file to convert (will automatically find _front/_back pairs if fusion PnP format)
    Output files: [Optional]
        --out         Output filename prefix (optional, default: JLC)
        
Notes:
    For best results with KiCAD: Export BOM from Schematic View → Tools → Generate BOM
"""
    print(help_text)


def convert_fusion_bom(input_file, output_file):
    # Convert Fusion BOM format to JLCPCB BOM format
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            # JLCPCB BOM format: Comment,Designator,Footprint,JLCPCB Part #（optional）
            output_rows = []
            
            for row in reader:
                # Extract relevant fields
                designator = row.get('Part', '')
                value = row.get('Value', '')
                package = row.get('Package', '')
                
                # Skip empty rows or test points
                if not designator or not value:
                    continue
                
                # Use value as comment (component value like "100pF", "1k", etc.)
                comment = value
                footprint = package
                jlcpcb_part = ''  # Optional field, leave empty for now.  TODO Later.
                
                output_rows.append({
                    'Comment': comment,
                    'Designator': designator,
                    'Footprint': footprint,
                    'JLCPCB Part #（optional）': jlcpcb_part
                })
        
        # Write output file
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['Comment', 'Designator', 'Footprint', 'JLCPCB Part #（optional）']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)
        
        print(f"BOM conversion completed: {output_file}")
        print(f"Converted {len(output_rows)} components")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error converting BOM: {e}")
        sys.exit(1)


def convert_kicad_bom(input_file, output_file):
    # Convert KiCAD BOM format to JLCPCB BOM format
    try:
        # First, detect the format by reading the header
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            first_line = infile.readline().strip()
            
        # Determine if this is the enhanced format (comma-delimited with many columns)
        # or the simple format (semicolon-delimited)
        is_enhanced_format = ('Reference' in first_line and 'LCSC #' in first_line)
        
        if is_enhanced_format:
            convert_kicad_bom_enhanced(input_file, output_file)
        else:
            convert_kicad_bom_simple(input_file, output_file)
            
    except Exception as e:
        print(f"Error converting BOM: {e}")
        sys.exit(1)


def convert_kicad_bom_simple(input_file, output_file):
    # Convert simple KiCAD BOM format (semicolon-delimited) to JLCPCB BOM format
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile, delimiter=';')
            
            # JLCPCB BOM format: Comment,Designator,Footprint,JLCPCB Part #（optional）
            output_rows = []
            
            for row in reader:
                # Extract relevant fields
                designators_str = row.get('Designator', '').strip('"')
                value = row.get('Designation', '').strip('"')
                footprint = row.get('Footprint', '').strip('"')
                
                # Skip empty rows
                if not designators_str or not value:
                    continue
                
                # Split comma-separated designators
                designators = [d.strip() for d in designators_str.split(',') if d.strip()]
                
                # Create a row for each designator
                for designator in designators:
                    output_rows.append({
                        'Comment': value,
                        'Designator': designator,
                        'Footprint': footprint,
                        'JLCPCB Part #（optional）': ''
                    })
        
        # Write output file
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['Comment', 'Designator', 'Footprint', 'JLCPCB Part #（optional）']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)
        
        print(f"BOM conversion completed: {output_file}")
        print(f"Converted {len(output_rows)} components")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error converting BOM: {e}")
        sys.exit(1)


def convert_kicad_bom_enhanced(input_file, output_file):
    # Convert enhanced KiCAD BOM format (comma-delimited with detailed columns) to JLCPCB BOM format
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            # JLCPCB BOM format: Comment,Designator,Footprint,JLCPCB Part #（optional）
            output_rows = []
            
            for row in reader:
                # Extract basic fields
                reference = row.get('Reference', '').strip('"')
                value = row.get('Value', '').strip('"')
                footprint = row.get('Footprint', '').strip('"')
                
                # Skip empty rows
                if not reference or not value:
                    continue
                
                # Find LCSC part number using priority order
                lcsc_part = get_priority_value(row, ['LCSC #', 'China LCSC #', 'Alternate LCSC #'])
                
                # Find part number using priority order
                part_number = get_priority_value(row, ['MFG Part Number', 'China MFG PN', 'Alternate MFG Part Number'])
                
                # Generate description/comment
                comment = generate_description(value, part_number, reference)
                
                # Split comma-separated references
                references = [r.strip() for r in reference.split(',') if r.strip()]
                
                # Create a row for each reference
                for ref in references:
                    output_rows.append({
                        'Comment': comment,
                        'Designator': ref,
                        'Footprint': footprint,
                        'JLCPCB Part #（optional）': lcsc_part
                    })
        
        # Write output file
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['Comment', 'Designator', 'Footprint', 'JLCPCB Part #（optional）']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)
        
        print(f"BOM conversion completed: {output_file}")
        print(f"Converted {len(output_rows)} components")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error converting BOM: {e}")
        sys.exit(1)


def get_priority_value(row, column_names):
    # Get the first non-empty value from a list of column names in priority order
    for col_name in column_names:
        value = row.get(col_name, '').strip().strip('"')
        if value and value.lower() not in ['n/a', 'na', '']:
            return value
    return ''


def generate_description(value, part_number, reference):
    # Generate description based on value, part number, and reference with fallback rules
    # If we have both value and part number, combine them
    if value and part_number:
        return f"{value} {part_number}"
    
    # If we only have value but no part number, use designator-based assumptions
    if value:
        ref_prefix = reference.split(',')[0].strip()  # Use first reference if multiple
        
        if ref_prefix.upper().startswith('C'):
            return f"{value} Capacitor"
        elif ref_prefix.upper().startswith('D'):
            return f"{value} Diode"
        elif ref_prefix.upper().startswith('R'):
            return f"{value} Resistor"
        elif ref_prefix.upper().startswith('L'):
            return f"{value} Inductor"
        else:
            return value
    
    # Fallback to just the reference if nothing else
    return reference


def find_pos_files(input_file):
    # Find both front and back PnP files based on input filename
    input_path = Path(input_file)
    base_name = input_path.stem
    directory = input_path.parent
    
    # Remove _front or _back suffix if present
    if base_name.endswith('_front'):
        base_name = base_name[:-6]
    elif base_name.endswith('_back'):
        base_name = base_name[:-5]
    
    # Look for both front and back files
    front_file = directory / f"{base_name}_front.csv"
    back_file = directory / f"{base_name}_back.csv"
    
    files = []
    if front_file.exists():
        files.append(str(front_file))
    if back_file.exists():
        files.append(str(back_file))
    
    # If no _front/_back files found, assume the input file is the only one
    if not files:
        files.append(input_file)
    
    return files


def convert_fusion_pnp(input_files, output_file):
    # Convert Fusion PnP format to JLCPCB Positions format
    try:
        output_rows = []
        
        for input_file in input_files:
            # Determine layer from filename
            layer = "Top" if "_front" in input_file else "Bottom"
            
            with open(input_file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                
                for row in reader:
                    # Extract relevant fields
                    designator = row.get('Name', '')
                    x = row.get('X', '')
                    y = row.get('Y', '')
                    rotation = row.get('Angle', '0')
                    
                    # Skip empty rows
                    if not designator or not x or not y:
                        continue
                    
                    # Format coordinates with mm suffix
                    mid_x = x
                    mid_y = y
                    
                    output_rows.append({
                        'Designator': designator,
                        'Mid X': mid_x,
                        'Mid Y': mid_y,
                        'Layer': layer,
                        'Rotation': rotation
                    })
        
        # Write output file
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)
        
        print(f"Positions conversion completed: {output_file}")
        print(f"Converted {len(output_rows)} components from {len(input_files)} files")
        
    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error converting Positions: {e}")
        sys.exit(1)


def convert_kicad_pnp(input_file, output_file):
    """Convert KiCAD Positions format to JLCPCB Positions format"""
    try:
        output_rows = []
        
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            for row in reader:
                # Extract relevant fields
                designator = row.get('Ref', '').strip('"')
                x = row.get('PosX', '')
                y = row.get('PosY', '')
                rotation = row.get('Rot', '0')
                side = row.get('Side', '').lower().strip('"')
                
                # Skip empty rows
                if not designator or not x or not y:
                    continue
                
                # Map KiCAD side to JLCPCB layer format
                if side == 'top':
                    layer = 'Top'
                elif side == 'bottom':
                    layer = 'Bottom'
                else:
                    layer = 'Top'  # Default to top if unclear
                
                output_rows.append({
                    'Designator': designator,
                    'Mid X': x,
                    'Mid Y': y,
                    'Layer': layer,
                    'Rotation': rotation
                })
        
        # Write output file
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)
        
        print(f"Positions conversion completed: {output_file}")
        print(f"Converted {len(output_rows)} components")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error converting Positions: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Convert BOM and Positions files to JLCPCB format', add_help=False)
    parser.add_argument('--fusion', action='store_true', help='Use Fusion/Eagle input format')
    parser.add_argument('--kicad', action='store_true', help='Use KiCAD input format')
    parser.add_argument('--bom', help='Bill of Materials file to convert')
    parser.add_argument('--pos', help='Positions file to convert')
    parser.add_argument('--out', default='JLC', help='Output filename prefix (default: JLC)')
    
    args = parser.parse_args()
    
    # Show help if no arguments provided
    if len(sys.argv) == 1:
        show_help()
        return
    
    # Check if format is specified
    if not args.fusion and not args.kicad:
        print("Error: Input format must be specified (--fusion or --kicad)")
        show_help()
        sys.exit(1)
    
    # Check that only one format is specified
    if args.fusion and args.kicad:
        print("Error: Only one input format can be specified")
        show_help()
        sys.exit(1)
    
    # Check if either BOM or Pos is specified
    if not args.bom and not args.pos:
        print("Error: Either --bom or --pos must be specified")
        show_help()
        sys.exit(1)
    
    # Process BOM conversion
    if args.bom:
        output_file = f"{args.out}_bom.csv"
        if args.fusion:
            convert_fusion_bom(args.bom, output_file)
        elif args.kicad:
            convert_kicad_bom(args.bom, output_file)
    
    # Process position conversion
    if args.pos:
        output_file = f"{args.out}_pos.csv"
        if args.fusion:
            pos_files = find_pos_files(args.pos)
            convert_fusion_pnp(pos_files, output_file)
        elif args.kicad:
            convert_kicad_pnp(args.pos, output_file)


if __name__ == "__main__":
    main() 