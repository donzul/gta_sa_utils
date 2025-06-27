import bpy
import os

def remove_unused_material_slots():
    """
    Deletes material slots from the active object that are not assigned to any faces.
    """
    # Get the currently active object
    obj = bpy.context.active_object

    # Check if there is an active object and it is a mesh
    if not obj or obj.type != 'MESH':
        print("No active mesh object selected.")
        return

    # Keep track of the material indices that are in use
    used_slots = set()
    for poly in obj.data.polygons:
        used_slots.add(poly.material_index)

    # Reverse iterate and remove unused slots
    for i in range(len(obj.material_slots) - 1, -1, -1):
        if i not in used_slots:
            obj.active_material_index = i
            bpy.ops.object.material_slot_remove()

    print("Unused material slots have been removed.")

def get_first_image_texture(material):
    """
    Finds the first image texture node in a material's node tree and
    returns its image.
    """
    if material and material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                return node.image
    return None

def remove_duplicate_material_slots():
    """
    Removes duplicate material slots from the active object,
    considering the first image texture of each material.
    """
    obj = bpy.context.view_layer.objects.active

    if not obj or obj.type != 'MESH':
        print("Please select an active mesh object.")
        return

    # Store materials encountered and their first slot index
    material_texture_map = {}
    slots_to_remove = []

    # Iterate through material slots in reverse to handle removal safely
    for i in range(len(obj.data.materials) - 1, -1, -1):
        mat = obj.data.materials[i]

        if mat is None:
            # Handle empty material slots
            slots_to_remove.append(i)
            continue

        # Get the first image texture of the material
        first_image = get_first_image_texture(mat)
        
        # Create a unique key based on the material and its first texture
        # If no image is found, the material itself is used as the key.
        mat_key = (mat, first_image)

        if mat_key not in material_texture_map:
            # First time encountering this material and texture combination
            material_texture_map[mat_key] = i
        else:
            # This material and texture combination is a duplicate
            original_slot_index = material_texture_map[mat_key]

            # Reassign faces using this duplicate material slot
            # to the original material slot
            for poly in obj.data.polygons:
                if poly.material_index == i:
                    poly.material_index = original_slot_index
            
            # Mark this slot for removal
            slots_to_remove.append(i)

    # Remove duplicate material slots
    # Sort in ascending order before removal to avoid index issues
    slots_to_remove.sort() 
    for index in reversed(slots_to_remove): # Remove in reverse order
        obj.data.materials.pop(index=index)

    print(f"Removed {len(slots_to_remove)} duplicate material slots for object: {obj.name}")

def remove_duplicate_materials():
    """
    Loops through images, identifies duplicate material usages, consolidates materials,
    deletes duplicates, and renames materials based on their linked image texture.
    """

    print("Starting material cleanup and renaming process...")

    # Dictionary to store the first material found for each image
    image_material_map = {}
    # List to store materials to be deleted later
    materials_to_delete = []

    # --- Phase 1: Identify and Consolidate Duplicate Materials ---
    print("\nPhase 1: Consolidating duplicate materials...")

    for image in bpy.data.images:
        print(f"\nProcessing image: {image.name}")
        linked_materials = []

        # Find all materials that use this image
        for material in bpy.data.materials:
            if material.use_nodes:
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image == image:
                        linked_materials.append(material)
                        break # Assume each material only has one texture node with that texture

        if not linked_materials:
            print(f"   No materials found linked to image: {image.name}")
            continue

        # If multiple materials are linked to the same image
        if len(linked_materials) > 1:
            first_material = linked_materials[0]
            print(f"   Image '{image.name}' is linked to multiple materials. Keeping: '{first_material.name}'")

            for i in range(1, len(linked_materials)):
                duplicate_material = linked_materials[i]
                print(f"     Consolidating duplicate material: '{duplicate_material.name}'")

                # Link the first material to all objects/meshes that use the duplicate
                for obj in bpy.data.objects:
                    if obj.type == 'MESH':
                        for slot in obj.material_slots:
                            if slot.material == duplicate_material:
                                slot.material = first_material
                                print(f"       Replaced material on object '{obj.name}' from '{duplicate_material.name}' to '{first_material.name}'")

                materials_to_delete.append(duplicate_material)
        elif len(linked_materials) == 1:
            print(f"   Image '{image.name}' is linked to a single material: '{linked_materials[0].name}'")

        # Store the first material associated with this image for renaming later
        if linked_materials:
            image_material_map[image.name] = linked_materials[0]

    # --- Phase 2: Delete Duplicate Materials ---
    print("\nPhase 2: Deleting duplicate materials...")
    for mat in set(materials_to_delete): # Use a set to avoid deleting the same material multiple times
        if mat.users == 0: # Ensure no more users before deleting
            print(f"     Deleting duplicate material: '{mat.name}'") # Print before removal
            bpy.data.materials.remove(mat)
        else:
            print(f"     Warning: Material '{mat.name}' still has users ({mat.users}) and could not be deleted.")

    # --- Phase 3: Rename Materials ---
    print("\nPhase 3: Renaming materials...")
    for image_name, material in image_material_map.items():
        # Extract the base name without the extension
        base_image_name = os.path.splitext(image_name)[0]

        # Extract the number from the image name (e.g., "T_39" -> "39")
        try:
            # Assumes image names are like "T_NUMBER" or "T_NUMBER.png"
            prefix, number = base_image_name.split('_', 1)
            if prefix == 'T' and number.isdigit():
                new_material_name = f"M_{number}"
                # Store the original name before renaming for logging purposes
                original_material_name = material.name
                if material.name != new_material_name:
                    material.name = new_material_name
                    print(f"   Renamed material '{original_material_name}' to '{material.name}' (from image '{image_name}')")
                else:
                    print(f"   Material '{material.name}' is already correctly named for image '{image_name}'.")
            else:
                print(f"   Skipping rename for image '{image_name}'. Image name format not recognized for renaming (expected 'T_NUMBER' or 'T_NUMBER.png').")
        except ValueError:
            print(f"   Skipping rename for image '{image_name}'. Image name format not recognized for renaming (expected 'T_NUMBER' or 'T_NUMBER.png').")
        except Exception as e:
            print(f"   An error occurred while renaming material for image '{image_name}': {e}")


    print("\nMaterial cleanup and renaming process complete!")