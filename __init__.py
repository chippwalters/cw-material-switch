bl_info = {
    "name": "Material Toggle Addon",
    "blender": (4, 3, 0),
    "category": "Tool",
    "author": "Your Name",
    "version": (1, 0, 0),
    "description": "Toggle between Original, White, and Custom material states with three buttons and a material dropdown."
}

import bpy
import os
import inspect

# Load the "cw-white" material from the same directory as the Blender script file

def load_cw_white_material():
    script_path = os.path.abspath(inspect.getfile(lambda: None))
    print(f"Current script file path: {script_path}")
    blend_dir = os.path.dirname(script_path)
    blend_file_path = os.path.join(blend_dir, "cw-white.blend")
    print(f"Attempting to load blend file from: {blend_file_path}")
    material_name = "cw-white"
    
    if os.path.exists(blend_file_path):
        with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
            if material_name in data_from.materials:
                data_to.materials = [material_name]
            else:
                print(f"Material '{material_name}' not found in '{blend_file_path}'.")
    else:
        print(f"Blend file not found: {blend_file_path}")

# Operator for Original Material
class OBJECT_OT_original_material(bpy.types.Operator):
    bl_idname = "object.original_material"
    bl_label = "Original"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and "original_material" in obj and "face_material_indices" in obj:
                obj.data.materials.clear()
                for mat_name in obj["original_material"]:
                    mat = bpy.data.materials.get(mat_name)
                    if mat:
                        obj.data.materials.append(mat)
                for poly, mat_index in zip(obj.data.polygons, obj["face_material_indices"]):
                    poly.material_index = mat_index
        context.scene.toggle_material_state = 'ORIGINAL'
        return {'FINISHED'}

# Operator for Custom Material
class OBJECT_OT_custom_material(bpy.types.Operator):
    bl_idname = "object.custom_material"
    bl_label = "Custom"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        custom_mat = bpy.data.materials.get(context.scene.custom_material)
        if custom_mat:
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    if context.scene.toggle_material_state == 'ORIGINAL':
                        obj["original_material"] = [slot.material.name for slot in obj.material_slots if slot.material]
                        obj["face_material_indices"] = [poly.material_index for poly in obj.data.polygons]

                    obj.data.materials.clear()
                    obj.data.materials.append(custom_mat)
                    for poly in obj.data.polygons:
                        poly.material_index = 0
        context.scene.toggle_material_state = 'CUSTOM'
        return {'FINISHED'}

# Operator for White Material
class OBJECT_OT_white_material(bpy.types.Operator):
    bl_idname = "object.white_material"
    bl_label = "White"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        white_mat = bpy.data.materials.get("cw-white")
        if white_mat is None:
            white_mat = load_cw_white_material()

        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                if context.scene.toggle_material_state == 'ORIGINAL':
                    obj["original_material"] = [slot.material.name for slot in obj.material_slots if slot.material]
                    obj["face_material_indices"] = [poly.material_index for poly in obj.data.polygons]

                obj.data.materials.clear()
                obj.data.materials.append(white_mat)
                for poly in obj.data.polygons:
                    poly.material_index = 0

        context.scene.toggle_material_state = 'WHITE'
        return {'FINISHED'}

# UI Panel with three buttons and a dropdown for custom material
class VIEW3D_PT_material_toggle_panel(bpy.types.Panel):
    bl_label = "Switch Material"
    bl_idname = "VIEW3D_PT_material_toggle_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("object.original_material", depress=(context.scene.get('toggle_material_state') == 'ORIGINAL'))
        row.operator("object.white_material", depress=(context.scene.get('toggle_material_state') == 'WHITE'))
        row.operator("object.custom_material", depress=(context.scene.get('toggle_material_state') == 'CUSTOM'))
        layout.prop(context.scene, "custom_material", text="Custom Material")

# Function to dynamically update the material list

def get_material_list(self, context):
    return [(mat.name, mat.name, "Select this material") for mat in bpy.data.materials]

bpy.types.Scene.custom_material = bpy.props.EnumProperty(
    name="Custom Material",
    items=get_material_list
)

# Registration
def register():
    bpy.utils.register_class(OBJECT_OT_original_material)
    bpy.utils.register_class(OBJECT_OT_custom_material)
    bpy.utils.register_class(OBJECT_OT_white_material)
    bpy.utils.register_class(VIEW3D_PT_material_toggle_panel)
    bpy.types.Scene.toggle_material_state = bpy.props.StringProperty(default="ORIGINAL")
    load_cw_white_material()

    # Ensure the addon starts with the Original button highlighted
    bpy.context.scene.toggle_material_state = "ORIGINAL"

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_original_material)
    bpy.utils.unregister_class(OBJECT_OT_custom_material)
    bpy.utils.unregister_class(OBJECT_OT_white_material)
    bpy.utils.unregister_class(VIEW3D_PT_material_toggle_panel)
    del bpy.types.Scene.toggle_material_state
    del bpy.types.Scene.custom_material

if __name__ == "__main__":
    register()
