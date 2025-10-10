import bpy
import sys
import os
import json
import shutil

def log(message):
    """Print log messages"""
    print(f"[CONVERTER] {message}")

def exit_with_error(error_message):
    """Exit with error JSON"""
    result = {"success": False, "error_message": error_message}
    print(json.dumps(result))
    sys.exit(1)

def exit_with_success(fbx_path, blend_path):
    """Exit with success JSON"""
    result = {
        "success": True,
        "fbx_path": fbx_path,
        "blend_path": blend_path
    }
    print(json.dumps(result))
    sys.exit(0)

def main():
    # Parse command line arguments
    # blender -b base.blend -P converter.py -- "path/to/avatar.obj" "output_fbx_dir"
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []

    if len(argv) < 2:
        exit_with_error("Usage: blender -b base.blend -P converter.py -- <obj_path> <output_fbx_dir>")

    obj_path = argv[0]
    output_fbx_dir = argv[1]
    
    # Validate OBJ path
    if not os.path.exists(obj_path):
        exit_with_error(f"OBJ file not found: {obj_path}")
    
    log(f"OBJ path: {obj_path}")
    
    # Get directory containing the OBJ
    obj_dir = os.path.dirname(obj_path)
    
    # Read metadata.json
    metadata_path = os.path.join(obj_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        exit_with_error(f"metadata.json not found: {metadata_path}")
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        exit_with_error(f"Failed to read metadata.json: {str(e)}")
    
    # Extract user info
    try:
        username = metadata['user_info']['name']
        user_id = metadata['user_info']['id']
        avatar_type = metadata['avatar_type']
    except KeyError as e:
        exit_with_error(f"Missing required field in metadata.json: {str(e)}")
    
    # Check if avatar is R6
    if avatar_type != "R6":
        exit_with_error(f"Avatar type is not R6. Found: {avatar_type}")
    
    log(f"Username: {username}, User ID: {user_id}, Avatar Type: {avatar_type}")
    log(f"Output directory: {output_fbx_dir}")

    # Create output filename
    output_name = f"{username}_{user_id}"

    # Create output directory if it doesn't exist
    os.makedirs(output_fbx_dir, exist_ok=True)

    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_blend_path = os.path.join(script_dir, "Roblox_Base_R6_For_Unreal.blend")

    output_blend_path = os.path.join(output_fbx_dir, f"{output_name}.blend")
    output_fbx_path = os.path.join(output_fbx_dir, f"{output_name}.fbx")

    # Copy texture to output directory
    texture_source = os.path.join(obj_dir, "textures", "texture_001.png")
    if not os.path.exists(texture_source):
        exit_with_error("Check the texture - texture_001.png not found")

    texture_dest = os.path.join(output_fbx_dir, f"T_Roblox_{output_name}.png")
    shutil.copy2(texture_source, texture_dest)
    log(f"Texture copied to: {texture_dest}")
    
    # Load base blend file
    log(f"Loading base blend file: {base_blend_path}")
    bpy.ops.wm.open_mainfile(filepath=base_blend_path)
    
    # Import OBJ
    log(f"Importing OBJ: {obj_path}")
    bpy.ops.wm.obj_import(filepath=obj_path)
    
    # Find the imported mesh object
    imported_obj = None
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            imported_obj = obj
            break
    
    if not imported_obj:
        exit_with_error("No mesh found in imported OBJ")
    
    log(f"Imported mesh: {imported_obj.name}")
    
    # Get M_Roblox material
    material = bpy.data.materials.get("M_Roblox")
    if not material:
        exit_with_error("Material M_Roblox not found in base blend file")
    
    log("Found M_Roblox material")
    
    # Assign texture to material
    if material.use_nodes:
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Find Principled BSDF
        principled = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break
        
        if not principled:
            exit_with_error("Principled BSDF not found in M_Roblox material")
        
        # Find or create Image Texture node
        image_node = None
        for node in nodes:
            if node.type == 'TEX_IMAGE':
                image_node = node
                break
        
        if not image_node:
            image_node = nodes.new(type='ShaderNodeTexImage')
            image_node.location = (-300, 300)
        
        # Load texture image
        try:
            image = bpy.data.images.load(texture_dest)
            image_node.image = image
            log(f"Loaded texture: {texture_dest}")
        except Exception as e:
            exit_with_error(f"Failed to load texture: {str(e)}")
        
        # Connect Image Texture to Principled BSDF
        # Color -> Base Color
        links.new(image_node.outputs['Color'], principled.inputs['Base Color'])
        # Alpha -> Alpha
        links.new(image_node.outputs['Alpha'], principled.inputs['Alpha'])
        
        log("Texture assigned to M_Roblox material")
    else:
        exit_with_error("M_Roblox material does not use nodes")
    
    # Delete the imported OBJ mesh
    bpy.data.objects.remove(imported_obj, do_unlink=True)
    log("Deleted imported OBJ mesh")
    
    # Save blend file
    bpy.ops.wm.save_as_mainfile(filepath=output_blend_path)
    log(f"Saved blend file: {output_blend_path}")
    
    # Export to FBX for Unreal Engine 5.3
    log("Exporting to FBX...")
    bpy.ops.export_scene.fbx(
        filepath=output_fbx_path,
        use_selection=False,
        use_active_collection=False,
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE',
        use_space_transform=True,
        bake_space_transform=False,
        object_types={'ARMATURE', 'MESH', 'EMPTY'},
        use_mesh_modifiers=True,
        use_mesh_modifiers_render=True,
        mesh_smooth_type='OFF',
        use_subsurf=False,
        use_mesh_edges=False,
        use_tspace=False,
        use_custom_props=False,
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL',
        bake_anim=False,
        bake_anim_use_all_bones=False,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=False,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=1.0,
        path_mode='AUTO',
        embed_textures=False,
        batch_mode='OFF',
        use_batch_own_dir=False,
        use_metadata=True,
        axis_forward='Z',
        axis_up='Y'
    )
    
    log(f"FBX exported: {output_fbx_path}")
    
    # Exit with success
    exit_with_success(output_fbx_path, output_blend_path)

if __name__ == "__main__":
    main()