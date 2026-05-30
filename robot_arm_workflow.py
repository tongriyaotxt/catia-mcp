"""Robot arm design workflow — built from LOW-LEVEL tools, no encapsulation.

This script demonstrates how to design a complete 2-DOF robotic arm using
only the raw CATIA MCP tools (sketches, pads, pockets, holes, patterns,
axis systems).  Each step is explicit so you can modify any dimension or
feature independently.

Run this file directly:  python robot_arm_workflow.py
"""

from catia_mcp.tools import (
    document,
    sketcher,
    part_design,
    parameters,
    axis_systems,
    export,
)
from catia_mcp.connection import _get_pycatia_part_doc
import math


def design_robot_arm():
    # =====================================================================
    # 0. Setup
    # =====================================================================
    document.close_all_documents()
    document.new_document("Part")
    part_doc = _get_pycatia_part_doc()
    part = part_doc.part

    # Add key dimensions as parameters so the arm is fully parametric
    parameters.add_parameter("BaseDiameter", 180.0, "Length")
    parameters.add_parameter("BaseThickness", 25.0, "Length")
    parameters.add_parameter("ShoulderHeight", 120.0, "Length")
    parameters.add_parameter("UpperArmLength", 280.0, "Length")
    parameters.add_parameter("ElbowOffset", 100.0, "Length")
    parameters.add_parameter("ForeArmLength", 220.0, "Length")
    parameters.add_parameter("JointAxisDia", 20.0, "Length")
    parameters.add_parameter("BoltDia", 8.0, "Length")
    print("Parameters created")

    # =====================================================================
    # 1. BASE PLATE  (cylinder + bolt holes + center bore)
    # =====================================================================
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 90)          # BaseDiameter/2
    sketcher.close_sketch()
    part_design.create_pad(25.0)            # BaseThickness

    # Center bore (pocket through)
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 25)
    sketcher.close_sketch()
    part_design.create_pocket(26.0)         # through

    # 6 bolt holes on PCD=140
    bolt_pcd = 70.0
    bolt_r = 4.0
    for i in range(6):
        a = math.radians(i * 60)
        x = bolt_pcd * math.cos(a)
        y = bolt_pcd * math.sin(a)
        sketcher.create_sketch_on_plane("xy")
        sketcher.add_circle(x, y, bolt_r)
        sketcher.close_sketch()
        part_design.create_pocket(26.0)
    print("Base plate done")

    # Base coordinate frame (Z = rotation axis of shoulder)
    axis_systems.create_axis_system("Frame_Base", 0, 0, 25.0)

    # =====================================================================
    # 2. SHOULDER JOINT  (vertical revolute axis)
    # =====================================================================
    # Main cylinder (hollow) sitting on base
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 40)
    sketcher.close_sketch()
    part_design.create_pad(120.0)           # ShoulderHeight

    # Hollow bore for shoulder shaft
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 10)
    sketcher.close_sketch()
    part_design.create_pocket(121.0)        # through

    # Bearing seat at top (Z=120)
    # We'll create a second body for the seat and boolean-add it
    shoulder_seat_body = part.bodies.add()
    shoulder_seat_body.name = "ShoulderSeat"
    part.in_work_object = shoulder_seat_body
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 55)
    sketcher.close_sketch()
    part_design.create_pad(15.0)
    part.in_work_object = part.bodies.item(1)
    # Boolean add the seat to main body
    from pycatia.part_interfaces.shape_factory import ShapeFactory
    sf = ShapeFactory(part.shape_factory.com_object)
    sf.add_new_add(shoulder_seat_body)
    part.update()

    # Bearing seat pocket (recess)
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 35)
    sketcher.close_sketch()
    part_design.create_pocket(8.0)

    axis_systems.create_axis_system("Frame_Shoulder", 0, 0, 120.0)
    print("Shoulder joint done")

    # =====================================================================
    # 3. UPPER ARM  (box tube, 280 mm long)
    # =====================================================================
    upper_arm_body = part.bodies.add()
    upper_arm_body.name = "UpperArm"
    part.in_work_object = upper_arm_body

    # Outer profile on XY, extrude along Z
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_rectangle(-25, -20, 25, 20)
    sketcher.close_sketch()
    part_design.create_pad(280.0)

    # Inner void (pocket) to make it hollow — create on offset sketch
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_rectangle(-20, -15, 20, 15)
    sketcher.close_sketch()
    part_design.create_pocket(281.0)        # through

    # Joint axis holes at both ends
    # Near end (Z=0)
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 10)
    sketcher.close_sketch()
    part_design.create_pocket(281.0)

    # Far end (Z=280) — create hole on the main body using a sketch on offset plane
    from pycatia.hybrid_shape_interfaces.hybrid_shape_factory import HybridShapeFactory
    hsf = HybridShapeFactory(part.hybrid_shape_factory.com_object)
    end_plane = hsf.add_new_plane_offset(part.origin_elements.plane_xy, 280.0, True)
    hb = part.hybrid_bodies.add()
    hb.name = "UpperArmConstruction"
    hb.append_hybrid_shape(end_plane)
    part.update()

    # Switch back to main body for the hole sketch
    part.in_work_object = part.bodies.item(1)
    sketch = part.bodies.item(1).sketches.add(end_plane)
    factory = sketch.open_edition()
    factory.create_closed_circle(0, 0, 10)
    sketch.close_edition()
    part_design.create_pocket(281.0)
    part.update()

    part.in_work_object = part.bodies.item(1)
    axis_systems.create_axis_system("Frame_UpperArm_End", 0, 0, 280.0)
    print("Upper arm done")

    # =====================================================================
    # 4. ELBOW JOINT  (horizontal revolute axis)
    # =====================================================================
    elbow_body = part.bodies.add()
    elbow_body.name = "ElbowJoint"
    part.in_work_object = elbow_body

    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 35)
    sketcher.close_sketch()
    part_design.create_pad(80.0)

    # Shaft bore
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 10)
    sketcher.close_sketch()
    part_design.create_pocket(81.0)

    part.in_work_object = part.bodies.item(1)
    axis_systems.create_axis_system("Frame_Elbow", 0, 0, 360.0)
    print("Elbow joint done")

    # =====================================================================
    # 5. FOREARM  (220 mm)
    # =====================================================================
    forearm_body = part.bodies.add()
    forearm_body.name = "Forearm"
    part.in_work_object = forearm_body

    sketcher.create_sketch_on_plane("xy")
    sketcher.add_rectangle(-20, -15, 20, 15)
    sketcher.close_sketch()
    part_design.create_pad(220.0)

    sketcher.create_sketch_on_plane("xy")
    sketcher.add_rectangle(-15, -10, 15, 10)
    sketcher.close_sketch()
    part_design.create_pocket(221.0)

    # Axis hole near end
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 8)
    sketcher.close_sketch()
    part_design.create_pocket(221.0)

    part.in_work_object = part.bodies.item(1)
    axis_systems.create_axis_system("Frame_Forearm_End", 0, 0, 580.0)
    print("Forearm done")

    # =====================================================================
    # 6. END-EFFECTOR MOUNT
    # =====================================================================
    mount_body = part.bodies.add()
    mount_body.name = "EndEffectorMount"
    part.in_work_object = mount_body

    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 40)
    sketcher.close_sketch()
    part_design.create_pad(12.0)

    # Center bore
    sketcher.create_sketch_on_plane("xy")
    sketcher.add_circle(0, 0, 12)
    sketcher.close_sketch()
    part_design.create_pocket(13.0)

    # 4 tool bolts on PCD=60
    for i in range(4):
        a = math.radians(i * 90 + 45)
        x = 30 * math.cos(a)
        y = 30 * math.sin(a)
        sketcher.create_sketch_on_plane("xy")
        sketcher.add_circle(x, y, 4)
        sketcher.close_sketch()
        part_design.create_pocket(13.0)

    part.in_work_object = part.bodies.item(1)
    axis_systems.create_axis_system("Frame_Tool", 0, 0, 592.0)
    print("End-effector mount done")

    # =====================================================================
    # 7. Feature tree & export
    # =====================================================================
    tree = part.bodies
    print(f"\nPart bodies: {tree.count}")
    for i in range(1, tree.count + 1):
        b = tree.item(i)
        print(f"  {i}. {b.name}")

    axes = axis_systems.list_axis_systems()
    print(f"\nAxis systems: {len(axes)}")
    for a in axes:
        print(f"  {a['name']} @ {a['origin']}")

    export.export_to_stl(r"D:\mcp-selfmade\robot_arm_demo.stl")
    print("\nSTL exported to robot_arm_demo.stl")

    # Keep document open for inspection
    print("\n=== ROBOT ARM DESIGN COMPLETE ===")


if __name__ == "__main__":
    try:
        design_robot_arm()
    except Exception as e:
        print(f"\n=== DESIGN FAILED: {e} ===")
        import traceback
        traceback.print_exc()
