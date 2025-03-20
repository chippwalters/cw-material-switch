bl_info = {
    "name": "Material Toggle Addon",
    "blender": (4, 3, 0),
    "category": "Tool",
    "author": "Chipp Walters",
    "version": (1, 0, 13),
    "description": "Toggle between Original, White, and Custom material states with three buttons and a material dropdown."
}

import bpy
import inspect

# Property Group to store material names
class OriginalMaterialProperties(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()

class FaceMaterialIndicesProperties(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty()

# Operator for Original Material
class OBJECT_OT_original_material(bpy.types.Operator):
    bl_idname = "object.original_material"
    bl_label = "Original"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.original_material and obj.face_material_indices:
                for mat in obj.original_material:
                    mat_data = bpy.data.materials.get(mat.name)
                    if mat_data:
                        mat_data.use_fake_user = False

                obj.data.materials.clear()
                for mat in obj.original_material:
                    mat_data = bpy.data.materials.get(mat.name)
                    if mat_data:
                        obj.data.materials.append(mat_data)

                for poly, mat_index in zip(obj.data.polygons, obj.face_material_indices):
                    poly.material_index = mat_index.index

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
                    if obj.is_override:
                        continue
                    if context.scene.toggle_material_state == 'ORIGINAL':
                        obj.original_material.clear()
                        obj.face_material_indices.clear()

                        for slot in obj.material_slots:
                            if slot.material:
                                mat_entry = obj.original_material.add()
                                mat_entry.name = slot.material.name
                                slot.material.use_fake_user = True  # ✅ Store Fake User when switching from Original

                        for poly in obj.data.polygons:
                            index_entry = obj.face_material_indices.add()
                            index_entry.index = poly.material_index

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
            white_mat = self.create_white_material()

        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                if obj.is_override:
                    continue
                if context.scene.toggle_material_state == 'ORIGINAL':
                    obj.original_material.clear()
                    obj.face_material_indices.clear()

                    for slot in obj.material_slots:
                        if slot.material:
                            mat_entry = obj.original_material.add()
                            mat_entry.name = slot.material.name
                            slot.material.use_fake_user = True  # ✅ Store Fake User when switching from Original

                    for poly in obj.data.polygons:
                        index_entry = obj.face_material_indices.add()
                        index_entry.index = poly.material_index

                obj.data.materials.clear()
                obj.data.materials.append(white_mat)
                for poly in obj.data.polygons:
                    poly.material_index = 0

        context.scene.toggle_material_state = 'WHITE'
        return {'FINISHED'}


    
    def create_white_material(self):
        white_mat = bpy.data.materials.new(name="cw-white")
        white_mat.use_fake_user = True
        white_mat.use_nodes = True
        bsdf = white_mat.node_tree.nodes.get('Principled BSDF')
        
        # Set Base Color to white
        bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
        
        # Blender 4.3 compatibility check for the 'Specular' input
        bsdf.inputs[13].default_value = 0.0
        
        # Set roughness for a matte finish
        bsdf.inputs['Roughness'].default_value = 1.0
        return white_mat

# UI Panel with three buttons and a dropdown for custom material
class VIEW3D_PT_material_toggle_panel(bpy.types.Panel):
    bl_label = "Switch Material"
    bl_idname = "VIEW3D_PT_material_toggle_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw_header_preset(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}")
#        row.label(text=f"v{addon_version[0]}.{addon_version[1]}.{addon_version[2]}")
        row.operator("ssp.open_help_url", icon='QUESTION',
                     text="").url = "http://cw1.me/ssp"
        row.separator()    
    
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("object.original_material", depress=(context.scene.toggle_material_state == 'ORIGINAL'))           
        row.operator("object.white_material", depress=(context.scene.toggle_material_state == 'WHITE'))
        row.operator("object.custom_material", depress=(context.scene.toggle_material_state == 'CUSTOM'))
        layout.prop(context.scene, "custom_material", text="Custom Material")

def update_custom_material(self, context):
    bpy.ops.object.custom_material()

def get_material_list(self, context):
    return [(mat.name, mat.name, "Select this material") for mat in bpy.data.materials]

# Registration
classes = (
    OriginalMaterialProperties,
    FaceMaterialIndicesProperties,
    VIEW3D_PT_material_toggle_panel,
    OBJECT_OT_original_material,
    OBJECT_OT_custom_material,
    OBJECT_OT_white_material
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.toggle_material_state = bpy.props.StringProperty(default="ORIGINAL")
    bpy.types.Scene.custom_material = bpy.props.EnumProperty(
        name="Custom Material",
        items=get_material_list,
        update=update_custom_material
    )
    bpy.types.Object.is_override = bpy.props.BoolProperty(default=False)
    bpy.types.Object.original_material = bpy.props.CollectionProperty(type=OriginalMaterialProperties)
    bpy.types.Object.face_material_indices = bpy.props.CollectionProperty(type=FaceMaterialIndicesProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.toggle_material_state
    del bpy.types.Scene.custom_material
    del bpy.types.Object.is_override
    del bpy.types.Object.original_material
    del bpy.types.Object.face_material_indices

if __name__ == "__main__":
    register()
