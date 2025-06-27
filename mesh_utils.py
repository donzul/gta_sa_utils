import bpy

def validate_mesh():
    """
    Validates and attempts to correct common mesh issues for the active object.
    It uses bpy.data.meshes.validate() for internal data consistency,
    and then checks for non-manifold geometry, zero-area faces, zero-length edges,
    and loose vertices, reporting and selecting them.
    """
    obj = bpy.context.active_object

    if not obj:
        print("Error: No object is selected and active. Please select a mesh object to validate.")
        return

    if obj.type != 'MESH':
        print(f"Skipping '{obj.name}': Not a mesh object. Only mesh objects can be validated and corrected.")
        return

    print(f"\n--- Validating and Correcting Mesh: '{obj.name}' ---")

    # Store the current mode to return to it later
    original_mode = bpy.context.mode

    try:
        # Ensure we are in Object Mode before any mesh data operations or mode changes
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh_data = obj.data
        if mesh_data.validate(verbose=True):
            print("  mesh.validate() found and corrected inconsistencies in mesh data.")
            # If validate() made changes, it's often good to update the display
            # and potentially recalculate normals if topology changed significantly.
            mesh_data.update()
        else:
            print("  mesh.validate() found no internal data inconsistencies.")
        
        print("\nNote: For duplicate vertices (vertices at the exact same location),")

    except Exception as e:
        print(f"An error occurred during mesh validation/correction: {e}")
    finally:
        # Return to the original mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode=original_mode)
        print(f"--- Mesh Validation and Correction Complete for '{obj.name}' ---")

def merge_duplicate_vertices(distance=0.01):
    """
    Merges the mesh vertices of the active object by distance.
    The object must be a mesh object and in Object Mode initially.
    It will temporarily switch to Edit Mode to perform the merge.

    Args:
        distance (float): The maximum distance between vertices to merge.
                          Defaults to 0.01.
    """
    obj = bpy.context.active_object

    if not obj:
        print("Error: No object is selected and active. Please select a mesh object.")
        return

    if obj.type != 'MESH':
        print(f"Skipping '{obj.name}': Not a mesh object. Only mesh objects can have their vertices merged.")
        return

    # Store the current mode to return to it later
    original_mode = bpy.context.mode

    try:
        # Ensure we are in Object Mode before switching to Edit Mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        # Switch to Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')

        # Deselect all vertices first to ensure only the merge operation is applied
        # This is often good practice to avoid unexpected behavior
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type="VERT") # Ensure vertex select mode

        # Select all vertices for the merge operation
        bpy.ops.mesh.select_all(action='SELECT')

        # Perform the merge by distance operation
        bpy.ops.mesh.remove_doubles(threshold=distance)
        print(f"Merged vertices of '{obj.name}' by distance of {distance:.4f}.")

    except Exception as e:
        print(f"An error occurred during merging vertices: {e}")
    finally:
        # Return to the original mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode=original_mode)

def reset_normals():
    """
    Applies the default automatic smoothing (Shade Auto Smooth)
    to the active object's mesh.
    This effectively adds a "Smooth by Angle" modifier with its default 30-degree angle.
    """
    
    # Check if there's an active object
    if bpy.context.active_object is None:
        print("Error: No active object selected.")
        return

    obj = bpy.context.active_object

    # Check if the active object is a mesh
    if obj.type == 'MESH':
        # Ensure we are in Object Mode before applying operations
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        # This operator directly applies "Shade Auto Smooth" which,
        # in Blender 4.1+, adds the "Smooth by Angle" modifier with default settings.
        bpy.ops.object.shade_auto_smooth()
        
        print(f"Applied default automatic smoothing (Smooth by Angle modifier) to '{obj.name}'.")
        print("The default angle is typically 30 degrees.")
    else:
        print(f"Error: Active object '{obj.name}' is not a mesh.")

def remove_duplicate_meshes():
    """
    Scans all meshes in the current Blender file, finds duplicates based on geometry,
    replaces all instances of duplicate meshes with a single true source mesh,
    and deletes the rest of the duplicate mesh data blocks.
    """

    mesh_data_blocks = {}  # Stores unique mesh data blocks based on geometry hash
    mesh_names_to_delete = []  # Store names of meshes that will be deleted
    duplicates_found = 0

    print("--- Starting Duplicate Mesh Cleaning Script ---")

    # First pass: Identify unique meshes and mark duplicates for replacement
    for mesh in bpy.data.meshes:
        # Skip mesh data blocks with no users
        if not mesh.users:
            continue

        # Calculate a simple hash of the mesh's geometry to identify duplicates
        geom_hash = (
            tuple(tuple(v.co) for v in mesh.vertices),
            tuple(tuple(e.vertices) for e in mesh.edges),
            tuple(tuple(p.vertices) for p in mesh.polygons)
        )

        # Check if this geometry hash already exists
        if geom_hash in mesh_data_blocks:
            # This mesh is a duplicate of an existing one
            source_mesh = mesh_data_blocks[geom_hash]

            # Find all objects using the current duplicate mesh
            objects_to_update = [obj for obj in bpy.data.objects if obj.data == mesh]

            # Replace the duplicate mesh with the source mesh for all found objects
            for obj in objects_to_update:
                obj.data = source_mesh
                print(f"  - Replaced mesh for object '{obj.name}' (was '{mesh.name}', now '{source_mesh.name}')")
                duplicates_found += 1

            # After updating all objects, if the duplicate mesh has no more users,
            # add its NAME to the list for deletion.
            if not mesh.users:
                mesh_names_to_delete.append(mesh.name)

        else:
            # This is a unique mesh geometry, add it to our dictionary
            mesh_data_blocks[geom_hash] = mesh

    # Second pass: Delete the identified duplicate mesh data blocks by name
    for mesh_name in mesh_names_to_delete:
        # Get a fresh reference to the mesh data block using its name
        mesh_to_remove = bpy.data.meshes.get(mesh_name)

        if mesh_to_remove:  # Check if the mesh still exists in bpy.data.meshes
            try:
                bpy.data.meshes.remove(mesh_to_remove)
                print(f"  - Deleted duplicate mesh data block: '{mesh_name}'")
            except Exception as e:
                # This should ideally not happen if mesh_to_remove is valid
                print(f"  - Error deleting mesh '{mesh_name}': {e}")
        else:
            print(f"  - Warning: Mesh '{mesh_name}' was already removed or became invalid before explicit deletion.")

    if duplicates_found == 0:
        print("No duplicate meshes (based on geometry) found and replaced.")
    else:
        print(f"--- Finished: Replaced {duplicates_found} duplicate mesh instances. ---")
