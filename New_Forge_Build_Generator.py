#!/usr/bin/env python3
"""
Dynamic Modular Forge Design Suite v2.0
Generates a complete PDF build guide for a Ribbon Burner Forge.
Requires: reportlab (pip install reportlab)
"""

import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.shapes import Drawing, Rect, Line, Circle, Polygon, String
from reportlab.graphics import renderPDF

# --- CORE CALCULATIONS & ENGINEERING ---

def get_forge_specs():
    print("="*60 + "\n   MODULAR RIBBON BURNER FORGE ENGINEERING SUITE\n" + "="*60)
    try:
        w = float(input("Internal Chamber Width (in) [Default 4]: ") or 4)
        h = float(input("Internal Chamber Height (in) [Default 4]: ") or 4)
        l = float(input("Internal Chamber Length (in) [Default 12]: ") or 12)
        ins = float(input("Insulation Thickness (in) [Default 2]: ") or 2)
        
        vol = w * h * l
        # Modular Chassis: Plates add roughly 1" to total length
        ext_w, ext_h, ext_l = w + (ins*2), h + (ins*2), l + 1.0
        
        # Burner & Blower Math
        total_holes = max(12, round(vol / 18))
        h_per_row = round(total_holes / 3)
        b_len = round((h_per_row * 0.75) + 1.5, 1)
        cfm = round((vol / 18) * 1.2)
        static_p = "1.5" if vol < 500 else "3.0"
        
        # Materials Calculation (Kast-O-Lite 30 LI ~90-95 lb/ft³)
        refr_ci = (ext_w * ext_h * ext_l) - vol
        bags = round((refr_ci / 1728) * 92 / 55, 1)
        cost = round((bags * 110) + 250, 2) # Est. including blower/steel
        
        return {
            "w":w, "h":h, "l":l, "vol":vol, "ins":ins, "ext_w":ext_w, "ext_h":ext_h, "ext_l":ext_l,
            "holes": h_per_row * 3, "h_per_row": h_per_row, "b_len": b_len, "cfm": cfm, 
            "sp": static_p, "bags": bags, "cost": cost
        }
    except ValueError:
        print("[!] Input Error: Numbers only, please.")
        sys.exit(1)

# --- GRAPHICS ENGINE ---

def iso_project(x, y, z, x_off, y_off, scale):
    """30-degree isometric projection logic."""
    ix = x_off + (x * 0.866 - z * 0.866) * scale
    iy = y_off + (y + (x * 0.5 + z * 0.5)) * scale
    return ix, iy

def draw_exploded_view(specs, width_px=500, height_px=350):
    d = Drawing(width_px, height_px)
    w, h, l = specs['ext_w'], specs['ext_h'], specs['ext_l']
    scale, x_off, y_off, gap = 6.0, 220, 100, 50

    # Back Plate
    bz = l + gap
    bp = [iso_project(ix, iy, bz, x_off, y_off, scale) for ix, iy in [(0,0), (w,0), (w,h), (0,h)]]
    d.add(Polygon([bp[0][0],bp[0][1], bp[1][0],bp[1][1], bp[2][0],bp[2][1], bp[3][0],bp[3][1]], fillColor=colors.lightgrey))
    
    # Body
    p_front = [iso_project(ix, iy, 0, x_off, y_off, scale) for ix, iy in [(0,0), (w,0), (w,h), (0,h)]]
    p_back = [iso_project(ix, iy, l, x_off, y_off, scale) for ix, iy in [(0,0), (w,0), (w,h), (0,h)]]
    d.add(Polygon([p_front[0][0],p_front[0][1], p_front[1][0],p_front[1][1], p_front[2][0],p_front[2][1], p_front[3][0],p_front[3][1]], fillColor=colors.grey))
    for s, e in zip(p_front, p_back): d.add(Line(s[0],s[1],e[0],e[1]))

    # Front Plate
    fz = -gap
    fp = [iso_project(ix, iy, fz, x_off, y_off, scale) for ix, iy in [(0,0), (w,0), (w,h), (0,h)]]
    d.add(Polygon([fp[0][0],fp[0][1], fp[1][0],fp[1][1], fp[2][0],fp[2][1], fp[3][0],fp[3][1]], fillColor=colors.lightgrey))

    # Threaded Rods (Sandwich Hardware)
    for ix, iy in [(0,0), (w,0), (w,h), (0,h)]:
        start = iso_project(ix, iy, fz-10, x_off, y_off, scale)
        end = iso_project(ix, iy, bz+10, x_off, y_off, scale)
        d.add(Line(start[0],start[1], end[0],end[1], strokeColor=colors.black, strokeDashArray=[2,2]))
        d.add(Circle(start[0],start[1], 3, fillColor=colors.darkgrey)) # Hardware Nut
    
    return d

