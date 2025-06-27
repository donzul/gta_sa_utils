import bpy
import os
import inspect # Needed to get the current script's file path
import hashlib
import numpy as np
from collections import defaultdict
import re

def remap_textures():
    script_file_path = inspect.getfile(inspect.currentframe())
    script_dir = os.path.dirname(os.path.abspath(script_file_path))
    texture_map_file_path = os.path.join(script_dir, "texture_map.txt")

    if not os.path.exists(texture_map_file_path):
        print(f"Error: texture_map.txt not found at {texture_map_file_path}")
        print("Please ensure 'texture_map.txt' is in the same directory as this script.")
        return

    image_map = {}
    try:
        with open(texture_map_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or ',' not in line:
                    continue
                new_name, original_blender_name = line.split(',', 1)
                
                # Normalize the original_blender_name: remove spaces and convert to lowercase
                normalized_original_name = original_blender_name.strip().replace(" ", "").lower()
                image_map[normalized_original_name] = new_name.strip()
    except Exception as e:
        print(f"Error reading texture_map.txt: {e}")
        return

    # List to hold images that are duplicates and will be removed
    images_to_remove = []

    # First pass: Rename images and handle duplicates by re-assigning materials
    for image in bpy.data.images:
        current_blender_image_name = image.name
        
        # Normalize the current Blender image name: remove spaces and convert to lowercase
        normalized_current_blender_image_name = current_blender_image_name.replace(" ", "").lower()

        # Check if this normalized image name is in our map
        if normalized_current_blender_image_name in image_map:
            new_desired_name = image_map[normalized_current_blender_image_name]

            # Check if an image with the new_desired_name already exists in Blender data
            if new_desired_name in bpy.data.images:
                target_image = bpy.data.images[new_desired_name]

                # If the current image is already the target image, skip
                if image == target_image:
                    continue

                # This current 'image' is a duplicate instance that needs to be replaced
                print(f"Consolidating duplicate: '{image.name}' will be replaced by '{target_image.name}'")

                # Reassign materials using this duplicate to the primary target image
                for mat in bpy.data.materials:
                    if mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.type == 'TEX_IMAGE' and node.image == image:
                                node.image = target_image
                                print(f"  - Material '{mat.name}' re-assigned from '{image.name}' to '{target_image.name}'")
                
                # Add the duplicate image to our removal list
                images_to_remove.append(image)
            else:
                # No image with the new_desired_name exists, so we can just rename it
                print(f"Renaming image: '{image.name}' to '{new_desired_name}'")
                image.name = new_desired_name
        else:
            print(f"No mapping found for image: '{current_blender_image_name}'")

    # Second pass: Remove redundant (duplicate) images that were re-assigned
    for image in images_to_remove:
        # Check if the image still has users before attempting to remove it
        if image.users == 0:
            print(f"Removing unused duplicate image: '{image.name}'")
            bpy.data.images.remove(image)
        else:
            print(f"Warning: Image '{image.name}' still has {image.users} users and cannot be removed.")
            print("Please manually check dependencies for this image.")

    rename_image_paths()

def clean_image_names():
    """
    Checks for and removes '.xxx' number extensions from image names
    for all *remaining* internal images after duplicate removal.
    """
    print("\nStarting image name cleanup (post-deduplication)...")
    images_renamed_count = 0
    for image in bpy.data.images:
        # Only process internal images (skip external and generated)
        if image.packed_file is None and image.source == 'FILE':
            continue
        if image.source == 'GENERATED':
            continue

        original_name = image.name
        # Regex to match common image extensions followed by . and 3 digits
        match = re.search(r'(\.[a-zA-Z0-9]{2,4})\.(\d{3})$', original_name)
        if match:
            original_extension = match.group(1) # e.g., .png, .jpg
            number_extension = match.group(2) # e.g., 001, 123
            
            # Reconstruct the name without the .xxx part
            cleaned_name = original_name[:-len(original_extension) - len(number_extension) - 1] + original_extension
            
            # Important: Check if the cleaned name already exists among *other* images.
            # If so, renaming might cause a name collision in Blender's data-block system.
            # Blender typically appends .001, .002 if you try to set a name that already exists.
            # We'll let Blender handle the automatic numbering if there's a collision.
            
            if cleaned_name != original_name:
                image.name = cleaned_name # Rename the image data-block
                print(f"  Renamed '{original_name}' to '{image.name}' (removed '.{number_extension}')")
                images_renamed_count += 1
    
    if images_renamed_count == 0:
        print("  No image names needed cleaning.")
    else:
        print(f"  Cleaned names for {images_renamed_count} images.")
    print("Image name cleanup complete.")

def get_image_hash(image):
    if not image.pixels:
        print(f"Warning: Image '{image.name}' has no pixel data.")
        return None
    # Get pixel data as a flat list of floats (RGBA)
    pixels = np.array(image.pixels).tobytes()
    return hashlib.md5(pixels).hexdigest()

def remove_duplicate_images():
    """
    Scans all internal/packed images for duplicates, deletes them, and re-links
    texture nodes to the original image.
    """
    image_hashes = defaultdict(list)
    
    print("Scanning for duplicate images...")

    # First pass: calculate hashes and group images
    for image in bpy.data.images:
        # Only process images that are truly packed (internal)
        # image.packed_file will be None for external files.
        if image.packed_file is None and image.source == 'FILE':
            print(f"Skipping external (unpacked) image: {image.name} (Source: {image.source}, Filepath: '{image.filepath}')")
            continue
        
        # Also skip 'Render Result' and other generated images if you don't want to hash them
        if image.source == 'GENERATED':
            print(f"Skipping generated image: {image.name}")
            continue

        img_hash = get_image_hash(image)
        if img_hash:
            image_hashes[img_hash].append(image)

    duplicates_found = False
    images_to_delete = []
    relinked_nodes_count = 0

    # Second pass: identify duplicates and prepare for relinking/deletion
    for img_hash, images in image_hashes.items():
        if len(images) > 1:
            duplicates_found = True
            original_image = images[0]
            print(f"\nFound duplicates for hash: {img_hash}")
            print(f"  Original: {original_image.name}")

            for i, duplicate_image in enumerate(images[1:]):
                print(f"  Duplicate: {duplicate_image.name}")
                
                # Check all materials and relink texture nodes
                for material in bpy.data.materials:
                    if material.use_nodes:
                        for node in material.node_tree.nodes:
                            if node.type == 'TEX_IMAGE' and node.image == duplicate_image:
                                node.image = original_image
                                relinked_nodes_count += 1
                                print(f"    - Relinked '{node.name}' in material '{material.name}' to '{original_image.name}'")
                
                images_to_delete.append(duplicate_image)

    if not duplicates_found:
        print("\nNo duplicate internal images found.")
        return

    print(f"\nRelinked {relinked_nodes_count} texture nodes.")

    print("\nDeleting duplicate images...")
    for image_to_delete in images_to_delete:
        image_name = image_to_delete.name # Get the name BEFORE deletion
        try:
            if image_to_delete.users == 0:
                 bpy.data.images.remove(image_to_delete)
                 print(f"  Deleted: {image_name}") # Use the stored name
            else:
                 print(f"  Warning: Image '{image_name}' still has {image_to_delete.users} users. Skipping deletion.")
        except RuntimeError as e:
            print(f"  Error deleting {image_name}: {e}") # Use the stored name

    clean_image_names()
    rename_image_paths()
    
    print("\nDuplicate image cleanup complete.")

def rename_image_paths():
    """
    Scans all packed images in the current Blender file and replaces
    their source paths with the current image name (e.g., 'newimagename.png').
    """
    for img in bpy.data.images:
        if img.packed_file:  # Check if the image is packed
            # Get the current name of the image in Blender (e.g., 'newimagename.png')
            new_path = img.name

            # Set the image's filepath to its current name.
            # This effectively "replaces" the source path with the image's name.
            oldname = img.filepath
            img.filepath = new_path
            print(f"Replaced source for packed image '{img.name}'. '{oldname}' > '{img.filepath}'")
        else:
            print(f"Image '{img.name}' is not packed, skipping.")