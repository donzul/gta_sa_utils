import bpy
import os
from mathutils import Matrix

def reset_object():
    """
    Resets the active object by creating a new object and linking its original mesh,
    while preserving the original object's world transform. It then deletes the original
    object and makes the newly created one active and selected, with the original name.
    """
    # Ensure we are in object mode
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')
    else:
        print("Could not set mode to OBJECT. Please ensure no editors are in a non-object mode that prevents it (e.g., Edit Mode).")
        return

    obj = bpy.context.active_object

    if not obj:
        print("Error: No object is selected and active. Please select a mesh object.")
        return

    if obj.type != 'MESH':
        print(f"Skipping '{obj.name}': Not a mesh object. Only mesh objects are supported for this reset operation.")
        return

    # Store original world matrix and mesh data
    original_world_matrix = obj.matrix_world.copy()
    original_mesh_data = obj.data # This is the actual Mesh data block
    original_name = obj.name # Store the original name
    original_rotation_mode = obj.rotation_mode # Store the rotation mode for consistency

    # Store the collections the original object is in
    original_collections = list(obj.users_collection)

    # Temporarily rename the old object to avoid name conflicts when creating the new one
    temp_old_name = original_name + "_TEMP_DEL"
    obj.name = temp_old_name
    print(f"Temporarily renamed old object to: '{temp_old_name}'")

    # Create a new object with the original name and preserved mesh data
    new_object = bpy.data.objects.new(original_name, original_mesh_data)

    # Set the world transform of the new object
    new_object.matrix_world = original_world_matrix
    new_object.rotation_mode = original_rotation_mode # Set the rotation mode

    # Link the new object to the same collections as the original
    for collection in original_collections:
        if new_object.name not in collection.objects: # Check if already linked
            collection.objects.link(new_object)

    # If the original object was linked to the scene collection (and not another specific one),
    # ensure the new object is also linked to the scene collection if it hasn't been linked elsewhere.
    if not new_object.users_collection: # If it's not in any other collection yet
        bpy.context.scene.collection.objects.link(new_object)

    # Make sure the new object is visible and selectable
    new_object.hide_set(False)
    new_object.hide_select = False
    new_object.hide_viewport = False
    new_object.hide_render = False

    print(f"Created new object: '{new_object.name}'.")

    # Deselect all objects in the scene to clear any lingering references
    bpy.ops.object.select_all(action='DESELECT')

    # Delete original object using its temporary name
    obj_to_del = bpy.data.objects.get(temp_old_name)
    if obj_to_del:
        bpy.data.objects.remove(obj_to_del, do_unlink=True)
        print(f"Deleted original object (temp name: '{temp_old_name}').")
    else:
        print(f"Original object '{temp_old_name}' already deleted or not found.")

    # Select the newly created object and set active
    if new_object.name in bpy.data.objects: # Check if the object actually exists in data
        new_object.select_set(True)
        bpy.context.view_layer.objects.active = new_object
    else:
        print(f"Warning: Newly created object '{new_object.name}' not found for selection.")

    print("--- Object Reset Process Complete ---")

def export_selected_objects_to_gltf():
    """
    Exports each selected object as a separate .gltf file with its textures
    saved in the same directory, not in a subfolder.
    """
    export_folder_name = "export_map"

    # Get the path of the current Blender file. It must be saved first.
    blend_file_path = bpy.data.filepath
    if not blend_file_path:
        print("Error: Please save your Blender file before running this script.")
        return {'CANCELLED'}

    # Get the directory where the Blender file is located
    base_dir = os.path.dirname(blend_file_path)

    # Define the full path for the main export folder
    export_dir = os.path.join(base_dir, export_folder_name)

    # Create the export directory if it does not exist
    os.makedirs(export_dir, exist_ok=True)

    # Get a copy of the list of currently selected objects
    selected_objects = bpy.context.selected_objects[:]

    if not selected_objects:
        print("No objects selected. Please select one or more objects to export.")
        return {'CANCELLED'}
        
    # Deselect all objects to ensure a clean export of each individual object
    bpy.ops.object.select_all(action='DESELECT')

    for obj in selected_objects:
        # We need to handle non-mesh objects gracefully
        if obj.type != 'MESH':
            print(f"Skipping '{obj.name}' as it is not a mesh object.")
            continue
            
        # Make the current object the only active and selected one
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # Define the export path and filename for the glTF file
        # It will be inside the main export folder.
        file_name = bpy.path.clean_name(obj.name) + ".gltf"
        export_path = os.path.join(export_dir, file_name)

        print(f"Exporting '{obj.name}' to '{export_path}'...")

        # Export the selected object as a separate glTF with its textures.
        # By setting export_texture_dir to "", textures are saved alongside the .gltf file.
        bpy.ops.export_scene.gltf(
            filepath=export_path,
            use_selection=True,  # Export only the selected object
            export_format='GLTF_SEPARATE',  # Creates .gltf, .bin, and texture files
            export_texture_dir="",  # Saves textures in the same folder as the gltf
            # export_keep_originals=True, # Recommended to avoid issues with texture paths
            
            # Optional: Other useful settings you might consider
            export_apply=True, # Apply modifiers (recommended)
            # export_colors=False, # Export vertex colors
            export_normals=False, # Export custom normals
            export_tangents=False, # Needed for some PBR materials
            export_materials='EXPORT', # Export materials
            export_animations=False, # Export animations
            export_lights=False, # Export lights
        )

        # Deselect the object after it has been exported
        obj.select_set(False)

    # Restore the original selection
    for obj in selected_objects:
        obj.select_set(True)
        
    success_message = f"Success! Exported {len(selected_objects)} objects to the '{export_folder_name}' folder."
    print(success_message)
    
    return {'FINISHED'}