def draw_manifold_detail(width_px=500, height_px=200):
    d = Drawing(width_px, height_px)
    # Air Pipe
    d.add(Rect(150, 100, 200, 40, fillColor=colors.lightgrey, strokeWidth=2))
    # Gas Port
    d.add(Line(250, 140, 250, 165, strokeColor=colors.red, strokeWidth=4))
    d.add(Circle(250, 170, 5, fillColor=colors.red))
    d.add(String(180, 180, 'Gas Injector (Needle Valve)', fontSize=9, fillColor=colors.red))
    # Gate Valve
    d.add(Rect(120, 95, 30, 50, fillColor=colors.darkblue))
    d.add(String(100, 150, 'Air Gate Valve', fontSize=8))
    # Coupling
    d.add(Rect(350, 70, 40, 30, fillColor=colors.darkgrey))
    d.add(String(340, 55, 'Burner Coupling', fontSize=8))
    return d

# --- PDF BUILDER ---

def create_full_guide(s):
    doc = SimpleDocTemplate(f"Forge_Master_Guide_{int(s['vol'])}ci.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # PAGE 1: Overview & Specs
    elements.append(Paragraph(f"Forge Build Guide: {int(s['vol'])}in³ Chamber", styles['Title']))
    elements.append(Paragraph(f"This document outlines a modular, non-welded forced-air forge designed for high-efficiency ribbon burner operation. <b>Estimated Cost: ${s['cost']}</b>", styles['Normal']))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(draw_exploded_view(s))
    elements.append(Paragraph("<b>Exploded Assembly:</b> Threaded rods compress the exterior plates against the insulated chassis, allowing for complete disassembly and maintenance.", styles['Normal']))
    
    # PAGE 2: System Specifications
    elements.append(PageBreak())
    elements.append(Paragraph("Technical Specifications", styles['Heading2']))
    table_data = [
        ["System", "Requirement", "Note"],
        ["Ribbon Burner", f"{s['holes']} Holes (1/4\")", f"Casting length: {s['b_len']}\""],
        ["Blower", f"{s['cfm']} CFM", f"Static Pressure: {s['sp']}\" WC"],
        ["Refractory", "Kast-O-Lite 30 LI", f"{s['bags']} Bags (55lb)"],
        ["Manifold", "Black Iron Pipe", "2\" Main Supply Pipe"]
    ]
    t = Table(table_data, colWidths=[1.5*inch, 2*inch, 2.5*inch])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.black), ('TEXTCOLOR',(0,0),(-1,0),colors.white), ('GRID',(0,0),(-1,-1),0.5,colors.grey)]))
    elements.append(t)
    elements.append(Spacer(1, 0.4*inch))
    elements.append(draw_manifold_detail())

    # PAGE 3: Assembly & Tuning
    elements.append(PageBreak())
    elements.append(Paragraph("Assembly & Flame Tuning", styles['Heading2']))
    for step in ["1. Build Chassis", "2. Cast Burner Block", "3. Line with 1/2\" Refractory", "4. Install Manifold"]:
        elements.append(Paragraph(f"<b>{step}</b>", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Tuning:</b> Adjust for a 'Neutral' flame (short blue cones). If scale builds up on steel, increase gas (Reducing). If forge is loud and hissing with no flame, decrease air (Oxidizing).", styles['Normal']))

    doc.build(elements)
    print(f"\n[Success] Professional guide generated: Forge_Master_Guide_{int(s['vol'])}ci.pdf")

if __name__ == "__main__":
    create_full_guide(get_forge_specs())

