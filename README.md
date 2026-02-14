# Forge Builder

An interactive ribbon burner forge design tool that generates comprehensive PDF build guides based on your custom chamber dimensions.

## Overview

Forge Builder calculates all engineering specifications for a propane-fired ribbon burner forge and produces a professional PDF build guide including:

- Safety procedures and requirements
- Complete bill of materials with calculated quantities
- Steel cut lists
- Technical diagrams (orthographic views with dimensions)
- Step-by-step assembly instructions
- Refractory lining and curing procedures
- Operation and shutdown procedures
- Flame tuning guide
- Troubleshooting reference
- Maintenance schedule

## Requirements

- Python 3.6+
- ReportLab library

## Quick Start

The easiest way to run Forge Builder is with the included launcher scripts. They automatically check for Python, install dependencies, and run the application.

### Linux / macOS

```bash
chmod +x mac-linux.sh
./mac-linux.sh
```

### Windows

Double-click `windows-run.bat` or run from Command Prompt:

```cmd
windows-run.bat
```

## Manual Installation

If you prefer to install dependencies manually:

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install reportlab
```

## Usage

### Interactive Mode

```bash
python3 ForgeDesigner.py       # Linux/macOS
python ForgeDesigner.py        # Windows
```

You'll be prompted to enter:
- Internal chamber dimensions (width, height, length)
- Insulation thickness
- Door configuration (front only, front+rear, or side loading)

### Command Line Options

```bash
python3 ForgeDesigner.py --debug    # Enable debug output showing all calculations
python3 ForgeDesigner.py --json     # Export specifications to JSON file
```

These options can also be passed through the launcher scripts:

```bash
./mac-linux.sh --debug    # Linux/macOS
windows-run.bat --debug   # Windows
```

## What Gets Calculated

Based on your chamber dimensions, the tool automatically calculates:

| Specification | Formula |
|--------------|---------|
| Burner holes | max(12, volume ÷ 18) — each 1/4" hole covers ~18 cu.in. |
| Blower CFM | (volume ÷ 18) × 1.5 with 25% safety margin |
| Static pressure | 1.5" WC for <500ci, 3.0" WC for larger chambers |
| Refractory | Based on shell volume at 92 lb/ft³ density |
| Door sizing | Proportional to chamber dimensions |
| Steel cut list | All panel dimensions with door cutouts |
| Estimated cost | Base materials + refractory bags |

## Output

The tool generates a PDF named `Forge_Build_Guide_[volume]ci.pdf` containing 15+ pages:

1. Title page with assembly schematic
2. Table of contents
3. Safety requirements & warnings
4. Design overview & specifications
5. Complete bill of materials
6. Steel cut list
7. Forge body construction
8. Ribbon burner assembly
9. Sliding door system
10. Bolted frame details
11. Air & gas systems
12. Refractory lining & curing
13. Operation procedures
14. Flame tuning guide
15. Troubleshooting
16. Maintenance schedule

## Example

```
$ python3 ForgeDesigner.py

======================================================================
   INTERACTIVE FORGE DESIGNER v1.0
   Ribbon Burner Forge Engineering Suite
======================================================================

Enter your desired INTERNAL chamber dimensions.
(Press Enter to accept default values shown in brackets)

  Internal Width  (inches) [6]:  7
  Internal Height (inches) [6]:  8
  Internal Length (inches) [14]: 14

  Insulation Thickness (inches) [2]: 2

  Door Configuration:
    1. Front door only
    2. Front and rear doors
    3. Side loading (one end open)
  Select [1]: 1

[*] Calculating forge specifications...

============================================================
   FORGE DESIGN SUMMARY
============================================================
   Chamber Volume:    784 cubic inches
   External Size:     11.5" × 12.5" × 15.0"
   Ribbon Burner:     45 holes, 12.8" long
   Blower Required:   65 CFM @ 3.0" WC
   Refractory:        1.3 bags Kast-O-Lite 30
   Ceramic Blanket:   5.8 sq ft
   Estimated Cost:    $393.0
============================================================

[*] Generating PDF build guide...

[SUCCESS] Build guide generated: Forge_Build_Guide_784ci.pdf
```

## Safety Notice

⚠️ **This forge operates with combustible gas at high temperatures.** Improper construction or operation can result in fire, explosion, severe burns, carbon monoxide poisoning, or death.

- Always follow all safety procedures in the generated guide
- Never operate indoors or in enclosed spaces
- Leak test all gas connections before use
- Keep a fire extinguisher within reach

## License

MIT License

## Author

Gary Boyce (with AI assistance)
