import bpy

from . import object_utils
from . import mesh_utils
from . import material_utils
from . import texture_utils

# --- Addon Information ---
bl_info = {
    "name": "GTA Utils",
    "author": "Don Zul",
    "version": (1, 0),
    "blender": (4, 0, 0), # Compatible with Blender 4.x
    "location": "3D Viewport > Sidebar > GTA Utils",
    "description": "Utility functions for processing GTA geometry.",
    "warning": "",
    "doc_url": "",
    "category": "Development",
}

#
# OBJECTS
#

class OT_Objects_ResetObjectData(bpy.types.Operator):
    bl_idname = "myaddon.objects_button1"
    bl_label = "Reset Object Data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Resetting object data...")
        object_utils.reset_object()
        return {'FINISHED'}

class OT_Objects_ExportSelectedToGLTF(bpy.types.Operator):
    bl_idname = "myaddon.objects_button2"
    bl_label = "Export Selected Objects to GLTF"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Exporting Objects...")
        object_utils.export_selected_objects_to_gltf()
        return {'FINISHED'}

#
# MESHES
#

class OT_Meshes_ValidateMesh(bpy.types.Operator):
    bl_idname = "myaddon.meshes_button1"
    bl_label = "Validate Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Validating mesh...")
        mesh_utils.validate_mesh()
        return {'FINISHED'}

class OT_Meshes_MergeDuplicateVertices(bpy.types.Operator):
    bl_idname = "myaddon.meshes_button2"
    bl_label = "Merge Duplicate Vertices"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Merging duplicate vertices...")
        mesh_utils.merge_duplicate_vertices()
        return {'FINISHED'}

class OT_Meshes_ResetNormals(bpy.types.Operator):
    bl_idname = "myaddon.meshes_button3"
    bl_label = "Reset Normals"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Resetting normals...")
        mesh_utils.reset_normals()
        return {'FINISHED'}

class OT_Meshes_RemoveDuplicateMeshes(bpy.types.Operator):
    bl_idname = "myaddon.meshes_button4"
    bl_label = "Remove duplicate meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Removing duplicate meshes...")
        mesh_utils.remove_duplicate_meshes()
        return {'FINISHED'}

#
# MATERIALS
#

class OT_Materials_RemoveUnusedMaterialSlots(bpy.types.Operator):
    bl_idname = "myaddon.materials_button1"
    bl_label = "Remove Unused Material Slots"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Removing unused material slots...")
        material_utils.remove_unused_material_slots()
        return {'FINISHED'}

class OT_Materials_RemoveDuplicateMaterialSlots(bpy.types.Operator):
    bl_idname = "myaddon.materials_button2"
    bl_label = "Remove Duplicate Material Slots"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Removing duplicate material slots...")
        material_utils.remove_duplicate_material_slots()
        return {'FINISHED'}

class OT_Materials_RemoveDuplicateMaterials(bpy.types.Operator):
    bl_idname = "myaddon.materials_button3"
    bl_label = "Remove Duplicate Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Removing duplicate materials...")
        material_utils.remove_duplicate_materials()
        return {'FINISHED'}

#
# TEXTURES
#

class OT_Textures_RemoveDuplicateImages(bpy.types.Operator):
    bl_idname = "myaddon.textures_button1" 
    bl_label = "Remove Duplicate Images" # Changed for clarity and uniqueness
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Removing duplicate images...")
        texture_utils.remove_duplicate_images()
        return {'FINISHED'}

class OT_Textures_RemapTextures(bpy.types.Operator):
    bl_idname = "myaddon.textures_button2" # Changed from myaddon.materials_button1
    bl_label = "Remap Textures" # Changed for clarity and uniqueness
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Remapping textures...")
        texture_utils.remap_textures()
        return {'FINISHED'}

# --- Panel UI Layout ---

class PT_Panel(bpy.types.Panel):
    bl_label = "GTA Utils" # Title of the addon
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Utils' # Name of the tab in the sidebar

    def draw(self, context):
        layout = self.layout

        # --- Section  ---
        box_obj = layout.box()
        box_obj.label(text="Objects", icon='OBJECT_DATA') # Subtitle for Section 1
        box_obj.row().operator(OT_Objects_ResetObjectData.bl_idname, text="Reset Object") # Button with icon
        box_obj.row().operator(OT_Objects_ExportSelectedToGLTF.bl_idname, text="Export Selected GLTF") # Button with icon

        # --- Section 1 ---
        box1 = layout.box()
        box1.label(text="Meshes", icon='MESH_DATA') # Subtitle for Section 1
        box1.row().operator(OT_Meshes_ValidateMesh.bl_idname, text="Validate Mesh") # Button with icon
        box1.row().operator(OT_Meshes_MergeDuplicateVertices.bl_idname, text="Merge Duplicate Vertices") # Button with icon
        box1.row().operator(OT_Meshes_ResetNormals.bl_idname, text="Reset Normals") # Button with icon
        box1.row().operator(OT_Meshes_RemoveDuplicateMeshes.bl_idname, text="Remove Duplicate Meshes") # Button with icon

        # --- Section 2 ---
        box2 = layout.box()
        box2.label(text="Materials", icon='MATERIAL') # Subtitle for Section 2
        box2.row().operator(OT_Materials_RemoveUnusedMaterialSlots.bl_idname, text="Remove Unused Material Slots") # Button with icon (changed icon)
        box2.row().operator(OT_Materials_RemoveDuplicateMaterialSlots.bl_idname, text="Remove Duplicate Material Slots") # Button with icon (changed icon)
        box2.row().operator(OT_Materials_RemoveDuplicateMaterials.bl_idname, text="Remove Duplicate Materials") # Button with icon (changed icon)

        # --- Section 3 ---
        box3 = layout.box()
        box3.label(text="Textures", icon='TEXTURE') # Subtitle for Section 3
        box3.row().operator(OT_Textures_RemoveDuplicateImages.bl_idname, text="Remove Duplicate Images") # Button with icon (changed icon)
        box3.row().operator(OT_Textures_RemapTextures.bl_idname, text="Remap Textures") # Button with icon (changed icon)

# --- Registration ---

classes = [
    OT_Objects_ResetObjectData,
    OT_Objects_ExportSelectedToGLTF,
    OT_Meshes_ValidateMesh,
    OT_Meshes_MergeDuplicateVertices,
    OT_Meshes_ResetNormals,
    OT_Meshes_RemoveDuplicateMeshes,
    OT_Materials_RemoveUnusedMaterialSlots,
    OT_Materials_RemoveDuplicateMaterialSlots,
    OT_Materials_RemoveDuplicateMaterials,
    OT_Textures_RemoveDuplicateImages,
    OT_Textures_RemapTextures,
    PT_Panel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("Addon Registered")

def unregister():
    for cls in reversed(classes): # Unregister in reverse order
        bpy.utils.unregister_class(cls)
    print("Addon Unregistered")

if __name__ == "__main__":
    register()