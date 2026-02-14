# Forge Designer - Development Notes

## Project Overview
Interactive ribbon burner forge design application that generates comprehensive PDF build guides based on user-specified chamber dimensions.

## Version History

### v1.1 (2026-02-14)
- Improved diagram style to architectural/engineering standard:
  - Added proper dimension lines with extension lines and arrows
  - Orthographic views (front/side) instead of cartoonish isometric
  - Cross-hatching for section cuts
  - Leader lines with labels
  - Title blocks on all drawings
  - Consistent line weights (1.5pt outlines, 0.5pt details)
- Fixed bolt count: 4 per corner (40-50 total) instead of 6 (60-80)
- Added `draw_dimension_line()` helper function

### v1.0 (2026-02-09)
- Initial release combining functionality from:
  - `generate_forge_pdf.py` - Comprehensive static PDF generator
  - `New_Forge_Build_Generator.py` - Dynamic dimension calculator
- Features:
  - Interactive CLI for dimension input
  - Dynamic engineering calculations (burner holes, CFM, refractory, costs)
  - Scaled technical diagrams
  - 15-section comprehensive PDF output
  - Debug mode (`--debug` flag)
  - JSON export (`--json` flag)

## File Structure
```
~/Projects/Forge/
├── ForgeDesigner.py           # Main application (use this one)
├── generate_forge_pdf.py      # Original static PDF generator (reference)
├── New_Forge_Build_Generator.py  # Original dynamic calculator (reference)
├── DEVNOTES.md                # This file
└── Forge_Build_Guide_*ci.pdf  # Generated output files
```

## Engineering Formulas

### Burner Sizing
- Hole count: `max(12, volume / 18)` - each 1/4" hole covers ~18 cubic inches
- Holes arranged in 3 rows (staggered pattern)
- Burner length: `(holes_per_row × 0.75") + 1.5"`

### Blower Requirements
- CFM required: `(volume / 18) × 1.2`
- CFM recommended: `required × 1.25` (25% safety margin)
- Static pressure: 1.5" WC for <500ci, 3.0" WC for larger

### Refractory Calculation
- Volume = external_dimensions - internal_dimensions
- Weight = volume × 92 lb/ft³ (Kast-O-Lite 30 LI density)
- Bags = weight / 55 lb per bag

### Cost Estimation
- Base: $250 (blower, hardware, miscellaneous)
- Plus: refractory_bags × $110 per bag

## Debug Mode
Run with `--debug` flag to see:
- All calculation steps
- Validation warnings
- Specs dictionary contents

## JSON Export
Run with `--json` flag to export specs to `forge_specs_[volume]ci.json`

## Known Limitations
- Single burner design only (volumes >2000ci may need multiple burners)
- Assumes propane fuel (natural gas would need different calculations)
- Cost estimates are approximate and will vary by region

## Future Enhancements (Ideas)
- [ ] GUI interface (tkinter or web-based)
- [ ] Natural gas option with different orifice sizing
- [ ] Multiple burner support for large forges
- [ ] 3D model export (STL for visualization)
- [ ] Material sourcing links
- [ ] Metric unit support

## Testing
```bash
# Test with defaults
echo -e "\n\n\n\n1" | python3 ForgeDesigner.py

# Test with custom dimensions + debug
echo -e "7\n8\n14\n2\n1" | python3 ForgeDesigner.py --debug

# Test with JSON export
echo -e "6\n6\n14\n2\n1" | python3 ForgeDesigner.py --json
```

## Dependencies
- Python 3.6+
- reportlab (`pip install reportlab`)

## Contact
Generated with AI assistance for Gary's forge building project.
