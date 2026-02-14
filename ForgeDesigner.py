#!/usr/bin/env python3
"""
Interactive Forge Designer v1.0
================================
A comprehensive ribbon burner forge design tool that generates complete
PDF build guides based on user-specified chamber dimensions.

Merges dynamic calculations with full documentation including:
- Safety procedures
- Complete BOM with calculated quantities
- Steel cut lists
- Scaled technical diagrams
- Step-by-step assembly instructions
- Operation and troubleshooting guides

Usage:
    python3 ForgeDesigner.py [--debug] [--json]

Requires: reportlab (pip install reportlab)

Author: Gary (with AI assistance)
"""

import sys
import argparse
import json
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, Line, Circle, Polygon, String

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

# Refractory properties (Kast-O-Lite 30 LI)
REFRACTORY_DENSITY_LB_PER_CF = 92  # lb/ft³
REFRACTORY_BAG_SIZE_LB = 55

# Engineering constants
BTU_PER_CUBIC_INCH = 450  # Approximate BTU requirement per ci of chamber
HOLE_COVERAGE_CI = 18     # Each 1/4" hole covers ~18 ci of chamber
MIN_BURNER_HOLES = 12
BURNER_ROWS = 3
HOLE_SPACING = 0.75       # inches between holes

# Cost estimates (USD)
COST_REFRACTORY_PER_BAG = 110
COST_BASE_MATERIALS = 250  # Blower, steel, hardware baseline

# Validation ranges
VALID_WIDTH_RANGE = (3, 12)
VALID_HEIGHT_RANGE = (3, 12)
VALID_LENGTH_RANGE = (6, 48)
VALID_INSULATION_RANGE = (1.0, 3.0)

# Debug state
DEBUG_MODE = False

