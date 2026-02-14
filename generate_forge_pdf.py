#!/usr/bin/env python3
"""
Generate an illustrated PDF for the Ribbon Burner Forge Design
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, Line, Circle, String, Polygon
from reportlab.graphics import renderPDF
from io import BytesIO

def create_3d_box_drawing(width_px=400, height_px=300):
    """Create isometric view of forge body"""
    d = Drawing(width_px, height_px)
    
    # Isometric projection parameters
    scale = 8
    x_off = 50
    y_off = 50
    
    # Define box dimensions (in design units: 12"W x 14"H x 30"L)
    w, h, l = 12, 14, 30
    
    # Isometric conversion
    def iso(x, y, z):
        iso_x = x_off + (x - z) * scale * 0.866
        iso_y = y_off + (x + z) * scale * 0.5 + y * scale
        return iso_x, iso_y
    
    # Front face vertices
    p1 = iso(0, 0, 0)
    p2 = iso(w, 0, 0)
    p3 = iso(w, h, 0)
    p4 = iso(0, h, 0)
    
    # Back face vertices
    p5 = iso(0, 0, l)
    p6 = iso(w, 0, l)
    p7 = iso(w, h, l)
    p8 = iso(0, h, l)
    
    # Draw back edges (lighter)
    d.add(Line(p5[0], p5[1], p6[0], p6[1], strokeColor=colors.grey, strokeWidth=1))
    d.add(Line(p6[0], p6[1], p7[0], p7[1], strokeColor=colors.grey, strokeWidth=1))
    d.add(Line(p7[0], p7[1], p8[0], p8[1], strokeColor=colors.grey, strokeWidth=1))
    d.add(Line(p8[0], p8[1], p5[0], p5[1], strokeColor=colors.grey, strokeWidth=1))
    
    # Draw connecting edges
    d.add(Line(p1[0], p1[1], p5[0], p5[1], strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(p2[0], p2[1], p6[0], p6[1], strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(p3[0], p3[1], p7[0], p7[1], strokeColor=colors.black, strokeWidth=1.5))
    d.add(Line(p4[0], p4[1], p8[0], p8[1], strokeColor=colors.black, strokeWidth=1.5))
    
    # Draw front face (darker)
    front_face = Polygon([p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1]], 
                        fillColor=colors.lightgrey, strokeColor=colors.black, strokeWidth=2)
    d.add(front_face)
    
    # Draw front door opening (9" x 11")
    door_w, door_h = 9, 11
    door_x, door_y = (w - door_w) / 2, (h - door_h) / 2
    d1 = iso(door_x, door_y, 0)
    d2 = iso(door_x + door_w, door_y, 0)
    d3 = iso(door_x + door_w, door_y + door_h, 0)
    d4 = iso(door_x, door_y + door_h, 0)
    door_rect = Polygon([d1[0], d1[1], d2[0], d2[1], d3[0], d3[1], d4[0], d4[1]], 
                       fillColor=colors.black, strokeColor=colors.red, strokeWidth=2)
    d.add(door_rect)
    
    # Add dimension labels
    d.add(String(x_off - 20, y_off + h * scale / 2, '14"', fontSize=10, fillColor=colors.blue))
    d.add(String(x_off + w * scale * 0.866 / 2, y_off - 20, '12"', fontSize=10, fillColor=colors.blue))
    d.add(String(x_off + w * scale * 0.866 + 50, y_off + h * scale / 2, '30"', fontSize=10, fillColor=colors.blue))
    
    # Title
    d.add(String(width_px/2 - 50, height_px - 20, 'Forge Body Assembly', fontSize=12, fillColor=colors.black))
    
    return d

def create_burner_drawing(width_px=400, height_px=300):
    """Create ribbon burner detail drawing - side view showing bottom holes"""
    d = Drawing(width_px, height_px)
    
    # Burner body (3" x 3" x 12") - side view
    x, y = 50, 120
    w, h = 250, 60  # Scaled dimensions (w=length, h=height)
    
    # Main burner rectangle (side profile)
    d.add(Rect(x, y, w, h, fillColor=colors.lightblue, strokeColor=colors.black, strokeWidth=2))
    
    # Air inlet pipe (1.5" dia) - left side
    pipe_w, pipe_h = 40, 30
    d.add(Rect(x - pipe_w, y + 15, pipe_w, pipe_h, fillColor=colors.lightgrey, 
               strokeColor=colors.black, strokeWidth=2))
    d.add(String(x - pipe_w/2 - 15, y - 15, '1.5" Air', fontSize=9, fillColor=colors.black))
    d.add(String(x - pipe_w/2 - 15, y - 25, 'Inlet', fontSize=9, fillColor=colors.black))
    
    # Bottom face with flame holes (shown below burner)
    bottom_y = y - 40
    d.add(Rect(x, bottom_y, w, 30, fillColor=colors.wheat, strokeColor=colors.black, strokeWidth=2))
    
    # Draw 24 flame holes (3 rows of 8) on BOTTOM face
    hole_radius = 2
    for row in range(3):
        for col in range(8):
            hole_x = x + 10 + col * 29
            hole_y = bottom_y + 8 + row * 8
            d.add(Circle(hole_x, hole_y, hole_radius, fillColor=colors.black))
    
    # Label for bottom face
    d.add(String(x + w/2 - 35, bottom_y - 12, 'Refractory Bottom', fontSize=9, fillColor=colors.black))
    d.add(String(x + w/2 - 35, bottom_y - 22, '(24 holes, 1/4" dia)', fontSize=8, fillColor=colors.black))
    
    # Gas injection annotation
    gas_y = y + h/2
    d.add(Line(x - 20, gas_y, x - 10, gas_y, strokeColor=colors.red, strokeWidth=2))
    d.add(Circle(x - 20, gas_y, 3, fillColor=colors.red))
    d.add(String(x - 55, gas_y + 5, 'Gas', fontSize=9, fillColor=colors.red))
    d.add(String(x - 70, gas_y - 5, 'Injection', fontSize=8, fillColor=colors.red))
    
    # Internal baffle indication (dashed line)
    baffle_x = x + 60
    d.add(Line(baffle_x, y, baffle_x, y + h, strokeColor=colors.grey, 
               strokeWidth=1, strokeDashArray=[3, 3]))
    d.add(String(baffle_x - 25, y + h + 12, 'Baffle', fontSize=8, fillColor=colors.grey))
    
    # Dimensions
    d.add(Line(x, y + h + 15, x + w, y + h + 15, strokeColor=colors.blue, strokeWidth=1))
    d.add(String(x + w/2 - 10, y + h + 25, '12" Long', fontSize=9, fillColor=colors.blue))
    
    d.add(Line(x - 55, y, x - 55, y + h, strokeColor=colors.blue, strokeWidth=1))
    d.add(String(x - 85, y + h/2 - 5, '3" x 3"', fontSize=9, fillColor=colors.blue))
    
    # Title
    d.add(String(width_px/2 - 70, height_px - 20, 'Ribbon Burner Assembly', fontSize=12, fillColor=colors.black))
    
    return d

def create_door_drawing(width_px=400, height_px=300):
    """Create sliding door system on round rod"""
    d = Drawing(width_px, height_px)
    
    # Door opening
    x, y = 100, 80
    opening_w, opening_h = 90, 110
    
    # Forge face outline
    d.add(Rect(x - 20, y - 20, opening_w + 100, opening_h + 40, 
               fillColor=colors.lightgrey, strokeColor=colors.black, strokeWidth=2))
    
    # Door opening
    d.add(Rect(x, y, opening_w, opening_h, fillColor=colors.black, 
               strokeColor=colors.red, strokeWidth=2))
    
    # Round rod above opening (1/2" rod)
    rod_y = y + opening_h + 15
    rod_x_start = x - 40
    rod_x_end = x + opening_w + 60
    # Draw rod with 3D effect
    d.add(Line(rod_x_start, rod_y + 3, rod_x_end, rod_y + 3, strokeColor=colors.grey, strokeWidth=6))
    d.add(Line(rod_x_start, rod_y, rod_x_end, rod_y, strokeColor=colors.darkgrey, strokeWidth=5))
    d.add(String(rod_x_start - 10, rod_y + 15, '1/2" Round Rod', fontSize=8, fillColor=colors.black))
    
    # Rod supports (welded to forge)
    support_positions = [rod_x_start + 10, rod_x_end - 10]
    for sx in support_positions:
        d.add(Rect(sx - 8, y + opening_h + 5, 16, 8, fillColor=colors.steelblue, 
                  strokeColor=colors.black, strokeWidth=1))
    
    # Door panel (slid partially open) - hangs from rod
    door_x = x + 40
    door_y = y - 5  # Slightly overlaps opening
    door_w, door_h = 100, 120
    
    # Rod clamp/hanger on top of door
    clamp_x = door_x + door_w/2
    d.add(Rect(clamp_x - 8, rod_y - 8, 16, 16, fillColor=colors.darkgrey, 
               strokeColor=colors.black, strokeWidth=1.5))
    d.add(Circle(clamp_x, rod_y, 3, fillColor=colors.lightgrey, strokeColor=colors.black))
    d.add(String(clamp_x + 10, rod_y - 3, 'Pipe clamp', fontSize=7, fillColor=colors.black))
    d.add(String(clamp_x + 10, rod_y - 10, 'or tube', fontSize=7, fillColor=colors.black))
    
    # Connecting bracket from clamp to door
    d.add(Rect(clamp_x - 3, rod_y + 8, 6, 12, fillColor=colors.darkgrey, 
               strokeColor=colors.black, strokeWidth=1))
    
    # Door frame
    d.add(Rect(door_x, door_y, door_w, door_h, fillColor=colors.silver, 
               strokeColor=colors.black, strokeWidth=2))
    
    # Firebrick pattern (4 bricks)
    brick_w, brick_h = 45, 45
    for row in range(2):
        for col in range(2):
            brick_x = door_x + 5 + col * (brick_w + 2)
            brick_y = door_y + 15 + row * (brick_h + 5)
            d.add(Rect(brick_x, brick_y, brick_w, brick_h, fillColor=colors.tan, 
                      strokeColor=colors.brown, strokeWidth=1))
    
    # Handle on side of door
    handle_x = door_x + door_w
    handle_y = door_y + door_h/2
    d.add(Rect(handle_x, handle_y - 3, 30, 6, fillColor=colors.darkgrey, 
               strokeColor=colors.black, strokeWidth=1))
    d.add(String(handle_x + 5, handle_y - 15, 'Handle', fontSize=8, fillColor=colors.black))
    
    # Arrow showing slide direction
    arrow_y = door_y - 25
    d.add(Line(door_x, arrow_y, door_x + 60, arrow_y, strokeColor=colors.blue, 
               strokeWidth=2, strokeLineCap=1))
    d.add(Polygon([door_x + 60, arrow_y, door_x + 55, arrow_y - 5, door_x + 55, arrow_y + 5], 
                 fillColor=colors.blue, strokeColor=colors.blue))
    d.add(String(door_x + 10, arrow_y - 15, 'Slides on Rod', fontSize=9, fillColor=colors.blue))
    
    # Dimensions
    d.add(String(x + opening_w/2 - 10, y - 40, '9"W', fontSize=10, fillColor=colors.red))
    d.add(String(x - 35, y + opening_h/2, '11"H', fontSize=10, fillColor=colors.red))
    
    # Title
    d.add(String(width_px/2 - 90, height_px - 20, 'Round Rod Sliding Firebrick Door', fontSize=12, fillColor=colors.black))
    
    return d

def create_angle_iron_frame_drawing(width_px=400, height_px=300):
    """Create corner detail showing angle iron and bolted assembly"""
    d = Drawing(width_px, height_px)
    
    # Title
    d.add(String(width_px/2 - 80, height_px - 20, 'Bolted Corner Assembly', fontSize=12, fillColor=colors.black))
    
    # Draw a proper L-shaped angle iron as ONE piece
    x, y = 100, 80
    
    # Create angle iron as connected L-shape (single piece)
    # Vertical leg (2" tall)
    angle_v_width = 8
    angle_v_height = 100
    d.add(Rect(x, y, angle_v_width, angle_v_height, fillColor=colors.steelblue, 
               strokeColor=colors.black, strokeWidth=2))
    
    # Horizontal leg (2" wide)
    angle_h_width = 100
    angle_h_height = 8
    d.add(Rect(x, y, angle_h_width, angle_h_height, fillColor=colors.steelblue, 
               strokeColor=colors.black, strokeWidth=2))
    
    # Show this is ONE piece by adding corner detail
    d.add(String(x + 15, y - 20, '1/8" x 2" Angle Iron', fontSize=9, fillColor=colors.blue))
    d.add(String(x + 15, y - 30, '(L-shaped, one piece)', fontSize=8, fillColor=colors.blue))
    
    # Steel plates (THICKER and LONGER than angle)
    # Vertical plate (forge side wall)
    plate_thickness = 12  # 1/4" plate shown thicker
    plate1_x = x - plate_thickness
    plate1_height = 120
    d.add(Rect(plate1_x, y - 10, plate_thickness, plate1_height, fillColor=colors.lightgrey, 
               strokeColor=colors.black, strokeWidth=2))
    d.add(String(plate1_x - 60, y + 50, '1/4" Forge', fontSize=9, fillColor=colors.black))
    d.add(String(plate1_x - 60, y + 40, 'Side Plate', fontSize=9, fillColor=colors.black))
    
    # Horizontal plate (forge top/bottom)
    plate2_y = y - plate_thickness
    plate2_width = 120
    d.add(Rect(x - 10, plate2_y, plate2_width, plate_thickness, fillColor=colors.lightgrey, 
               strokeColor=colors.black, strokeWidth=2))
    d.add(String(x + 30, plate2_y - 15, '1/4" Top/Bottom Plate', fontSize=9, fillColor=colors.black))
    
    # Bolts going through plates into angle iron
    # Vertical bolts (through side plate into vertical leg of angle)
    bolt_v_y = [y + 20, y + 50, y + 80]
    for by in bolt_v_y:
        # Bolt shaft
        bolt_x_start = x - plate_thickness - 4
        bolt_x_end = x + 4
        d.add(Line(bolt_x_start, by, bolt_x_end, by, strokeColor=colors.grey, strokeWidth=4))
        # Bolt head
        d.add(Circle(bolt_x_start, by, 5, fillColor=colors.darkgrey, strokeColor=colors.black, strokeWidth=1.5))
        # Washer
        d.add(Circle(bolt_x_start, by, 7, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    
    # Horizontal bolts (through top plate into horizontal leg of angle)
    bolt_h_x = [x + 20, x + 50, x + 80]
    for bx in bolt_h_x:
        # Bolt shaft
        bolt_y_start = y - plate_thickness - 4
        bolt_y_end = y + 4
        d.add(Line(bx, bolt_y_start, bx, bolt_y_end, strokeColor=colors.grey, strokeWidth=4))
        # Bolt head
        d.add(Circle(bx, bolt_y_start, 5, fillColor=colors.darkgrey, strokeColor=colors.black, strokeWidth=1.5))
        # Washer
        d.add(Circle(bx, bolt_y_start, 7, fillColor=None, strokeColor=colors.black, strokeWidth=1))
    
    # Label bolts
    d.add(String(x - 70, y + 110, '5/16" or 3/8"', fontSize=9, fillColor=colors.black))
    d.add(String(x - 70, y + 100, 'Bolts', fontSize=9, fillColor=colors.black))
    
    # Arrow showing inside of forge
    d.add(String(x + 20, y + 30, 'Inside', fontSize=10, fillColor=colors.red))
    d.add(String(x + 20, y + 20, 'Forge', fontSize=10, fillColor=colors.red))
    
    # Detail note
    d.add(String(x + 110, y + 70, 'Angle sits at', fontSize=8, fillColor=colors.grey))
    d.add(String(x + 110, y + 60, 'inside corner,', fontSize=8, fillColor=colors.grey))
    d.add(String(x + 110, y + 50, 'plates bolt', fontSize=8, fillColor=colors.grey))
    d.add(String(x + 110, y + 40, 'to flanges', fontSize=8, fillColor=colors.grey))
    
    return d

def create_assembly_overview(width_px=500, height_px=400):
    """Create complete assembly overview"""
    d = Drawing(width_px, height_px)
    
    # Title
    d.add(String(width_px/2 - 80, height_px - 20, 'Complete Assembly View', fontSize=14, fillColor=colors.black))
    
    # Simplified forge body
    forge_x, forge_y = 100, 150
    forge_w, forge_h = 200, 80
    d.add(Rect(forge_x, forge_y, forge_w, forge_h, fillColor=colors.lightgrey, 
               strokeColor=colors.black, strokeWidth=2))
    
    # Burner on top (angled)
    burner_x = forge_x + 60
    burner_y = forge_y + forge_h
    d.add(Polygon([burner_x, burner_y, burner_x + 80, burner_y, 
                  burner_x + 70, burner_y + 40, burner_x - 10, burner_y + 40],
                 fillColor=colors.lightblue, strokeColor=colors.black, strokeWidth=2))
    d.add(String(burner_x + 20, burner_y + 50, 'Ribbon Burner', fontSize=10, fillColor=colors.black))
    
    # Stand legs
    leg_w = 8
    # Front left leg
    d.add(Rect(forge_x + 10, 50, leg_w, forge_y - 50, fillColor=colors.darkgrey, 
               strokeColor=colors.black, strokeWidth=1))
    # Front right leg
    d.add(Rect(forge_x + forge_w - 18, 50, leg_w, forge_y - 50, fillColor=colors.darkgrey, 
               strokeColor=colors.black, strokeWidth=1))
    
    # Door track extension (left side)
    track_extend = 80
    d.add(Rect(forge_x - track_extend, forge_y + 20, track_extend + 20, 6, 
               fillColor=colors.darkgrey, strokeColor=colors.black, strokeWidth=1))
    d.add(String(forge_x - track_extend + 10, forge_y + 30, 'Door Track', fontSize=8, fillColor=colors.black))
    
    # Door (partially open)
    door_x = forge_x - 50
    door_y = forge_y + 10
    d.add(Rect(door_x, door_y, 60, 70, fillColor=colors.tan, strokeColor=colors.black, strokeWidth=2))
    d.add(String(door_x + 10, door_y - 10, 'Sliding Door', fontSize=9, fillColor=colors.black))
    
    # Blower (side mounted)
    blower_x = forge_x + forge_w + 40
    blower_y = forge_y + 10
    d.add(Circle(blower_x, blower_y + 25, 25, fillColor=colors.grey, strokeColor=colors.black, strokeWidth=2))
    d.add(String(blower_x - 20, blower_y - 10, 'Blower', fontSize=9, fillColor=colors.black))
    
    # Air line
    d.add(Line(blower_x - 25, blower_y + 25, burner_x - 10, burner_y + 20, 
               strokeColor=colors.blue, strokeWidth=3))
    d.add(String(blower_x - 60, blower_y + 35, '1.5" Air', fontSize=8, fillColor=colors.blue))
    
    # Gas line
    gas_start_x = forge_x - 30
    gas_start_y = 80
    d.add(Line(gas_start_x, gas_start_y, burner_x - 10, burner_y + 10, 
               strokeColor=colors.red, strokeWidth=2))
    d.add(String(gas_start_x - 30, gas_start_y, 'Gas Line', fontSize=8, fillColor=colors.red))
    
    # Propane tank
    tank_x = gas_start_x - 10
    tank_y = 50
    d.add(Rect(tank_x, tank_y, 20, 40, fillColor=colors.yellow, strokeColor=colors.black, 
               strokeWidth=2, strokeLineCap=1))
    d.add(String(tank_x - 25, tank_y + 15, 'Propane', fontSize=8, fillColor=colors.black))
    
    return d

def save_drawing_as_image(drawing, filename):
    """Helper to save drawing for inclusion in PDF"""
    renderPDF.drawToFile(drawing, filename)

# Create the PDF
def generate_pdf():
    filename = "/home/gary/ribbon_burner_forge_design.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for content
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#444444'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    body_style = styles['BodyText']
    
    # Title Page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("Forced Air Ribbon Burner Forge", title_style))
    story.append(Paragraph("Complete Design & Build Guide", heading_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Bolted Assembly with 1.5\" Air System", body_style))
    story.append(Paragraph("and Sliding Firebrick Doors", body_style))
    story.append(PageBreak())
    
    # Table of Contents
    story.append(Paragraph("Table of Contents", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    toc_data = [
        ["1.", "Materials & Design Overview"],
        ["2.", "Forge Body Construction"],
        ["3.", "Ribbon Burner Assembly"],
        ["4.", "Sliding Door System"],
        ["5.", "Bolted Frame Details"],
        ["6.", "Air & Gas Systems"],
        ["7.", "Assembly Instructions"],
        ["8.", "Bill of Materials"],
        ["9.", "Operation & Safety"],
    ]
    
    toc_table = Table(toc_data, colWidths=[0.5*inch, 5*inch])
    toc_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(toc_table)
    story.append(PageBreak())
    
    # Section 1: Materials & Overview
    story.append(Paragraph("1. Materials & Design Overview", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("Materials Available:", subheading_style))
    materials_data = [
        ["Qty", "Dimension", "Purpose"],
        ["2", "1/4\" × 14\" × 30\" steel plates", "Side panels"],
        ["2", "1/4\" × 12\" × 14\" steel plates", "End panels (doors)"],
        ["2", "1/4\" × 12\" × 30\" steel plates", "Top & bottom"],
        ["TBD", "1/8\" × 2\" angle iron", "Frame & tracks"],
    ]
    
    materials_table = Table(materials_data, colWidths=[0.8*inch, 2.5*inch, 3*inch])
    materials_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(materials_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Design Features:", subheading_style))
    story.append(Paragraph("• <b>Bolted construction</b> using angle iron frame for easy disassembly", body_style))
    story.append(Paragraph("• <b>1.5\" air system</b> with 120-150 CFM blower", body_style))
    story.append(Paragraph("• <b>Ribbon burner</b> with 24 holes for even heat distribution", body_style))
    story.append(Paragraph("• <b>Sliding firebrick doors</b> on front and rear", body_style))
    story.append(Paragraph("• <b>Internal chamber:</b> 7.5\"W × 9\"H × 25.5\"L (after lining)", body_style))
    story.append(Paragraph("• <b>Temperature range:</b> Up to 2400-2500°F (forge welding heat)", body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Add complete assembly drawing
    story.append(create_assembly_overview(500, 350))
    story.append(PageBreak())
    
    # Section 2: Forge Body Construction
    story.append(Paragraph("2. Forge Body Construction", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("Bolted Box Assembly:", subheading_style))
    story.append(Paragraph("The forge body is assembled using 1/8\" × 2\" angle iron as an internal corner frame. "
                          "All six steel plates bolt to the angle iron flanges, creating a rigid yet disassembleable structure.", 
                          body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Add 3D box drawing
    story.append(create_3d_box_drawing(450, 300))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Dimensions:", subheading_style))
    dimensions_data = [
        ["Measurement", "External", "Internal (Before Lining)", "Internal (After Lining)"],
        ["Width", "12\"", "11.5\"", "7.5\""],
        ["Height", "14\"", "13.5\"", "9\""],
        ["Length", "30\"", "29.5\"", "25.5\""],
    ]
    
    dim_table = Table(dimensions_data, colWidths=[1.5*inch, 1.3*inch, 2*inch, 1.8*inch])
    dim_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(dim_table)
    story.append(PageBreak())
    
    # Section 3: Ribbon Burner
    story.append(Paragraph("3. Ribbon Burner Assembly", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("The ribbon burner is the heart of the forge, providing even heat distribution "
                          "across the chamber width.", body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Add burner drawing
    story.append(create_burner_drawing(450, 300))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Specifications:", subheading_style))
    burner_specs = [
        ["Component", "Specification"],
        ["Housing", "3\" × 3\" square steel tubing, 12\" long"],
        ["Air Inlet", "1.5\" diameter pipe, 6\" stub"],
        ["Refractory Head", "3\" deep castable refractory"],
        ["Flame Holes", "24 holes, 1/4\" diameter"],
        ["Hole Pattern", "3 rows of 8, staggered"],
        ["Gas Injection", "1/4\" pipe into air inlet"],
        ["Mounting Angle", "30-45° downward"],
    ]
    
    burner_table = Table(burner_specs, colWidths=[2*inch, 4*inch])
    burner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(burner_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Construction Steps:", subheading_style))
    story.append(Paragraph("1. Cut 3\"×3\" square tube to 12\" length", body_style))
    story.append(Paragraph("2. Drill 1.5\" hole and weld air inlet pipe stub", body_style))
    story.append(Paragraph("3. Install internal baffle plate for gas/air mixing", body_style))
    story.append(Paragraph("4. Drill 1/4\" hole for gas injection pipe", body_style))
    story.append(Paragraph("5. Build mold and cast refractory head with 24 straws", body_style))
    story.append(Paragraph("6. Cure 24-48 hours, then oven cure at 200-250°F", body_style))
    story.append(PageBreak())
    
    # Section 4: Sliding Door System
    story.append(Paragraph("4. Sliding Firebrick Door System", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("The sliding door system provides superior control over heat retention and chamber access. "
                          "Firebrick insulation in steel frames slides on angle iron tracks.", body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Add door drawing
    story.append(create_door_drawing(450, 320))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Door Specifications:", subheading_style))
    door_specs = [
        ["Feature", "Front Door", "Rear Door"],
        ["Opening Size", "9\"W × 11\"H", "7\"W × 9\"H"],
        ["Door Frame Size", "10\"W × 12\"H × 3\"D", "8\"W × 10\"H × 3\"D"],
        ["Firebricks", "4-6 IFB", "2-3 IFB"],
        ["Track Length", "24\" (extends 12\")", "18\" (extends 8-10\")"],
        ["Operation", "Slides horizontally", "Slides horizontally"],
    ]
    
    door_table = Table(door_specs, colWidths=[2*inch, 2*inch, 2*inch])
    door_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(door_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Advantages of Sliding Doors:", subheading_style))
    story.append(Paragraph("• One-handed operation", body_style))
    story.append(Paragraph("• Infinite positioning (not just open/closed)", body_style))
    story.append(Paragraph("• Doors stay in place (won't fall out)", body_style))
    story.append(Paragraph("• Firebrick provides excellent insulation", body_style))
    story.append(Paragraph("• No need to find place for removed door", body_style))
    story.append(PageBreak())
    
    # Section 5: Bolted Frame Details
    story.append(Paragraph("5. Bolted Frame Construction Details", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("The angle iron frame creates a strong, rigid structure while allowing complete disassembly. "
                          "This is especially valuable for maintenance and modifications.", body_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Add angle iron detail drawing
    story.append(create_angle_iron_frame_drawing(450, 300))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Frame Components:", subheading_style))
    frame_parts = [
        ["Component", "Quantity", "Length", "Purpose"],
        ["Corner Posts", "4", "14\"", "Vertical corners"],
        ["Edge Reinforcement", "4", "30\"", "Top/bottom edges (optional)"],
        ["Door Frame Pieces", "8", "13\"", "Around door openings"],
        ["Sliding Tracks", "4", "18-24\"", "Door slide rails"],
        ["Burner Mount", "4", "4-14\"", "Angled burner support"],
    ]
    
    frame_table = Table(frame_parts, colWidths=[2*inch, 1*inch, 1*inch, 2.5*inch])
    frame_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(frame_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Bolt Specifications:", subheading_style))
    story.append(Paragraph("• <b>Size:</b> 5/16\" or 3/8\" diameter", body_style))
    story.append(Paragraph("• <b>Grade:</b> Grade 5 minimum (Grade 8 recommended)", body_style))
    story.append(Paragraph("• <b>Quantity:</b> 60-80 bolts for complete assembly", body_style))
    story.append(Paragraph("• <b>Hardware:</b> Use flat washers and lock washers", body_style))
    story.append(Paragraph("• <b>Spacing:</b> 3-4\" on center along angle iron", body_style))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Assembly Advantages:", subheading_style))
    story.append(Paragraph("✓ Complete disassembly for maintenance", body_style))
    story.append(Paragraph("✓ Easy to replace damaged components", body_style))
    story.append(Paragraph("✓ No welding distortion", body_style))
    story.append(Paragraph("✓ Can modify or upgrade later", body_style))
    story.append(Paragraph("✓ Easier to transport (disassembled)", body_style))
    story.append(PageBreak())
    
    # Section 6: Air & Gas Systems
    story.append(Paragraph("6. Air & Gas Supply Systems", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("1.5\" Air System:", subheading_style))
    air_components = [
        ["Component", "Specification"],
        ["Blower", "120-150 CFM centrifugal forge blower"],
        ["Pipe Size", "1.5\" throughout"],
        ["Control Valve", "1.5\" gate valve"],
        ["Speed Control", "Variable (ceiling fan controller, NOT dimmer)"],
        ["Flexible Connection", "1.5\" silicone hose, 12-18\""],
        ["Total Length", "Under 6 feet recommended"],
    ]
    
    air_table = Table(air_components, colWidths=[2*inch, 4.5*inch])
    air_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(air_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Propane Gas System:", subheading_style))
    gas_components = [
        ["Component", "Specification"],
        ["Propane Tank", "20-100 lb cylinder"],
        ["Regulator", "Adjustable 0-30 PSI"],
        ["Pressure Gauge", "0-15 PSI display"],
        ["Main Shutoff", "1/4\" ball valve"],
        ["Solenoid Valve", "1/4\" normally closed (optional but recommended)"],
        ["Fine Adjustment", "1/4\" needle valve"],
        ["Gas Line", "1/4\" black iron pipe or propane hose"],
        ["Operating Pressure", "5-10 PSI typical"],
    ]
    
    gas_table = Table(gas_components, colWidths=[2*inch, 4.5*inch])
    gas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(gas_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Safety Note:</b> Always leak test the entire gas system with soapy water before operation. "
                          "Install a solenoid valve wired to blower power to prevent gas flow without airflow.", 
                          body_style))
    story.append(PageBreak())
    
    # Section 7: Assembly Instructions
    story.append(Paragraph("7. Assembly Instructions Summary", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    assembly_phases = [
        ["Phase", "Tasks", "Time"],
        ["1. Frame Fabrication", "Cut angle iron, drill holes, create template", "4-6 hrs"],
        ["2. Plate Preparation", "Cut openings, drill bolt holes, deburr", "4-6 hrs"],
        ["3. Test Fit", "Bolt together, check square, adjust", "2-3 hrs"],
        ["4. Door System", "Install frames, build door assemblies", "6-8 hrs"],
        ["5. Burner Build", "Fabricate housing, cast refractory", "4-6 hrs"],
        ["6. Final Assembly", "Bolt forge, install burner, seal", "2-3 hrs"],
        ["7. Refractory Lining", "Install floor, blanket, rigidizer", "4-6 hrs"],
        ["8. Plumbing", "Build stand, run air/gas lines", "6-8 hrs"],
        ["9. Curing", "Low heat burns, increase temp", "3-7 days"],
    ]
    
    assembly_table = Table(assembly_phases, colWidths=[1.2*inch, 3.7*inch, 1.6*inch])
    assembly_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(assembly_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("<b>Total Active Build Time:</b> 30-43 hours (plus cure time)", body_style))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Critical Assembly Notes:", subheading_style))
    story.append(Paragraph("• Use the angle iron frame as a drilling template for plates", body_style))
    story.append(Paragraph("• Drill bolt holes slightly oversize (1/64\") for easy alignment", body_style))
    story.append(Paragraph("• Check for square during test fit before final assembly", body_style))
    story.append(Paragraph("• Allow refractory to cure fully before firing", body_style))
    story.append(Paragraph("• Leak test gas system before first use", body_style))
    story.append(Paragraph("• Break in forge gradually over 3-5 burns", body_style))
    story.append(PageBreak())
    
    # Section 8: Bill of Materials
    story.append(Paragraph("8. Complete Bill of Materials", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("Steel & Metal Components:", subheading_style))
    steel_bom = [
        ["Item", "Quantity", "Notes"],
        ["1/4\" steel plates", "As specified", "Already have"],
        ["1/8\" × 2\" angle iron", "150-300 ft", "Already have (partial)"],
        ["3\" × 3\" square tube", "12\"", "Burner housing"],
        ["1.5\" pipe", "24-36\"", "Air inlet & line"],
        ["1/4\" pipe", "12\"", "Gas injection"],
        ["1/8\" steel sheet", "4-5 sq ft", "Door faces, baffle"],
        ["1/2\" rod", "2 ft", "Door handles"],
        ["2\" square tube", "25-30 ft", "Stand (if not using angle)"],
    ]
    
    steel_table = Table(steel_bom, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
    steel_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(steel_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Refractory Materials:", subheading_style))
    refrac_bom = [
        ["Item", "Quantity", "Purpose"],
        ["Ceramic fiber blanket 2\"", "15 sq ft", "Wall/ceiling lining"],
        ["Castable refractory", "5-8 lbs", "Burner head"],
        ["IFB (Insulating Fire Brick)", "26-32 bricks", "Floor & doors"],
        ["Rigidizer", "1-2 quarts", "Seal blanket"],
        ["ITC-100 (or equivalent)", "1 pint", "IR coating (optional)"],
        ["Stainless pins/staples", "50-100", "Secure blanket"],
        ["Refractory cement", "1 quart", "Sealing"],
    ]
    
    refrac_table = Table(refrac_bom, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
    refrac_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(refrac_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Hardware & Components:", subheading_style))
    hardware_bom = [
        ["Item", "Quantity", "Notes"],
        ["5/16\" or 3/8\" bolts", "60-80", "Grade 5+, with washers"],
        ["Forge blower", "1", "120-150 CFM"],
        ["1.5\" gate valve", "1", "Air control"],
        ["Variable speed controller", "1", "Ceiling fan type"],
        ["Propane regulator", "1", "0-30 PSI adjustable"],
        ["Pressure gauge", "1", "0-15 PSI"],
        ["1/4\" ball valve", "1", "Main gas shutoff"],
        ["1/4\" needle valve", "1", "Fine adjustment"],
        ["1/4\" solenoid valve", "1", "Safety (optional)"],
        ["1/4\" pipe fittings", "Various", "Tees, elbows, nipples"],
        ["Fire extinguisher", "1", "ABC rated"],
    ]
    
    hardware_table = Table(hardware_bom, colWidths=[2.5*inch, 1*inch, 3*inch])
    hardware_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(hardware_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Estimated Total Cost:</b> $675-1,100 (excluding steel plates and angle iron you already have)", 
                          body_style))
    story.append(PageBreak())
    
    # Section 9: Operation & Safety
    story.append(Paragraph("9. Operation & Safety", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("Startup Procedure:", subheading_style))
    story.append(Paragraph("1. Slide doors to desired position", body_style))
    story.append(Paragraph("2. Open air gate valve fully", body_style))
    story.append(Paragraph("3. Start blower, wait 10-15 seconds", body_style))
    story.append(Paragraph("4. Open gas main valve", body_style))
    story.append(Paragraph("5. Slowly open needle valve", body_style))
    story.append(Paragraph("6. Ignite at door opening with long lighter", body_style))
    story.append(Paragraph("7. Adjust gas for desired heat", body_style))
    story.append(Paragraph("8. Fine-tune air for proper atmosphere", body_style))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Flame Tuning Guide:", subheading_style))
    flame_guide = [
        ["Flame Appearance", "Air/Gas Ratio", "Use Case"],
        ["Purple-blue with orange streaks", "Neutral (balanced)", "General forging"],
        ["More orange/yellow", "Reducing (less air)", "Forge welding"],
        ["Bright blue", "Oxidizing (excess air)", "Maximum heat (causes scale)"],
    ]
    
    flame_table = Table(flame_guide, colWidths=[2.5*inch, 2*inch, 2*inch])
    flame_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(flame_table)
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("Shutdown Procedure:", subheading_style))
    story.append(Paragraph("1. Close gas needle valve", body_style))
    story.append(Paragraph("2. Keep blower running 60 seconds (purge gas)", body_style))
    story.append(Paragraph("3. Turn off blower", body_style))
    story.append(Paragraph("4. Allow forge to cool before fully closing doors", body_style))
    story.append(Paragraph("5. Never move forge while hot", body_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Safety Requirements:", subheading_style))
    story.append(Paragraph("<b>Required Safety Equipment:</b>", body_style))
    story.append(Paragraph("• ABC-rated fire extinguisher (within reach)", body_style))
    story.append(Paragraph("• Safety glasses (always wear)", body_style))
    story.append(Paragraph("• Leather gloves and apron", body_style))
    story.append(Paragraph("• Hearing protection (blower noise)", body_style))
    story.append(Paragraph("• Proper ventilation or exhaust hood", body_style))
    story.append(Paragraph("• CO detector in shop (recommended)", body_style))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Operational Safety:</b>", body_style))
    story.append(Paragraph("• Never operate in enclosed space without ventilation", body_style))
    story.append(Paragraph("• Keep combustibles 3+ feet from forge", body_style))
    story.append(Paragraph("• Leak test gas connections before each use (first few times)", body_style))
    story.append(Paragraph("• Never leave running forge unattended", body_style))
    story.append(Paragraph("• Check bolt tightness periodically (thermal cycling)", body_style))
    story.append(Paragraph("• Watch for pinch points on sliding doors", body_style))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("<b>Emergency Procedures:</b>", body_style))
    story.append(Paragraph("• <b>Gas leak:</b> Close tank valve immediately, ventilate area, find and repair leak", body_style))
    story.append(Paragraph("• <b>Fire outside forge:</b> Use fire extinguisher, close gas supply", body_style))
    story.append(Paragraph("• <b>Blower failure:</b> Close gas valve immediately", body_style))
    story.append(Paragraph("• <b>Flame blowing out:</b> Reduce both air and gas, let forge heat up first", body_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Expected Performance:", subheading_style))
    perf_data = [
        ["Parameter", "Specification"],
        ["Heat-up Time", "10-15 minutes to 2000°F"],
        ["Maximum Temperature", "2400-2500°F (forge welding heat)"],
        ["Even Heating Zone", "~12\" from ribbon burner"],
        ["Fuel Consumption", "5-10 PSI propane (varies with heat demand)"],
        ["Operating Cost", "Approximately $1-3/hour (propane prices vary)"],
    ]
    
    perf_table = Table(perf_data, colWidths=[2.5*inch, 4*inch])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(perf_table)
    story.append(PageBreak())
    
    # Final page - Notes
    story.append(Paragraph("Additional Notes & Tips", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("Maintenance Schedule:", subheading_style))
    story.append(Paragraph("<b>Monthly (heavy use):</b>", body_style))
    story.append(Paragraph("• Check bolt tightness", body_style))
    story.append(Paragraph("• Inspect door firebricks for cracks", body_style))
    story.append(Paragraph("• Clean sliding tracks", body_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Quarterly:</b>", body_style))
    story.append(Paragraph("• Inspect ceramic blanket condition", body_style))
    story.append(Paragraph("• Check for gas leaks", body_style))
    story.append(Paragraph("• Inspect refractory floor", body_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Annually:</b>", body_style))
    story.append(Paragraph("• Disassemble top plate, inspect chamber", body_style))
    story.append(Paragraph("• Replace damaged refractory", body_style))
    story.append(Paragraph("• Replace door firebricks if needed", body_style))
    story.append(Paragraph("• Deep clean entire forge", body_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Design Advantages:", subheading_style))
    story.append(Paragraph("✓ <b>Bolted construction</b> allows complete disassembly", body_style))
    story.append(Paragraph("✓ <b>1.5\" air system</b> is economical and adequate", body_style))
    story.append(Paragraph("✓ <b>Ribbon burner</b> provides even, efficient heating", body_style))
    story.append(Paragraph("✓ <b>Sliding doors</b> offer superior control and convenience", body_style))
    story.append(Paragraph("✓ <b>Professional-grade</b> performance for home shop", body_style))
    story.append(Paragraph("✓ <b>Materials on hand</b> reduces overall cost", body_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Troubleshooting Quick Reference:", subheading_style))
    troubleshoot = [
        ["Problem", "Solution"],
        ["Not reaching temperature", "Close doors more, increase gas, check for leaks"],
        ["Uneven heating", "Adjust burner angle, check all holes clear"],
        ["Excessive fuel use", "Fix gas leaks, repair refractory cracks"],
        ["Door binding", "Check track parallel, clean scale, adjust spacing"],
        ["Bolts loosening", "Use lock washers or Loctite, re-torque after first burns"],
        ["Flame blowing out", "Reduce air and gas, let forge heat up first"],
    ]
    
    trouble_table = Table(troubleshoot, colWidths=[2.5*inch, 4*inch])
    trouble_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(trouble_table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Design Attribution:", subheading_style))
    story.append(Paragraph("This forced air ribbon burner forge design incorporates principles from the "
                          "blacksmithing community's proven ribbon burner designs, adapted to utilize "
                          "specified steel plate dimensions and bolted construction for optimal performance "
                          "and maintainability.", body_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("<i>Document generated with technical illustrations for complete forge construction.</i>", 
                          body_style))
    
    # Build PDF
    doc.build(story)
    print(f"PDF generated successfully: {filename}")
    return filename

if __name__ == "__main__":
    generate_pdf()
