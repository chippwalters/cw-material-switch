bl_info = {
    "name": "Material Toggle Addon",
    "blender": (4, 3, 0),
    "category": "Tool",
    "author": "Chipp Walters",
    "version": (1, 0, 20),
    "description": "Toggle between Original, White, and Custom material states with three buttons and a material dropdown."
}

import bpy
import inspect

# Operator for Original Material
class OBJECT_OT_original_material(bpy.types.Operator):
    bl_idname = "object.original_material"
    bl_label = "Original"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and "original_material" in obj and "face_material_indices" in obj:
                for mat_name in obj["original_material"]:
                    mat = bpy.data.materials.get(mat_name)
                    if mat:
                        mat.use_fake_user = False

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
                    if "_is_override" in obj and obj["_is_override"]:
                        continue
                    if context.scene.toggle_material_state == 'ORIGINAL':
                        obj["original_material"] = [slot.material.name for slot in obj.material_slots if slot.material]
                        obj["face_material_indices"] = [poly.material_index for poly in obj.data.polygons]
                        for mat_name in obj["original_material"]:
                            mat = bpy.data.materials.get(mat_name)
                            if mat:
                                mat.use_fake_user = True

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
                if "_is_override" in obj and obj["_is_override"]:
                    continue
                if context.scene.toggle_material_state == 'ORIGINAL':
                    obj["original_material"] = [slot.material.name for slot in obj.material_slots if slot.material]
                    obj["face_material_indices"] = [poly.material_index for poly in obj.data.polygons]
                    for mat_name in obj["original_material"]:
                        mat = bpy.data.materials.get(mat_name)
                        if mat:
                            mat.use_fake_user = True

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


# Operator for Toggle Material Button
class OBJECT_OT_toggle_material(bpy.types.Operator):
    bl_idname = "object.toggle_material"
    bl_label = "Toggle Material"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.scene.toggle_material_state in {'WHITE', 'CUSTOM'}

    def execute(self, context):
        obj = context.active_object
        white_mat = bpy.data.materials.get("cw-white")
        custom_mat = bpy.data.materials.get(context.scene.custom_material)

        if context.scene.toggle_material_state == 'WHITE':
            if obj.active_material and obj.active_material.name == "cw-white":
                if "original_material" in obj and "face_material_indices" in obj:
                    obj.data.materials.clear()
                    for mat_name in obj["original_material"]:
                        mat = bpy.data.materials.get(mat_name)
                        if mat:
                            obj.data.materials.append(mat)
                    for poly, mat_index in zip(obj.data.polygons, obj["face_material_indices"]):
                        poly.material_index = mat_index
                    obj["_is_override"] = True
            else:
                obj.data.materials.clear()
                obj.data.materials.append(white_mat)
                for poly in obj.data.polygons:
                    poly.material_index = 0
                obj["_is_override"] = False

        elif context.scene.toggle_material_state == 'CUSTOM':
            if obj.active_material and obj.active_material == custom_mat:
                if "original_material" in obj and "face_material_indices" in obj:
                    obj.data.materials.clear()
                    for mat_name in obj["original_material"]:
                        mat = bpy.data.materials.get(mat_name)
                        if mat:
                            obj.data.materials.append(mat)
                    for poly, mat_index in zip(obj.data.polygons, obj["face_material_indices"]):
                        poly.material_index = mat_index
                    obj["_is_override"] = True
            else:
                obj.data.materials.clear()
                obj.data.materials.append(custom_mat)
                for poly in obj.data.polygons:
                    poly.material_index = 0
                obj["_is_override"] = False

        self.report({'INFO'}, "Toggle Material executed")
        return {'FINISHED'}



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
    VIEW3D_PT_material_toggle_panel,
    OBJECT_OT_original_material,
    OBJECT_OT_custom_material,
    OBJECT_OT_white_material,
    OBJECT_OT_toggle_material
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

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.toggle_material_state
    del bpy.types.Scene.custom_material


if __name__ == "__main__":
    register()