def debug_log(msg):
    """Print debug messages if debug mode is enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG] {msg}")


# =============================================================================
# USER INPUT MODULE
# =============================================================================

def print_header():
    """Display application header."""
    print("=" * 70)
    print("   INTERACTIVE FORGE DESIGNER v1.0")
    print("   Ribbon Burner Forge Engineering Suite")
    print("=" * 70)
    print()

def get_user_input():
    """
    Collect forge specifications from user via interactive prompts.
    Returns a dictionary of raw user inputs.
    """
    print_header()
    print("Enter your desired INTERNAL chamber dimensions.")
    print("(Press Enter to accept default values shown in brackets)\n")
    
    try:
        # Core dimensions
        width = float(input("  Internal Width  (inches) [6]:  ") or 6)
        height = float(input("  Internal Height (inches) [6]:  ") or 6)
        length = float(input("  Internal Length (inches) [14]: ") or 14)
        
        print()
        insulation = float(input("  Insulation Thickness (inches) [2]: ") or 2)
        
        # Door configuration
        print("\n  Door Configuration:")
        print("    1. Front door only")
        print("    2. Front and rear doors")
        print("    3. Side loading (one end open)")
        door_config = int(input("  Select [1]: ") or 1)
        
        # Validate inputs
        warnings = validate_inputs(width, height, length, insulation)
        if warnings:
            print("\n[!] WARNINGS:")
            for w in warnings:
                print(f"    - {w}")
            proceed = input("\nProceed anyway? (y/n) [y]: ") or "y"
            if proceed.lower() != 'y':
                print("Design cancelled.")
                sys.exit(0)
        
        return {
            'width': width,
            'height': height,
            'length': length,
            'insulation': insulation,
            'door_config': door_config
        }
        
    except ValueError:
        print("\n[ERROR] Invalid input. Please enter numbers only.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nDesign cancelled.")
        sys.exit(0)

def validate_inputs(width, height, length, insulation):
    """
    Validate user inputs against reasonable ranges.
    Returns list of warning messages.
    """
    warnings = []
    
    if not (VALID_WIDTH_RANGE[0] <= width <= VALID_WIDTH_RANGE[1]):
        warnings.append(f"Width {width}\" outside typical range ({VALID_WIDTH_RANGE[0]}-{VALID_WIDTH_RANGE[1]}\")")
    
    if not (VALID_HEIGHT_RANGE[0] <= height <= VALID_HEIGHT_RANGE[1]):
        warnings.append(f"Height {height}\" outside typical range ({VALID_HEIGHT_RANGE[0]}-{VALID_HEIGHT_RANGE[1]}\")")
    
    if not (VALID_LENGTH_RANGE[0] <= length <= VALID_LENGTH_RANGE[1]):
        warnings.append(f"Length {length}\" outside typical range ({VALID_LENGTH_RANGE[0]}-{VALID_LENGTH_RANGE[1]}\")")
    
    if not (VALID_INSULATION_RANGE[0] <= insulation <= VALID_INSULATION_RANGE[1]):
        warnings.append(f"Insulation {insulation}\" outside typical range ({VALID_INSULATION_RANGE[0]}-{VALID_INSULATION_RANGE[1]}\")")
    
    volume = width * height * length
    if volume < 100:
        warnings.append(f"Very small chamber ({volume} ci) - may have difficulty heating evenly")
    if volume > 2000:
        warnings.append(f"Very large chamber ({volume} ci) - may need multiple burners")
    
    debug_log(f"Validation complete: {len(warnings)} warnings")
    return warnings


# =============================================================================
# ENGINEERING CALCULATOR
# =============================================================================

def calculate_forge_specs(user_input):
    """
    Calculate all engineering specifications from user input.
    Returns comprehensive specs dictionary.
    """
    w = user_input['width']
    h = user_input['height']
    l = user_input['length']
    ins = user_input['insulation']
    door_config = user_input['door_config']
    
    # Internal volume
    internal_volume = w * h * l
    debug_log(f"Internal volume: {internal_volume} ci")
    
    # External dimensions (insulation on all sides + 1" for plates/frame)
    ext_w = w + (ins * 2) + 0.5  # 1/4" plate each side
    ext_h = h + (ins * 2) + 0.5
    ext_l = l + 1.0  # End plates
    
    debug_log(f"External dimensions: {ext_w}\" x {ext_h}\" x {ext_l}\"")
    
    # Burner calculations
    total_holes = max(MIN_BURNER_HOLES, round(internal_volume / HOLE_COVERAGE_CI))
    holes_per_row = round(total_holes / BURNER_ROWS)
    total_holes = holes_per_row * BURNER_ROWS  # Ensure divisible by rows
    
    burner_length = round((holes_per_row * HOLE_SPACING) + 1.5, 1)
    burner_width = 3.0  # Standard 3x3 square tube
    
    debug_log(f"Burner: {total_holes} holes ({holes_per_row} x {BURNER_ROWS}), {burner_length}\" long")
    
    # Blower/CFM calculations
    cfm_required = round((internal_volume / HOLE_COVERAGE_CI) * 1.2)
    cfm_recommended = round(cfm_required * 1.25)  # 25% safety margin
    static_pressure = "1.5" if internal_volume < 500 else "3.0"
    
    debug_log(f"Blower: {cfm_required} CFM required, {cfm_recommended} CFM recommended")
    
    # Refractory calculations
    external_volume_ci = ext_w * ext_h * ext_l
    refractory_volume_ci = external_volume_ci - internal_volume
    refractory_volume_cf = refractory_volume_ci / 1728  # Convert to cubic feet
    refractory_weight_lb = refractory_volume_cf * REFRACTORY_DENSITY_LB_PER_CF
    refractory_bags = round(refractory_weight_lb / REFRACTORY_BAG_SIZE_LB, 1)
    
    debug_log(f"Refractory: {refractory_bags} bags ({refractory_weight_lb:.1f} lb)")
    
    # Door sizing (proportional to chamber)
    front_door_w = round(w * 0.85, 1)  # 85% of internal width
    front_door_h = round(h * 0.85, 1)
    
    if door_config == 2:  # Front + rear
        rear_door_w = round(w * 0.7, 1)
        rear_door_h = round(h * 0.75, 1)
    else:
        rear_door_w = 0
        rear_door_h = 0
    
    # Steel cut list
    steel_cuts = calculate_steel_cuts(ext_w, ext_h, ext_l, front_door_w, front_door_h)
    
    # Cost estimation
    estimated_cost = round(COST_BASE_MATERIALS + (refractory_bags * COST_REFRACTORY_PER_BAG), 2)
    
    # BTU estimation
    btu_required = round(internal_volume * BTU_PER_CUBIC_INCH)
    
    # Ceramic blanket calculation (walls and ceiling)
    blanket_sqft = round(((ext_l * ext_h * 2) + (ext_l * ext_w) + (ext_w * ext_h * 2)) / 144, 1)
    
    # IFB count for floor
    ifb_floor_count = max(2, round((ext_l * ext_w) / 72))  # 9x4.5" bricks
    ifb_door_count = 4 if door_config == 1 else 6
    
    specs = {
        # User inputs
        'internal_w': w,
        'internal_h': h,
        'internal_l': l,
        'insulation': ins,
        'door_config': door_config,
        
        # Calculated dimensions
        'internal_volume': internal_volume,
        'external_w': ext_w,
        'external_h': ext_h,
        'external_l': ext_l,
        
        # Burner specs
        'burner_holes': total_holes,
        'holes_per_row': holes_per_row,
        'burner_rows': BURNER_ROWS,
        'burner_length': burner_length,
        'burner_width': burner_width,
        
        # Blower specs
        'cfm_required': cfm_required,
        'cfm_recommended': cfm_recommended,
        'static_pressure': static_pressure,
        
        # Refractory
        'refractory_bags': refractory_bags,
        'refractory_weight': round(refractory_weight_lb, 1),
        'blanket_sqft': blanket_sqft,
        'ifb_floor': ifb_floor_count,
        'ifb_doors': ifb_door_count,
        
        # Doors
        'front_door_w': front_door_w,
        'front_door_h': front_door_h,
        'rear_door_w': rear_door_w,
        'rear_door_h': rear_door_h,
        
        # Steel
        'steel_cuts': steel_cuts,
        
        # Performance
        'btu_required': btu_required,
        'estimated_cost': estimated_cost,
        
        # Metadata
        'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    
    debug_log(f"Specs calculation complete: {len(specs)} parameters")
    return specs

def calculate_steel_cuts(ext_w, ext_h, ext_l, door_w, door_h):
    """Generate steel plate cut list based on dimensions."""
    cuts = [
        {'name': 'Side Panels', 'qty': 2, 'w': ext_l, 'h': ext_h, 'thickness': '1/4"'},
        {'name': 'Top Panel', 'qty': 1, 'w': ext_l, 'h': ext_w, 'thickness': '1/4"'},
        {'name': 'Bottom Panel', 'qty': 1, 'w': ext_l, 'h': ext_w, 'thickness': '1/4"'},
        {'name': 'Front End Panel', 'qty': 1, 'w': ext_w, 'h': ext_h, 'thickness': '1/4"',
         'note': f'Cut {door_w}"x{door_h}" door opening'},
        {'name': 'Rear End Panel', 'qty': 1, 'w': ext_w, 'h': ext_h, 'thickness': '1/4"'},
    ]
    
    # Angle iron for frame
    angle_cuts = [
        {'name': 'Corner Posts', 'qty': 4, 'length': ext_h, 'size': '2" x 2" x 1/8"'},
        {'name': 'Top/Bottom Rails', 'qty': 8, 'length': ext_l - 4, 'size': '2" x 2" x 1/8"'},
        {'name': 'End Rails', 'qty': 8, 'length': ext_w - 4, 'size': '2" x 2" x 1/8"'},
    ]
    
    return {'plates': cuts, 'angle_iron': angle_cuts}


# =============================================================================
# DYNAMIC DIAGRAM GENERATOR
# =============================================================================

def draw_dimension_line(d, x1, y1, x2, y2, label, offset=15, fontsize=8):
    """Draw a proper dimension line with arrows and label."""
    import math
    # Calculate angle and perpendicular offset
    dx, dy = x2 - x1, y2 - y1
    length = math.sqrt(dx*dx + dy*dy)
    if length == 0:
        return
    ux, uy = dx/length, dy/length  # Unit vector along line
    px, py = -uy, ux  # Perpendicular unit vector
    
    # Offset points for dimension line
    ox1, oy1 = x1 + px*offset, y1 + py*offset
    ox2, oy2 = x2 + px*offset, y2 + py*offset
    
    # Extension lines
    d.add(Line(x1, y1, ox1, oy1, strokeColor=colors.black, strokeWidth=0.5))
    d.add(Line(x2, y2, ox2, oy2, strokeColor=colors.black, strokeWidth=0.5))
    
    # Main dimension line
    d.add(Line(ox1, oy1, ox2, oy2, strokeColor=colors.black, strokeWidth=0.5))
    
    # Arrow heads (simple ticks at 45 degrees)
    arrow_size = 4
    # Start arrow
    d.add(Line(ox1, oy1, ox1 + ux*arrow_size + px*arrow_size*0.3, oy1 + uy*arrow_size + py*arrow_size*0.3, 
               strokeColor=colors.black, strokeWidth=0.75))
    d.add(Line(ox1, oy1, ox1 + ux*arrow_size - px*arrow_size*0.3, oy1 + uy*arrow_size - py*arrow_size*0.3, 
               strokeColor=colors.black, strokeWidth=0.75))
    # End arrow
    d.add(Line(ox2, oy2, ox2 - ux*arrow_size + px*arrow_size*0.3, oy2 - uy*arrow_size + py*arrow_size*0.3, 
               strokeColor=colors.black, strokeWidth=0.75))
    d.add(Line(ox2, oy2, ox2 - ux*arrow_size - px*arrow_size*0.3, oy2 - uy*arrow_size - py*arrow_size*0.3, 
               strokeColor=colors.black, strokeWidth=0.75))
    
    # Label at midpoint
    mx, my = (ox1 + ox2) / 2, (oy1 + oy2) / 2
    d.add(String(mx - len(label)*2, my + 3, label, fontSize=fontsize, fillColor=colors.black))

def draw_forge_body_isometric(specs, width_px=450, height_px=320):
    """Create architectural orthographic views of forge body."""
    d = Drawing(width_px, height_px)
    
    w = specs['external_w']
    h = specs['external_h']
    l = specs['external_l']
    door_w = specs['front_door_w']
    door_h = specs['front_door_h']
    ins = specs['insulation']
    
    # Scale to fit - use orthographic front and side views
    scale = min(12, 120 / max(w, h), 80 / l)
    
    # === FRONT VIEW (left side) ===
    fx, fy = 60, 80  # Front view origin
    fw, fh = w * scale, h * scale
    
    # Outer shell
    d.add(Rect(fx, fy, fw, fh, fillColor=None, strokeColor=colors.black, strokeWidth=1.5))
    
    # Inner chamber (dashed)
    ins_px = ins * scale
    d.add(Rect(fx + ins_px, fy + ins_px, fw - 2*ins_px, fh - 2*ins_px, 
               fillColor=colors.Color(0.95, 0.95, 0.95), strokeColor=colors.black, 
               strokeWidth=0.5, strokeDashArray=[3, 2]))
    
    # Door opening
    door_px_w = door_w * scale
    door_px_h = door_h * scale
    door_x = fx + (fw - door_px_w) / 2
    door_y = fy + (fh - door_px_h) / 2
    d.add(Rect(door_x, door_y, door_px_w, door_px_h, fillColor=colors.white, 
               strokeColor=colors.black, strokeWidth=1))
    
    # Cross-hatch the insulation area (top strip)
    hatch_spacing = 6
    for i in range(int(fw / hatch_spacing) + 5):
        hx = fx + i * hatch_spacing
        # Top insulation hatch
        d.add(Line(hx, fy + fh - ins_px, hx + ins_px, fy + fh, 
                   strokeColor=colors.grey, strokeWidth=0.3))
    
    # Front view dimensions
    draw_dimension_line(d, fx, fy, fx + fw, fy, f'{w:.1f}"', offset=-18)
    draw_dimension_line(d, fx, fy, fx, fy + fh, f'{h:.1f}"', offset=-18)
    
    # Door dimension
    d.add(String(door_x + door_px_w/2 - 15, door_y + door_px_h/2, f'{door_w:.1f}"×{door_h:.1f}"', 
                 fontSize=7, fillColor=colors.black))
    
    d.add(String(fx + fw/2 - 25, fy + fh + 25, 'FRONT VIEW', fontSize=9, fillColor=colors.black))
    
    # === SIDE VIEW (right side) ===
    sx, sy = 260, 80  # Side view origin
    sw, sh = l * scale * 0.6, h * scale  # Compressed for fit
    
    # Outer shell
    d.add(Rect(sx, sy, sw, sh, fillColor=None, strokeColor=colors.black, strokeWidth=1.5))
    
    # Inner chamber
    ins_px_side = ins * scale * 0.6
    d.add(Rect(sx + ins_px_side, sy + ins_px, sw - 2*ins_px_side, sh - 2*ins_px, 
               fillColor=colors.Color(0.95, 0.95, 0.95), strokeColor=colors.black, 
               strokeWidth=0.5, strokeDashArray=[3, 2]))
    
    # Burner position indicator (on top)
    burner_x = sx + sw * 0.4
    d.add(Line(burner_x, sy + sh, burner_x, sy + sh + 15, strokeColor=colors.black, strokeWidth=1))
    d.add(Line(burner_x - 5, sy + sh + 15, burner_x + 5, sy + sh + 15, strokeColor=colors.black, strokeWidth=1))
    d.add(String(burner_x - 20, sy + sh + 20, 'BURNER', fontSize=6, fillColor=colors.black))
    
    # Side view dimensions
    draw_dimension_line(d, sx, sy, sx + sw, sy, f'{l:.1f}"', offset=-18)
    
    d.add(String(sx + sw/2 - 20, sy + sh + 25, 'SIDE VIEW', fontSize=9, fillColor=colors.black))
    
    # Title block
    d.add(Line(10, 15, width_px - 10, 15, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(width_px/2 - 80, 5, f'FORGE BODY - EXTERNAL: {w:.1f}" × {h:.1f}" × {l:.1f}"', 
                 fontSize=9, fillColor=colors.black))
    
    return d

def draw_burner_detail(specs, width_px=450, height_px=280):
    """Create architectural section view of ribbon burner."""
    d = Drawing(width_px, height_px)
    
    burner_len = specs['burner_length']
    holes = specs['burner_holes']
    holes_per_row = specs['holes_per_row']
    rows = specs['burner_rows']
    
    # === LONGITUDINAL SECTION (top) ===
    scale = min(16, 200 / burner_len)
    x, y = 80, 160
    w = burner_len * scale
    h = 45
    
    # Outer housing (3x3 square tube)
    d.add(Rect(x, y, w, h, fillColor=None, strokeColor=colors.black, strokeWidth=1.5))
    
    # Inner cavity
    wall = 4
    d.add(Rect(x + wall, y + wall, w - 2*wall, h - 2*wall, fillColor=colors.white, 
               strokeColor=colors.black, strokeWidth=0.5))
    
    # Refractory layer at bottom
    refr_h = 15
    d.add(Rect(x + wall, y + wall, w - 2*wall, refr_h, fillColor=colors.Color(0.9, 0.85, 0.7), 
               strokeColor=colors.black, strokeWidth=0.5))
    
    # Cross-hatch the refractory
    for i in range(int(w / 8) + 2):
        hx = x + wall + i * 8
        if hx < x + w - wall:
            d.add(Line(hx, y + wall, min(hx + refr_h, x + w - wall), y + wall + min(refr_h, x + w - wall - hx), 
                       strokeColor=colors.grey, strokeWidth=0.3))
    
    # Air inlet pipe (left side)
    pipe_w, pipe_h = 25, 18
    pipe_y = y + h/2 - pipe_h/2
    d.add(Rect(x - pipe_w, pipe_y, pipe_w, pipe_h, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    d.add(Line(x - pipe_w, pipe_y, x, pipe_y, strokeColor=colors.black, strokeWidth=0.5))
    d.add(Line(x - pipe_w, pipe_y + pipe_h, x, pipe_y + pipe_h, strokeColor=colors.black, strokeWidth=0.5))
    
    # Gas injection point
    gas_x = x - pipe_w/2
    gas_y = pipe_y + pipe_h
    d.add(Line(gas_x, gas_y, gas_x, gas_y + 12, strokeColor=colors.black, strokeWidth=1))
    d.add(Circle(gas_x, gas_y + 12, 2, fillColor=colors.black, strokeColor=colors.black))
    
    # Internal baffle
    baffle_x = x + 20
    d.add(Line(baffle_x, y + wall + refr_h, baffle_x, y + h - wall, 
               strokeColor=colors.black, strokeWidth=1, strokeDashArray=[4, 2]))
    
    # Dimension lines
    draw_dimension_line(d, x, y + h + 5, x + w, y + h + 5, f'{burner_len}"', offset=12)
    draw_dimension_line(d, x + w + 5, y, x + w + 5, y + h, '3"', offset=12)
    
    # Labels with leader lines
    d.add(Line(x - pipe_w/2, pipe_y - 5, x - pipe_w/2, pipe_y - 20, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(x - pipe_w - 15, pipe_y - 25, '1.5" AIR', fontSize=7, fillColor=colors.black))
    
    d.add(Line(gas_x + 5, gas_y + 12, gas_x + 25, gas_y + 20, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(gas_x + 27, gas_y + 17, '1/4" GAS', fontSize=7, fillColor=colors.black))
    
    d.add(String(x + w/2 - 25, y + wall + 5, 'REFRACTORY', fontSize=6, fillColor=colors.black))
    
    # Section indicator
    d.add(String(x - 15, y + h/2, 'A', fontSize=10, fillColor=colors.black))
    d.add(String(x + w + 8, y + h/2, 'A', fontSize=10, fillColor=colors.black))
    
    d.add(String(x + w/2 - 40, y + h + 35, 'SECTION A-A: LONGITUDINAL', fontSize=8, fillColor=colors.black))
    
    # === BOTTOM VIEW (hole pattern) ===
    bx, by = 80, 40
    bw, bh = w, 50
    
    d.add(Rect(bx, by, bw, bh, fillColor=colors.Color(0.9, 0.85, 0.7), strokeColor=colors.black, strokeWidth=1))
    
    # Draw flame holes in pattern
    hole_radius = 2.5
    hole_spacing_px = (bw - 20) / max(1, holes_per_row - 1)
    row_spacing = bh / (rows + 1)
    
    for row in range(rows):
        row_offset = (row % 2) * (hole_spacing_px / 2) * 0.3  # Stagger
        for col in range(holes_per_row):
            hole_x = bx + 10 + col * hole_spacing_px + row_offset
            hole_y = by + row_spacing * (row + 1)
            if hole_x < bx + bw - 5:
                d.add(Circle(hole_x, hole_y, hole_radius, fillColor=colors.black, strokeColor=colors.black))
    
    d.add(String(bx + bw/2 - 50, by - 12, f'BOTTOM VIEW: {holes} × 1/4" HOLES ({rows}×{holes_per_row})', 
                 fontSize=7, fillColor=colors.black))
    
    # Title block
    d.add(Line(10, 15, width_px - 10, 15, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(width_px/2 - 60, 5, 'RIBBON BURNER ASSEMBLY', fontSize=9, fillColor=colors.black))
    
    return d

def draw_door_system(specs, width_px=400, height_px=280):
    """Create architectural detail of sliding door system."""
    d = Drawing(width_px, height_px)
    
    door_w = specs['front_door_w']
    door_h = specs['front_door_h']
    ext_w = specs['external_w']
    ext_h = specs['external_h']
    
    # Scale to fit
    scale = min(7, 130 / max(ext_w, ext_h))
    
    # === FRONT ELEVATION ===
    x, y = 50, 60
    face_w = ext_w * scale
    face_h = ext_h * scale
    opening_w = door_w * scale
    opening_h = door_h * scale
    
    # Forge front face outline
    d.add(Rect(x, y, face_w, face_h, fillColor=None, strokeColor=colors.black, strokeWidth=1.5))
    
    # Door opening (centered)
    open_x = x + (face_w - opening_w) / 2
    open_y = y + (face_h - opening_h) / 2
    d.add(Rect(open_x, open_y, opening_w, opening_h, fillColor=colors.white, strokeColor=colors.black, strokeWidth=1))
    
    # Hatch the forge face (section lines)
    for i in range(int(face_w / 10) + 3):
        hx = x + i * 10
        if hx < x + face_w:
            # Only draw where not opening
            if hx < open_x or hx > open_x + opening_w:
                d.add(Line(hx, y, hx + 5, y + 5, strokeColor=colors.grey, strokeWidth=0.25))
    
    # Track rod (above opening)
    rod_y = y + face_h + 8
    track_extend = 30
    d.add(Line(open_x - track_extend, rod_y, open_x + opening_w + track_extend, rod_y, 
               strokeColor=colors.black, strokeWidth=1.5))
    # Rod end circles
    d.add(Circle(open_x - track_extend, rod_y, 3, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    d.add(Circle(open_x + opening_w + track_extend, rod_y, 3, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    
    # Rod supports (triangular brackets)
    for bracket_x in [open_x - 5, open_x + opening_w + 5]:
        d.add(Line(bracket_x, y + face_h, bracket_x, rod_y, strokeColor=colors.black, strokeWidth=1))
        d.add(Line(bracket_x - 5, y + face_h, bracket_x + 5, y + face_h, strokeColor=colors.black, strokeWidth=1))
    
    # Dimensions
    draw_dimension_line(d, open_x, open_y - 5, open_x + opening_w, open_y - 5, f'{door_w:.1f}"', offset=-15)
    draw_dimension_line(d, open_x - 5, open_y, open_x - 5, open_y + opening_h, f'{door_h:.1f}"', offset=-15)
    
    d.add(String(x + face_w/2 - 30, y + face_h + 25, 'FRONT ELEVATION', fontSize=8, fillColor=colors.black))
    
    # === SECTION DETAIL (right side) ===
    sx, sy = 250, 60
    
    # Forge wall section
    wall_t = 15
    d.add(Rect(sx, sy, wall_t, face_h, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    # Cross hatch the wall
    for i in range(int(face_h / 6) + 2):
        hy = sy + i * 6
        if hy < sy + face_h:
            d.add(Line(sx, hy, sx + wall_t, hy + wall_t*0.7, strokeColor=colors.grey, strokeWidth=0.3))
    
    # Track rod (circle in section)
    rod_sx = sx + wall_t + 20
    rod_sy = sy + face_h + 8
    d.add(Circle(rod_sx, rod_sy, 4, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    d.add(String(rod_sx + 8, rod_sy - 3, '1/2" ROD', fontSize=6, fillColor=colors.black))
    
    # Door hanger
    hanger_w = 12
    d.add(Rect(rod_sx - hanger_w/2, rod_sy - 15, hanger_w, 12, fillColor=None, strokeColor=colors.black, strokeWidth=0.75))
    d.add(Line(rod_sx, rod_sy - 3, rod_sx, rod_sy - 15, strokeColor=colors.black, strokeWidth=0.5))
    
    # Door panel (firebrick in frame)
    door_t = 25
    door_h_px = opening_h
    d.add(Rect(rod_sx - hanger_w/2, sy + (face_h - door_h_px)/2, door_t, door_h_px, 
               fillColor=None, strokeColor=colors.black, strokeWidth=1))
    # Firebrick inside
    d.add(Rect(rod_sx - hanger_w/2 + 3, sy + (face_h - door_h_px)/2 + 3, door_t - 6, door_h_px - 6, 
               fillColor=colors.Color(0.85, 0.75, 0.6), strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(rod_sx - 5, sy + face_h/2, 'IFB', fontSize=6, fillColor=colors.black))
    
    # Movement arrow
    arrow_y = sy + 20
    d.add(Line(rod_sx + door_t, arrow_y, rod_sx + door_t + 25, arrow_y, strokeColor=colors.black, strokeWidth=0.75))
    d.add(Line(rod_sx + door_t + 25, arrow_y, rod_sx + door_t + 20, arrow_y - 3, strokeColor=colors.black, strokeWidth=0.75))
    d.add(Line(rod_sx + door_t + 25, arrow_y, rod_sx + door_t + 20, arrow_y + 3, strokeColor=colors.black, strokeWidth=0.75))
    d.add(String(rod_sx + door_t + 5, arrow_y + 8, 'SLIDE', fontSize=6, fillColor=colors.black))
    
    d.add(String(sx + 30, sy + face_h + 25, 'SECTION B-B', fontSize=8, fillColor=colors.black))
    
    # Title block
    d.add(Line(10, 15, width_px - 10, 15, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(width_px/2 - 70, 5, 'SLIDING FIREBRICK DOOR DETAIL', fontSize=9, fillColor=colors.black))
    
    return d

def draw_assembly_overview(specs, width_px=480, height_px=350):
    """Create schematic assembly overview with proper piping."""
    d = Drawing(width_px, height_px)
    
    pipe_thickness = 6  # Visual thickness for 1.5" pipe representation
    gas_pipe_thickness = 3  # Smaller for 1/4" gas line
    
    # Main forge body - side elevation
    forge_x, forge_y = 140, 140
    forge_w, forge_h = 160, 70
    
    # Forge shell (double line for wall thickness)
    d.add(Rect(forge_x, forge_y, forge_w, forge_h, fillColor=None, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Rect(forge_x + 5, forge_y + 5, forge_w - 10, forge_h - 10, fillColor=colors.white, 
               strokeColor=colors.black, strokeWidth=0.5, strokeDashArray=[2, 2]))
    
    # Stand legs
    leg_h = 70
    d.add(Line(forge_x + 12, forge_y, forge_x + 12, forge_y - leg_h, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(forge_x + forge_w - 12, forge_y, forge_x + forge_w - 12, forge_y - leg_h, strokeColor=colors.black, strokeWidth=1.5))
    # Cross brace
    d.add(Line(forge_x + 12, forge_y - leg_h + 12, forge_x + forge_w - 12, forge_y - leg_h + 12, 
               strokeColor=colors.black, strokeWidth=1))
    # Feet
    d.add(Line(forge_x + 2, forge_y - leg_h, forge_x + 22, forge_y - leg_h, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(forge_x + forge_w - 22, forge_y - leg_h, forge_x + forge_w - 2, forge_y - leg_h, strokeColor=colors.black, strokeWidth=1.5))
    
    # Burner on top
    burner_w = 50
    burner_h = 22
    burner_x = forge_x + forge_w/2 - burner_w/2
    burner_y = forge_y + forge_h
    d.add(Rect(burner_x, burner_y, burner_w, burner_h, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    
    # === AIR PIPE (1.5" - shown as double lines) ===
    # Pipe runs from blower (lower right) up and over to burner
    # Blower is positioned lower than forge, to the right
    blower_x = forge_x + forge_w + 100
    blower_y = forge_y - 30  # Lower than forge bottom
    
    # Air pipe path: blower -> up -> horizontal -> down into burner
    pipe_start_x = blower_x - 18  # Blower outlet
    pipe_start_y = blower_y
    
    # Vertical rise from blower
    pipe_rise_top = burner_y + burner_h + 15
    
    # Elbow position - above burner center
    elbow_x = burner_x + burner_w/2
    
    # Draw pipe as parallel lines (showing tube walls)
    # Vertical section from blower up
    d.add(Line(pipe_start_x, pipe_start_y, pipe_start_x, pipe_rise_top, strokeColor=colors.black, strokeWidth=1))
    d.add(Line(pipe_start_x - pipe_thickness, pipe_start_y, pipe_start_x - pipe_thickness, pipe_rise_top, strokeColor=colors.black, strokeWidth=1))
    
    # Top elbow (vertical to horizontal) - proper squared corner
    d.add(Line(pipe_start_x - pipe_thickness, pipe_rise_top, pipe_start_x, pipe_rise_top, strokeColor=colors.black, strokeWidth=1))
    
    # Horizontal section running left toward elbow down to burner
    # Top line of horizontal pipe (extends all the way to outer edge of elbow)
    d.add(Line(pipe_start_x - pipe_thickness, pipe_rise_top, elbow_x, pipe_rise_top, strokeColor=colors.black, strokeWidth=1))
    # Bottom line of horizontal pipe (stops at inner corner)
    d.add(Line(pipe_start_x - pipe_thickness, pipe_rise_top - pipe_thickness, elbow_x + pipe_thickness, pipe_rise_top - pipe_thickness, strokeColor=colors.black, strokeWidth=1))
    
    # Elbow down into burner - proper squared 90-degree corner
    # Outer line (left side) goes straight down from end of top horizontal line
    d.add(Line(elbow_x, pipe_rise_top, elbow_x, burner_y + burner_h, strokeColor=colors.black, strokeWidth=1))
    # Inner line (right side) goes down from where bottom horizontal ended
    d.add(Line(elbow_x + pipe_thickness, pipe_rise_top - pipe_thickness, elbow_x + pipe_thickness, burner_y + burner_h, strokeColor=colors.black, strokeWidth=1))
    
    # === GAS PIPE (1/4" - injects into vertical air pipe section) ===
    # Propane tank position (rear/right side, beyond blower)
    tank_x = blower_x + 35
    tank_y = blower_y - 30
    tank_w, tank_h = 18, 40
    d.add(Rect(tank_x, tank_y, tank_w, tank_h, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    # Tank valve on top
    d.add(Rect(tank_x + tank_w/2 - 3, tank_y + tank_h, 6, 6, fillColor=None, strokeColor=colors.black, strokeWidth=0.75))
    
    # Gas injection point - T into the vertical air pipe section
    gas_inject_y = blower_y + 50  # Above the blower, on vertical pipe run
    
    # Gas line path: tank -> UP -> horizontal LEFT (above blower) -> DOWN to T into air pipe
    gas_rise_y = blower_y + 55  # Height to clear above the blower
    
    # Vertical rise from tank
    d.add(Line(tank_x + tank_w/2, tank_y + tank_h + 6, tank_x + tank_w/2, gas_rise_y, strokeColor=colors.black, strokeWidth=0.75))
    d.add(Line(tank_x + tank_w/2 - gas_pipe_thickness, tank_y + tank_h + 6, tank_x + tank_w/2 - gas_pipe_thickness, gas_rise_y, strokeColor=colors.black, strokeWidth=0.75))
    
    # Horizontal run above blower to above air pipe
    d.add(Line(tank_x + tank_w/2, gas_rise_y, pipe_start_x + 5, gas_rise_y, strokeColor=colors.black, strokeWidth=0.75))
    d.add(Line(tank_x + tank_w/2 - gas_pipe_thickness, gas_rise_y - gas_pipe_thickness, pipe_start_x + 5 - gas_pipe_thickness, gas_rise_y - gas_pipe_thickness, strokeColor=colors.black, strokeWidth=0.75))
    
    # Vertical down to injection point on air pipe
    d.add(Line(pipe_start_x + 5, gas_rise_y - gas_pipe_thickness, pipe_start_x + 5, gas_inject_y, strokeColor=colors.black, strokeWidth=0.75))
    d.add(Line(pipe_start_x + 5 - gas_pipe_thickness, gas_rise_y - gas_pipe_thickness, pipe_start_x + 5 - gas_pipe_thickness, gas_inject_y, strokeColor=colors.black, strokeWidth=0.75))
    
    # T-junction into air pipe (horizontal stub into the vertical pipe)
    d.add(Line(pipe_start_x + 5 - gas_pipe_thickness, gas_inject_y, pipe_start_x, gas_inject_y, strokeColor=colors.black, strokeWidth=0.75))
    d.add(Line(pipe_start_x + 5 - gas_pipe_thickness, gas_inject_y - gas_pipe_thickness, pipe_start_x, gas_inject_y - gas_pipe_thickness, strokeColor=colors.black, strokeWidth=0.75))
    # T-junction symbol on air pipe
    d.add(Line(pipe_start_x, gas_inject_y + 2, pipe_start_x, gas_inject_y - gas_pipe_thickness - 2, strokeColor=colors.black, strokeWidth=1.5))
    
    # Valve symbol on gas line (X shape) - on horizontal section above blower
    valve_x = (tank_x + pipe_start_x) / 2 + 20
    valve_y = gas_rise_y - gas_pipe_thickness/2
    d.add(Line(valve_x - 4, valve_y - 4, valve_x + 4, valve_y + 4, strokeColor=colors.black, strokeWidth=1))
    d.add(Line(valve_x - 4, valve_y + 4, valve_x + 4, valve_y - 4, strokeColor=colors.black, strokeWidth=1))
    
    # === BLOWER (positioned lower, to the right) ===
    d.add(Circle(blower_x, blower_y, 20, fillColor=None, strokeColor=colors.black, strokeWidth=1.5))
    d.add(Circle(blower_x, blower_y, 8, fillColor=None, strokeColor=colors.black, strokeWidth=0.75))  # Hub
    # Blower outlet flange connecting to pipe
    d.add(Rect(pipe_start_x - pipe_thickness - 2, blower_y - pipe_thickness/2 - 2, pipe_thickness + 4, pipe_thickness + 4, 
               fillColor=None, strokeColor=colors.black, strokeWidth=0.75))
    
    # === DOOR OPENING (shown as dashed on front face - visible from side as a slot) ===
    # In side view, door opening appears as a vertical slot on the front face
    door_slot_h = forge_h - 20
    d.add(Rect(forge_x - 2, forge_y + 10, 4, door_slot_h, fillColor=None, strokeColor=colors.black, 
               strokeWidth=0.75, strokeDashArray=[3, 2]))
    
    # === LABELS ===
    d.add(String(forge_x + forge_w/2 - 18, forge_y + forge_h/2 - 5, 'FORGE', fontSize=9, fillColor=colors.black))
    d.add(String(burner_x + 8, burner_y + 6, 'BURNER', fontSize=6, fillColor=colors.black))
    d.add(String(blower_x - 15, blower_y - 30, 'BLOWER', fontSize=7, fillColor=colors.black))
    d.add(String(blower_x - 22, blower_y - 40, f'{specs["cfm_recommended"]} CFM', fontSize=6, fillColor=colors.black))
    d.add(String(tank_x, tank_y - 10, 'PROPANE', fontSize=6, fillColor=colors.black))
    d.add(String(forge_x - 15, forge_y + forge_h/2 + 20, 'DOOR', fontSize=5, fillColor=colors.black))
    d.add(String(forge_x - 22, forge_y + forge_h/2 + 12, '(FRONT)', fontSize=4, fillColor=colors.black))
    d.add(String(valve_x - 10, valve_y + 8, 'VALVE', fontSize=5, fillColor=colors.black))
    
    # Pipe labels
    d.add(String(pipe_start_x - 45, pipe_rise_top - pipe_thickness - 8, '1.5" AIR', fontSize=5, fillColor=colors.black))
    d.add(String(pipe_start_x + 10, gas_inject_y - 5, '1/4" GAS', fontSize=5, fillColor=colors.black))
    
    # === SPECS BLOCK ===
    d.add(Rect(10, 10, 120, 50, fillColor=None, strokeColor=colors.black, strokeWidth=0.5))
    d.add(Line(10, 47, 130, 47, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(15, 50, 'SPECIFICATIONS', fontSize=6, fillColor=colors.black))
    d.add(String(15, 38, f'Chamber: {int(specs["internal_volume"])} cu.in.', fontSize=6, fillColor=colors.black))
    d.add(String(15, 28, f'Burner: {specs["burner_holes"]} holes', fontSize=6, fillColor=colors.black))
    d.add(String(15, 18, f'Blower: {specs["cfm_recommended"]} CFM', fontSize=6, fillColor=colors.black))
    
    # === TITLE BLOCK ===
    d.add(Line(10, height_px - 22, width_px - 10, height_px - 22, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(width_px/2 - 55, height_px - 18, 'SYSTEM SCHEMATIC', fontSize=10, fillColor=colors.black))
    
    return d

def draw_corner_detail(width_px=400, height_px=280):
    """Create architectural section detail of bolted corner assembly."""
    d = Drawing(width_px, height_px)
    
    # === SECTION VIEW ===
    x, y = 80, 70
    
    # Angle iron (L-shape in section)
    angle_t = 6  # Thickness
    angle_leg = 70
    
    # Vertical leg of angle
    d.add(Rect(x, y, angle_t, angle_leg, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    # Horizontal leg of angle  
    d.add(Rect(x, y, angle_leg, angle_t, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    
    # Cross-hatch the angle iron
    for i in range(int(angle_leg / 5)):
        hy = y + i * 5
        if hy < y + angle_leg:
            d.add(Line(x, hy, x + angle_t, hy + 3, strokeColor=colors.grey, strokeWidth=0.3))
        hx = x + i * 5
        if hx < x + angle_leg and hx > x + angle_t:
            d.add(Line(hx, y, hx + 3, y + angle_t, strokeColor=colors.grey, strokeWidth=0.3))
    
    # Vertical plate (forge side)
    plate_t = 8
    d.add(Rect(x - plate_t - 2, y - 10, plate_t, angle_leg + 20, fillColor=None, strokeColor=colors.black, strokeWidth=1.5))
    
    # Horizontal plate (forge top/bottom)
    d.add(Rect(x - 10, y - plate_t - 2, angle_leg + 20, plate_t, fillColor=None, strokeColor=colors.black, strokeWidth=1.5))
    
    # Bolts (4 per corner - 2 each direction)
    bolt_positions_v = [y + 20, y + 50]
    for by in bolt_positions_v:
        # Bolt shaft
        d.add(Line(x - plate_t - 5, by, x + angle_t/2, by, strokeColor=colors.black, strokeWidth=1.5))
        # Bolt head (hexagon simplified as circle)
        d.add(Circle(x - plate_t - 5, by, 4, fillColor=None, strokeColor=colors.black, strokeWidth=1))
        # Nut
        d.add(Rect(x + angle_t/2 - 3, by - 3, 6, 6, fillColor=None, strokeColor=colors.black, strokeWidth=0.75))
    
    bolt_positions_h = [x + 20, x + 50]
    for bx in bolt_positions_h:
        # Bolt shaft
        d.add(Line(bx, y - plate_t - 5, bx, y + angle_t/2, strokeColor=colors.black, strokeWidth=1.5))
        # Bolt head
        d.add(Circle(bx, y - plate_t - 5, 4, fillColor=None, strokeColor=colors.black, strokeWidth=1))
        # Nut
        d.add(Rect(bx - 3, y + angle_t/2 - 3, 6, 6, fillColor=None, strokeColor=colors.black, strokeWidth=0.75))
    
    # Dimension lines
    draw_dimension_line(d, x, y + angle_leg + 5, x + angle_leg, y + angle_leg + 5, '2"', offset=12)
    draw_dimension_line(d, x + angle_leg + 5, y, x + angle_leg + 5, y + angle_t, '1/8"', offset=15)
    
    # Labels with leader lines
    d.add(Line(x + angle_t + 5, y + angle_leg/2, x + 40, y + angle_leg + 30, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(x + 42, y + angle_leg + 27, 'ANGLE IRON', fontSize=7, fillColor=colors.black))
    d.add(String(x + 42, y + angle_leg + 18, '2" × 2" × 1/8"', fontSize=6, fillColor=colors.black))
    
    d.add(Line(x - plate_t/2 - 2, y + angle_leg + 5, x - 30, y + angle_leg + 40, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(x - 55, y + angle_leg + 37, '1/4" PLATE', fontSize=7, fillColor=colors.black))
    
    d.add(Line(x - plate_t - 5, y + 20, x - 40, y + 10, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(x - 75, y + 7, '5/16" BOLT', fontSize=6, fillColor=colors.black))
    d.add(String(x - 75, y - 2, '(4 PER CORNER)', fontSize=5, fillColor=colors.black))
    
    # Inside indicator
    d.add(String(x + 15, y + 25, 'INSIDE', fontSize=7, fillColor=colors.black))
    d.add(Line(x + 20, y + 22, x + 35, y + 35, strokeColor=colors.black, strokeWidth=0.5))
    
    # === PLAN VIEW (top-down, small) ===
    px, py = 260, 100
    pscale = 0.6
    
    d.add(String(px + 20, py + 70, 'PLAN VIEW', fontSize=7, fillColor=colors.black))
    
    # Outer plate outline
    d.add(Rect(px, py, 80, 60, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    
    # Angle iron position (corner)
    d.add(Rect(px + 5, py + 5, 8, 50, fillColor=None, strokeColor=colors.black, strokeWidth=0.75))
    d.add(Rect(px + 5, py + 5, 50, 8, fillColor=None, strokeColor=colors.black, strokeWidth=0.75))
    
    # Bolt positions (4 total)
    for bpos in [(px + 10, py + 20), (px + 10, py + 40), (px + 25, py + 10), (px + 45, py + 10)]:
        d.add(Circle(bpos[0], bpos[1], 3, fillColor=colors.black, strokeColor=colors.black))
    
    # Title block
    d.add(Line(10, 15, width_px - 10, 15, strokeColor=colors.black, strokeWidth=0.5))
    d.add(String(width_px/2 - 70, 5, 'CORNER ASSEMBLY DETAIL', fontSize=9, fillColor=colors.black))
    
    return d


# =============================================================================
# PDF BUILDER
# =============================================================================

def create_styles():
    """Create custom paragraph styles for PDF."""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=12,
        spaceBefore=12
    ))
    
    styles.add(ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#444444'),
        spaceAfter=10,
        spaceBefore=10
    ))
    
    styles.add(ParagraphStyle(
        'WarningText',
        parent=styles['BodyText'],
        textColor=colors.red,
        fontSize=10,
        spaceBefore=6,
        spaceAfter=6
    ))
    
    return styles

def build_pdf(specs):
    """Generate complete PDF build guide from specifications."""
    filename = f"Forge_Build_Guide_{int(specs['internal_volume'])}ci.pdf"
    doc = SimpleDocTemplate(
        filename, 
        pagesize=letter,
        rightMargin=0.5*inch, 
        leftMargin=0.5*inch,
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch
    )
    
    styles = create_styles()
    story = []
    
    debug_log(f"Building PDF: {filename}")
    
    # =========================================================================
    # PAGE 1: TITLE PAGE
    # =========================================================================
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("Ribbon Burner Forge", styles['CustomTitle']))
    story.append(Paragraph("Complete Build Guide", styles['CustomHeading']))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<b>Chamber Volume:</b> {int(specs['internal_volume'])} cubic inches", styles['BodyText']))
    story.append(Paragraph(f"<b>Internal Dimensions:</b> {specs['internal_w']}\" × {specs['internal_h']}\" × {specs['internal_l']}\"", styles['BodyText']))
    story.append(Paragraph(f"<b>Estimated Cost:</b> ${specs['estimated_cost']}", styles['BodyText']))
    story.append(Spacer(1, 0.5*inch))
    story.append(draw_assembly_overview(specs))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<i>Generated: {specs['generated_date']}</i>", styles['BodyText']))
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 2: TABLE OF CONTENTS
    # =========================================================================
    story.append(Paragraph("Table of Contents", styles['CustomHeading']))
    story.append(Spacer(1, 0.2*inch))
    
    toc_data = [
        ["1.", "Safety Requirements & Warnings"],
        ["2.", "Design Overview & Specifications"],
        ["3.", "Complete Bill of Materials"],
        ["4.", "Steel Cut List"],
        ["5.", "Forge Body Construction"],
        ["6.", "Ribbon Burner Assembly"],
        ["7.", "Sliding Door System"],
        ["8.", "Bolted Frame Details"],
        ["9.", "Air & Gas Systems"],
        ["10.", "Refractory Lining & Curing"],
        ["11.", "Assembly Instructions"],
        ["12.", "Operation Procedures"],
        ["13.", "Flame Tuning Guide"],
        ["14.", "Troubleshooting"],
        ["15.", "Maintenance Schedule"],
    ]
    
    toc_table = Table(toc_data, colWidths=[0.5*inch, 5*inch])
    toc_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(toc_table)
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 3: SAFETY REQUIREMENTS (CRITICAL)
    # =========================================================================
    story.append(Paragraph("1. Safety Requirements & Warnings", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>⚠️ CRITICAL SAFETY INFORMATION</b>", styles['WarningText']))
    story.append(Paragraph(
        "This forge operates with combustible gas at high temperatures. Improper construction "
        "or operation can result in fire, explosion, severe burns, carbon monoxide poisoning, or death. "
        "Read and understand ALL safety requirements before beginning construction.",
        styles['BodyText']))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Required Safety Equipment:</b>", styles['CustomSubHeading']))
    safety_items = [
        "• ABC-rated fire extinguisher (within arm's reach during operation)",
        "• Safety glasses (wear at ALL times near operating forge)",
        "• Leather gloves (minimum 14\" gauntlet style)",
        "• Leather apron or jacket",
        "• Hearing protection (blower noise can cause hearing damage)",
        "• Steel-toed boots (protection from dropped hot material)",
        "• Face shield (for forge welding operations)",
    ]
    for item in safety_items:
        story.append(Paragraph(item, styles['BodyText']))
    
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("<b>Workspace Requirements:</b>", styles['CustomSubHeading']))
    workspace_items = [
        "• NEVER operate indoors or in enclosed spaces",
        "• Minimum 10' × 10' clear area around forge",
        "• Concrete, gravel, or dirt floor (NO wood decking)",
        "• Overhead clearance minimum 8' (no combustible ceiling)",
        "• Remove all combustibles within 5 feet of forge",
        "• Install CO detector in adjacent enclosed spaces",
        "• Ensure adequate ventilation even outdoors",
    ]
    for item in workspace_items:
        story.append(Paragraph(item, styles['BodyText']))
    
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("<b>Gas System Safety:</b>", styles['CustomSubHeading']))
    gas_safety = [
        "• Leak test ALL connections with soapy water before EVERY use (first month)",
        "• Use only approved gas fittings and hoses rated for propane",
        "• Install shutoff valve within reach of operating position",
        "• NEVER use Teflon tape on flare fittings",
        "• Keep propane tank upright and secured",
        "• Store spare tanks outdoors, away from forge",
        "• Replace hoses showing any wear, cracking, or damage",
    ]
    for item in gas_safety:
        story.append(Paragraph(item, styles['BodyText']))
    
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("<b>Emergency Procedures:</b>", styles['CustomSubHeading']))
    emergency_items = [
        "• <b>Gas leak detected:</b> Close tank valve immediately, evacuate area, ventilate, do NOT operate any electrical switches",
        "• <b>Fire outside forge:</b> Close gas valve, use fire extinguisher, call 911 if not immediately controlled",
        "• <b>Blower failure:</b> Close gas valve IMMEDIATELY - gas will accumulate without airflow",
        "• <b>Burns:</b> Cool with water, seek medical attention for burns larger than 2\" or on face/hands/joints",
        "• <b>CO symptoms (headache, dizziness):</b> Leave area immediately, get fresh air, seek medical attention",
    ]
    for item in emergency_items:
        story.append(Paragraph(item, styles['BodyText']))
    
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 4: DESIGN OVERVIEW & SPECIFICATIONS
    # =========================================================================
    story.append(Paragraph("2. Design Overview & Specifications", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph(
        f"This forge design features a {int(specs['internal_volume'])} cubic inch internal chamber "
        f"with a {specs['burner_holes']}-hole ribbon burner. The bolted construction allows complete "
        "disassembly for maintenance and repair.",
        styles['BodyText']))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(draw_forge_body_isometric(specs))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Dimensional Specifications:</b>", styles['CustomSubHeading']))
    dim_data = [
        ["Measurement", "Internal", "External"],
        ["Width", f'{specs["internal_w"]}"', f'{specs["external_w"]:.1f}"'],
        ["Height", f'{specs["internal_h"]}"', f'{specs["external_h"]:.1f}"'],
        ["Length", f'{specs["internal_l"]}"', f'{specs["external_l"]:.1f}"'],
        ["Volume", f'{int(specs["internal_volume"])} ci', "—"],
        ["Insulation", f'{specs["insulation"]}"', "Ceramic blanket + IFB"],
    ]
    
    dim_table = Table(dim_data, colWidths=[2*inch, 2*inch, 2*inch])
    dim_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(dim_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("<b>System Specifications:</b>", styles['CustomSubHeading']))
    sys_data = [
        ["System", "Specification", "Notes"],
        ["Ribbon Burner", f'{specs["burner_holes"]} holes (1/4")', f'{specs["burner_length"]}" casting length'],
        ["Blower", f'{specs["cfm_recommended"]} CFM', f'Static pressure: {specs["static_pressure"]}" WC'],
        ["Refractory", "Kast-O-Lite 30 LI", f'{specs["refractory_bags"]} bags (55 lb)'],
        ["Ceramic Blanket", f'{specs["blanket_sqft"]} sq ft', '2" thickness'],
        ["BTU Requirement", f'{specs["btu_required"]:,}', 'Approximate'],
        ["Front Door", f'{specs["front_door_w"]}" × {specs["front_door_h"]}"', 'Sliding firebrick'],
    ]
    
    sys_table = Table(sys_data, colWidths=[1.8*inch, 2*inch, 2.5*inch])
    sys_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(sys_table)
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 5: BILL OF MATERIALS
    # =========================================================================
    story.append(Paragraph("3. Complete Bill of Materials", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Steel Components:</b>", styles['CustomSubHeading']))
    steel_bom = [
        ["Item", "Quantity", "Notes"],
        ["1/4\" Steel Plate", "See cut list", "6 panels total"],
        ["2\" × 2\" × 1/8\" Angle Iron", f"~{int(specs['external_l'] * 8 + specs['external_w'] * 8 + specs['external_h'] * 4)}\"", "Frame corners"],
        ["3\" × 3\" Square Tube", f'{specs["burner_length"] + 2}"', "Burner housing"],
        ["1.5\" Pipe", "24-36\"", "Air inlet"],
        ["1/4\" Pipe", "12\"", "Gas injection"],
        ["1/8\" Sheet Steel", "4 sq ft", "Door frames, baffle"],
        ["1/2\" Round Rod", "24\"", "Door tracks, handles"],
    ]
    
    steel_table = Table(steel_bom, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
    steel_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(steel_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Refractory Materials:</b>", styles['CustomSubHeading']))
    refrac_bom = [
        ["Item", "Quantity", "Purpose"],
        ["Ceramic Fiber Blanket 2\"", f'{specs["blanket_sqft"]} sq ft', "Wall/ceiling lining"],
        ["Castable Refractory", f'{specs["refractory_bags"]} bags', "Burner head (Kast-O-Lite 30)"],
        ["IFB (Insulating Fire Brick)", f'{specs["ifb_floor"] + specs["ifb_doors"]} bricks', "Floor and doors"],
        ["Rigidizer", "1-2 quarts", "Seal blanket surface"],
        ["ITC-100 (optional)", "1 pint", "IR reflective coating"],
        ["Stainless Pins/Staples", "50-100", "Secure blanket"],
    ]
    
    refrac_table = Table(refrac_bom, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
    refrac_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(refrac_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Hardware & Components:</b>", styles['CustomSubHeading']))
    hw_bom = [
        ["Item", "Quantity", "Notes"],
        ["5/16\" or 3/8\" Bolts", "40-50", "Grade 5+, 4 per corner"],
        ["Forge Blower", "1", f'{specs["cfm_recommended"]} CFM, {specs["static_pressure"]}" WC'],
        ["1.5\" Gate Valve", "1", "Air control"],
        ["Variable Speed Controller", "1", "Ceiling fan type (NOT dimmer)"],
        ["Propane Regulator", "1", "0-30 PSI adjustable"],
        ["Pressure Gauge", "1", "0-15 PSI display"],
        ["1/4\" Ball Valve", "1", "Main gas shutoff"],
        ["1/4\" Needle Valve", "1", "Fine adjustment"],
        ["1/4\" Solenoid Valve", "1", "Safety (wired to blower)"],
        ["Fire Extinguisher", "1", "ABC rated, 5+ lb"],
    ]
    
    hw_table = Table(hw_bom, colWidths=[2.5*inch, 1*inch, 3*inch])
    hw_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(hw_table)
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(f"<b>Estimated Total Cost:</b> ${specs['estimated_cost']} (excluding steel you may already have)", styles['BodyText']))
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 6: STEEL CUT LIST
    # =========================================================================
    story.append(Paragraph("4. Steel Cut List", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>1/4\" Steel Plate Cuts:</b>", styles['CustomSubHeading']))
    plate_data = [["Panel", "Qty", "Width", "Height", "Notes"]]
    for cut in specs['steel_cuts']['plates']:
        note = cut.get('note', '—')
        plate_data.append([cut['name'], str(cut['qty']), f'{cut["w"]:.1f}"', f'{cut["h"]:.1f}"', note])
    
    plate_table = Table(plate_data, colWidths=[1.5*inch, 0.5*inch, 1*inch, 1*inch, 2.5*inch])
    plate_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(plate_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Angle Iron Cuts (2\" × 2\" × 1/8\"):</b>", styles['CustomSubHeading']))
    angle_data = [["Component", "Qty", "Length"]]
    for cut in specs['steel_cuts']['angle_iron']:
        angle_data.append([cut['name'], str(cut['qty']), f'{cut["length"]:.1f}"'])
    
    angle_table = Table(angle_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
    angle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(angle_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("<b>Cutting Notes:</b>", styles['CustomSubHeading']))
    story.append(Paragraph("• Cut angle iron ends at 45° for miter joints at corners", styles['BodyText']))
    story.append(Paragraph("• Drill bolt holes slightly oversize (1/64\") for alignment tolerance", styles['BodyText']))
    story.append(Paragraph("• Deburr all cut edges to prevent injury during assembly", styles['BodyText']))
    story.append(Paragraph("• Use angle iron as drilling template for plate holes", styles['BodyText']))
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 7: FORGE BODY CONSTRUCTION
    # =========================================================================
    story.append(Paragraph("5. Forge Body Construction", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph(
        "The forge body uses bolted angle iron construction for easy assembly and future maintenance. "
        "All six panels bolt to the internal angle iron frame.",
        styles['BodyText']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(draw_corner_detail())
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Assembly Sequence:</b>", styles['CustomSubHeading']))
    assembly_steps = [
        "1. Cut all angle iron pieces to length per cut list",
        "2. Drill bolt holes in angle iron at 3-4\" spacing",
        "3. Assemble angle iron frame (dry fit, no plates)",
        "4. Verify frame is square using diagonal measurements",
        "5. Use frame as template to drill plate holes",
        "6. Cut door opening in front panel",
        f"7. Cut burner hole in top panel ({specs['burner_width'] + 0.5}\" diameter)",
        "8. Bolt bottom panel to frame first",
        "9. Attach side panels",
        "10. Install front and rear panels",
        "11. Top panel installs after refractory lining",
    ]
    for step in assembly_steps:
        story.append(Paragraph(step, styles['BodyText']))
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 8: RIBBON BURNER ASSEMBLY
    # =========================================================================
    story.append(Paragraph("6. Ribbon Burner Assembly", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph(
        f"The ribbon burner provides even heat distribution through {specs['burner_holes']} flame ports. "
        f"Sized for your {int(specs['internal_volume'])} ci chamber.",
        styles['BodyText']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(draw_burner_detail(specs))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Burner Specifications:</b>", styles['CustomSubHeading']))
    burner_specs = [
        ["Component", "Specification"],
        ["Housing", f'3" × 3" square tube, {specs["burner_length"] + 2}" long'],
        ["Air Inlet", "1.5\" pipe, 6\" stub"],
        ["Refractory Head", f'{specs["burner_length"]}" × 3" × 3" deep'],
        ["Flame Holes", f'{specs["burner_holes"]} holes, 1/4" diameter'],
        ["Hole Pattern", f'{specs["burner_rows"]} rows × {specs["holes_per_row"]} holes, staggered'],
        ["Gas Injection", "1/4\" pipe into air stream"],
        ["Mounting Angle", "30-45° downward into chamber"],
    ]
    
    burner_table = Table(burner_specs, colWidths=[2*inch, 4.5*inch])
    burner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(burner_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Casting the Refractory Head:</b>", styles['CustomSubHeading']))
    casting_steps = [
        f"1. Build mold: {specs['burner_length']}\" × 3\" × 3\" deep (plywood or melamine)",
        f"2. Insert {specs['burner_holes']} drinking straws in {specs['burner_rows']}×{specs['holes_per_row']} pattern",
        "3. Space straws ~3/4\" apart in staggered rows",
        "4. Mix Kast-O-Lite 30 to peanut butter consistency",
        "5. Pack refractory firmly around straws",
        "6. Vibrate or tap mold to release air bubbles",
        "7. Cure 24-48 hours before demolding",
        "8. Remove straws (burn out or pull)",
        "9. Oven cure: 200°F for 2 hours, then 350°F for 2 hours",
        "10. Mount to burner housing with refractory cement",
    ]
    for step in casting_steps:
        story.append(Paragraph(step, styles['BodyText']))
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 9: SLIDING DOOR SYSTEM
    # =========================================================================
    story.append(Paragraph("7. Sliding Door System", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph(
        "Sliding firebrick doors provide excellent heat retention and one-handed operation. "
        "The doors hang from a round rod track above the opening.",
        styles['BodyText']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(draw_door_system(specs))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Door Specifications:</b>", styles['CustomSubHeading']))
    door_data = [
        ["Feature", "Front Door", "Rear Door" if specs['door_config'] == 2 else "N/A"],
        ["Opening", f'{specs["front_door_w"]}" × {specs["front_door_h"]}"', 
         f'{specs["rear_door_w"]}" × {specs["rear_door_h"]}"' if specs['door_config'] == 2 else "—"],
        ["Door Frame", f'{specs["front_door_w"] + 1}" × {specs["front_door_h"] + 1}" × 3"', "Similar"],
        ["Track Length", f'{specs["front_door_w"] + 12}"', "Similar"],
        ["Firebricks", f'{specs["ifb_doors"]} IFB', "—"],
    ]
    
    door_table = Table(door_data, colWidths=[2*inch, 2.2*inch, 2.2*inch])
    door_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(door_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Door Construction:</b>", styles['CustomSubHeading']))
    door_steps = [
        "1. Weld 1/8\" angle iron into rectangular door frame",
        "2. Add tube or pipe hanger on top to slide on rod",
        "3. Cut firebricks to fit inside frame",
        "4. Secure bricks with high-temp cement or wire",
        "5. Weld handle to one side",
        "6. Weld rod supports above door opening",
        "7. Install 1/2\" round rod through supports",
        "8. Hang door and test slide action",
    ]
    for step in door_steps:
        story.append(Paragraph(step, styles['BodyText']))
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 10: AIR & GAS SYSTEMS
    # =========================================================================
    story.append(Paragraph("9. Air & Gas Supply Systems", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Air Supply System:</b>", styles['CustomSubHeading']))
    air_data = [
        ["Component", "Specification"],
        ["Blower", f'{specs["cfm_recommended"]} CFM centrifugal forge blower'],
        ["Static Pressure", f'{specs["static_pressure"]}" WC minimum'],
        ["Pipe Size", "1.5\" throughout"],
        ["Gate Valve", "1.5\" for coarse air control"],
        ["Speed Controller", "Ceiling fan type (NOT lamp dimmer)"],
        ["Flex Connection", "1.5\" silicone hose, 12-18\""],
    ]
    
    air_table = Table(air_data, colWidths=[2*inch, 4.5*inch])
    air_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(air_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Propane Gas System:</b>", styles['CustomSubHeading']))
    gas_data = [
        ["Component", "Specification"],
        ["Propane Tank", "20-100 lb cylinder"],
        ["Regulator", "Adjustable 0-30 PSI"],
        ["Pressure Gauge", "0-15 PSI display"],
        ["Main Shutoff", "1/4\" ball valve"],
        ["Solenoid Valve", "1/4\" normally closed (wire to blower power)"],
        ["Needle Valve", "1/4\" for fine adjustment"],
        ["Gas Line", "1/4\" black iron or approved propane hose"],
        ["Operating Pressure", "5-10 PSI typical"],
    ]
    
    gas_table = Table(gas_data, colWidths=[2*inch, 4.5*inch])
    gas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(gas_table)
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph(
        "<b>SAFETY:</b> Wire gas solenoid valve to blower power so gas cannot flow when blower is off. "
        "Leak test entire gas system with soapy water before first use.",
        styles['WarningText']))
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 11: REFRACTORY LINING & CURING
    # =========================================================================
    story.append(Paragraph("10. Refractory Lining & Curing", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Lining Installation:</b>", styles['CustomSubHeading']))
    lining_steps = [
        f"1. Cut ceramic blanket to fit chamber: {specs['blanket_sqft']} sq ft total",
        "2. Install floor first: layer of IFB bricks on thin refractory cement bed",
        "3. Line walls with 2\" ceramic blanket",
        "4. Secure blanket with stainless pins every 4-6\"",
        "5. Line ceiling with 2\" ceramic blanket",
        "6. Apply rigidizer to all blanket surfaces (wear respirator!)",
        "7. Allow rigidizer to dry completely (24 hours)",
        "8. Optional: Apply ITC-100 coating for IR reflection",
        "9. Install top panel after lining is complete",
    ]
    for step in lining_steps:
        story.append(Paragraph(step, styles['BodyText']))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Curing Schedule (CRITICAL):</b>", styles['CustomSubHeading']))
    story.append(Paragraph(
        "Improper curing will cause refractory to crack and fail. Follow this schedule:",
        styles['BodyText']))
    story.append(Spacer(1, 0.1*inch))
    
    cure_data = [
        ["Day", "Temperature", "Duration", "Notes"],
        ["1", "200-300°F", "2-3 hours", "Low flame, doors open"],
        ["2", "400-500°F", "2-3 hours", "Doors cracked"],
        ["3", "700-800°F", "2-3 hours", "Doors partially closed"],
        ["4", "1000-1200°F", "2-3 hours", "Normal operation"],
        ["5+", "Full heat", "As needed", "Ready for use"],
    ]
    
    cure_table = Table(cure_data, colWidths=[0.8*inch, 1.5*inch, 1.5*inch, 2.5*inch])
    cure_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(cure_table)
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Steam escaping during initial cures is normal. Cracking sounds may occur. "
        "Do NOT rush the curing process.",
        styles['BodyText']))
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 12: OPERATION PROCEDURES
    # =========================================================================
    story.append(Paragraph("12. Operation Procedures", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Startup Procedure:</b>", styles['CustomSubHeading']))
    startup = [
        "1. Inspect forge and gas connections (leak test if needed)",
        "2. Ensure fire extinguisher is within reach",
        "3. Clear area of combustibles",
        "4. Position doors for desired opening",
        "5. Open air gate valve fully",
        "6. Turn on blower, wait 10-15 seconds",
        "7. Open main gas ball valve",
        "8. Slowly open needle valve",
        "9. Ignite at door opening with long lighter or torch",
        "10. Adjust gas for desired heat",
        "11. Fine-tune air for proper flame",
    ]
    for step in startup:
        story.append(Paragraph(step, styles['BodyText']))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Shutdown Procedure:</b>", styles['CustomSubHeading']))
    shutdown = [
        "1. Close gas needle valve",
        "2. Close main gas ball valve",
        "3. Keep blower running 60 seconds (purge chamber)",
        "4. Turn off blower",
        "5. Leave doors cracked until cool (thermal shock prevention)",
        "6. Never move forge while hot",
    ]
    for step in shutdown:
        story.append(Paragraph(step, styles['BodyText']))
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 13: FLAME TUNING
    # =========================================================================
    story.append(Paragraph("13. Flame Tuning Guide", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph(
        "Proper flame tuning is essential for efficient operation and quality work. "
        "The air-to-fuel ratio determines the forge atmosphere.",
        styles['BodyText']))
    story.append(Spacer(1, 0.1*inch))
    
    flame_data = [
        ["Flame Type", "Appearance", "Use Case"],
        ["Neutral", "Short blue cones, purple tips", "General forging"],
        ["Reducing", "Longer flames, orange/yellow streaks", "Forge welding, minimizes scale"],
        ["Oxidizing", "Short, loud, hissing blue", "Maximum heat (causes heavy scale)"],
    ]
    
    flame_table = Table(flame_data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
    flame_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(flame_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Tuning Adjustments:</b>", styles['CustomSubHeading']))
    story.append(Paragraph("• <b>Too much scale on steel:</b> Reduce air (more reducing atmosphere)", styles['BodyText']))
    story.append(Paragraph("• <b>Not reaching temperature:</b> Increase gas, close doors more", styles['BodyText']))
    story.append(Paragraph("• <b>Flame blowing out:</b> Reduce both air and gas, let forge warm up", styles['BodyText']))
    story.append(Paragraph("• <b>Loud roaring/hissing:</b> Too much air - reduce blower speed", styles['BodyText']))
    story.append(Paragraph("• <b>Lazy, yellow flames:</b> Not enough air - increase blower", styles['BodyText']))
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 14: TROUBLESHOOTING
    # =========================================================================
    story.append(Paragraph("14. Troubleshooting", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    trouble_data = [
        ["Problem", "Possible Causes", "Solutions"],
        ["Won't ignite", "No gas, no spark, wrong air/gas", "Check gas valve, test igniter, reduce air"],
        ["Flame blows out", "Too much air, forge cold", "Reduce air, preheat with low flame"],
        ["Won't reach temp", "Gas leak, poor insulation, doors open", "Leak test, check blanket, close doors"],
        ["Uneven heating", "Blocked holes, burner angle", "Clear holes, adjust mount angle"],
        ["Excessive scale", "Oxidizing atmosphere", "Reduce air, increase gas slightly"],
        ["High fuel use", "Gas leak, damaged insulation", "Leak test, inspect/repair lining"],
        ["Door binding", "Scale buildup, track bent", "Clean track, check alignment"],
        ["Bolts loosening", "Thermal cycling", "Use lock washers, retorque after cures"],
        ["Smoke from chamber", "Contamination, flux residue", "Clean chamber, normal with flux"],
        ["Blower overheating", "Blocked inlet, undersized", "Clear obstructions, check CFM rating"],
    ]
    
    trouble_table = Table(trouble_data, colWidths=[1.5*inch, 2.2*inch, 2.8*inch])
    trouble_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(trouble_table)
    story.append(PageBreak())
    
    # =========================================================================
    # PAGE 15: MAINTENANCE SCHEDULE
    # =========================================================================
    story.append(Paragraph("15. Maintenance Schedule", styles['CustomHeading']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>After Each Use:</b>", styles['CustomSubHeading']))
    story.append(Paragraph("• Visual inspection of chamber for damage", styles['BodyText']))
    story.append(Paragraph("• Remove scale and debris from floor", styles['BodyText']))
    story.append(Paragraph("• Check door operation", styles['BodyText']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Monthly (Heavy Use):</b>", styles['CustomSubHeading']))
    story.append(Paragraph("• Check all bolt tightness", styles['BodyText']))
    story.append(Paragraph("• Inspect door firebricks for cracks", styles['BodyText']))
    story.append(Paragraph("• Clean sliding tracks", styles['BodyText']))
    story.append(Paragraph("• Leak test gas connections", styles['BodyText']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Quarterly:</b>", styles['CustomSubHeading']))
    story.append(Paragraph("• Inspect ceramic blanket condition", styles['BodyText']))
    story.append(Paragraph("• Check burner holes for blockage", styles['BodyText']))
    story.append(Paragraph("• Inspect refractory floor for wear", styles['BodyText']))
    story.append(Paragraph("• Clean blower intake filter", styles['BodyText']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Annually:</b>", styles['CustomSubHeading']))
    story.append(Paragraph("• Disassemble top panel, full chamber inspection", styles['BodyText']))
    story.append(Paragraph("• Replace damaged refractory", styles['BodyText']))
    story.append(Paragraph("• Reapply rigidizer to worn areas", styles['BodyText']))
    story.append(Paragraph("• Replace door firebricks if needed", styles['BodyText']))
    story.append(Paragraph("• Deep clean entire forge", styles['BodyText']))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("<b>Expected Performance:</b>", styles['CustomSubHeading']))
    perf_data = [
        ["Parameter", "Specification"],
        ["Heat-up Time", "10-15 minutes to 2000°F"],
        ["Maximum Temperature", "2400-2500°F (forge welding heat)"],
        ["Even Heating Zone", f"~{int(specs['internal_l'] * 0.6)}\" from burner"],
        ["Operating Pressure", "5-10 PSI propane"],
        ["Operating Cost", "~$1-3/hour (varies with propane prices)"],
    ]
    
    perf_table = Table(perf_data, colWidths=[2*inch, 4.5*inch])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(perf_table)
    
    # Build the PDF
    debug_log("Building PDF document...")
    doc.build(story)
    
    return filename


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main application entry point."""
    global DEBUG_MODE
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Interactive Forge Designer - Generate custom forge build guides'
    )
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--json', action='store_true', help='Export specs to JSON file')
    args = parser.parse_args()
    
    DEBUG_MODE = args.debug
    
    if DEBUG_MODE:
        print("[DEBUG MODE ENABLED]")
        print(f"[DEBUG] Python version: {sys.version}")
        print()
    
    try:
        # Get user input
        user_input = get_user_input()
        debug_log(f"User input received: {user_input}")
        
        # Calculate specifications
        print("\n[*] Calculating forge specifications...")
        specs = calculate_forge_specs(user_input)
        
        # Display summary
        print("\n" + "=" * 60)
        print("   FORGE DESIGN SUMMARY")
        print("=" * 60)
        print(f"   Chamber Volume:    {int(specs['internal_volume'])} cubic inches")
        print(f"   External Size:     {specs['external_w']:.1f}\" × {specs['external_h']:.1f}\" × {specs['external_l']:.1f}\"")
        print(f"   Ribbon Burner:     {specs['burner_holes']} holes, {specs['burner_length']}\" long")
        print(f"   Blower Required:   {specs['cfm_recommended']} CFM @ {specs['static_pressure']}\" WC")
        print(f"   Refractory:        {specs['refractory_bags']} bags Kast-O-Lite 30")
        print(f"   Ceramic Blanket:   {specs['blanket_sqft']} sq ft")
        print(f"   Estimated Cost:    ${specs['estimated_cost']}")
        print("=" * 60)
        
        # Export JSON if requested
        if args.json:
            json_file = f"forge_specs_{int(specs['internal_volume'])}ci.json"
            with open(json_file, 'w') as f:
                json.dump(specs, f, indent=2, default=str)
            print(f"\n[*] Specs exported to: {json_file}")
        
        # Generate PDF
        print("\n[*] Generating PDF build guide...")
        pdf_file = build_pdf(specs)
        
        print(f"\n[SUCCESS] Build guide generated: {pdf_file}")
        print("          Open the PDF for complete instructions, safety info, and diagrams.")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
