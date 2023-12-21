import os
import bpy
import sys
import json
import argparse
import mathutils
import numpy as np

def getSensorSize(sensor_fit, sensor_x, sensor_y):
    if sensor_fit == 'VERTICAL':
        return sensor_y
    return sensor_x

def getSensorFit(sensor_fit, size_x, size_y):
    if sensor_fit == 'AUTO':
        if size_x >= size_y:
            return 'HORIZONTAL'
        else:
            return 'VERTICAL'
    return sensor_fit

def getIntrinsicMatrix(cam_data):
    if cam_data.type != 'PERSP':
        raise ValueError('Non-perspective cameras not supported')
    scene = bpy.context.scene
    f_in_mm = cam_data.lens
    scale = scene.render.resolution_percentage / 100
    resolution_x_in_px = scale * scene.render.resolution_x
    resolution_y_in_px = scale * scene.render.resolution_y
    sensor_size_in_mm = getSensorSize(cam_data.sensor_fit, cam_data.sensor_width, cam_data.sensor_height)
    sensor_fit = getSensorFit(
        cam_data.sensor_fit,
        scene.render.pixel_aspect_x * resolution_x_in_px,
        scene.render.pixel_aspect_y * resolution_y_in_px
    )
    pixel_aspect_ratio = scene.render.pixel_aspect_y / scene.render.pixel_aspect_x
    if sensor_fit == 'HORIZONTAL':
        view_fac_in_px = resolution_x_in_px
    else:
        view_fac_in_px = pixel_aspect_ratio * resolution_y_in_px
    pixel_size_mm_per_px = sensor_size_in_mm / f_in_mm / view_fac_in_px
    FocalX = 1 / pixel_size_mm_per_px
    FocalY = 1 / pixel_size_mm_per_px / pixel_aspect_ratio

    # Parameters of intrinsic calibration matrix K
    PrinciplePointX = resolution_x_in_px / 2 - cam_data.shift_x * view_fac_in_px
    PrinciplePointY = resolution_y_in_px / 2 + cam_data.shift_y * view_fac_in_px / pixel_aspect_ratio
    skew = 0 # only use rectangular pixels

    IntrinsicM = np.array([
      [FocalX,   skew, PrinciplePointX], 
      [     0, FocalY, PrinciplePointY], 
      [     0,      0,                1]], 
      dtype=np.float64)

    return IntrinsicM

def getExtrinsicMatrix(cam_data):
    R_bcam2cv = mathutils.Matrix(
        ((-1, 0, 0),
         ( 0, 0, 1),
         ( 0, 1, 0)))
         
    location = cam_data.matrix_local.to_translation()
    rotation = cam_data.matrix_local.to_quaternion()

    R_world2bcam = rotation.to_matrix()     
    T_world2bcam = location

    RotationM = R_bcam2cv @ R_world2bcam
    TranslationV = R_bcam2cv @ T_world2bcam

    ExtrinsicM = np.array([
    [RotationM[0][0], RotationM[0][1], RotationM[0][2],  TranslationV[0]],
    [RotationM[1][0], RotationM[1][1], RotationM[1][2], -TranslationV[1]],
    [RotationM[2][0], RotationM[2][1], RotationM[2][2], -TranslationV[2]]],
    dtype=np.float64)

    return ExtrinsicM
   
def AllmostZero(v):
    eps = 1e-7
    return abs(v) < eps

def RotationMatrixToEulerAngles(R):
    yaw   = 0.0
    pitch = 0.0
    roll  = 0.0
    
    if AllmostZero( R[0,0] ) and AllmostZero( R[1,0] ) :
        yaw = np.arctan2( R[1,2], R[0,2] )
        if R[2,0] < 0.0:
            pitch = np.pi/2
        else:
            pitch = -np.pi/2
        roll = 0.0
    else:
        yaw = np.arctan2( R[1,0], R[0,0] )
        if AllmostZero( R[0,0] ) :
            pitch = np.arctan2( -R[2,0], R[1,0] / np.sin(yaw) )
        else:
            pitch = np.arctan2( -R[2,0], R[0,0] / np.cos(yaw) )
        
        roll = np.arctan2( R[2,1], R[2,2] )
    
    euler = np.array( [yaw, pitch, roll] )
    return np.rad2deg(euler)
###########################################################################
def main():
    ArgParser = argparse.ArgumentParser()
    ArgParser.add_argument('-s',    type=int,   help='Start frame'              )
    ArgParser.add_argument('-e',    type=int,   help='End frame'                )
    ArgParser.add_argument('-j',    type=int,   help='Jump frame'               )
    ArgParser.add_argument('-zn',   type=float, help='Depth Z near value [m]'   )
    ArgParser.add_argument('-zf',   type=float, help='Depth Z far value [m]'    )
    
    #print(sys.argv)
    argv = sys.argv
    argv = argv[argv.index('--') + 1:]
    Args, _ = ArgParser.parse_known_args(argv)

###########################################################################
# Check preconditions

    assert len(bpy.data.cameras) > 1, 'Scene should contain at least 2 cameras.'
    for camera in bpy.data.cameras:
        assert camera.name in bpy.data.objects.keys(), 'Object name and camera name are diffrent: \
            \n\t{} not in {}'.format(camera.name, bpy.data.objects.keys())
        
    # Assume there is one scene
    scene = bpy.data.scenes['Scene']

    scene.frame_start = Args.s
    scene.frame_end = Args.e
    scene.frame_step = Args.j

    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 5
    scene.eevee.taa_samples = 8

###########################################################################
# Texture (color video) settings
    scene.render.filepath =  '//..//1_renderedScene//texture//'
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264' 
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.ffmpeg.ffmpeg_preset = 'REALTIME'
    # Default gop
    

###########################################################################
# Depth map settings
    scene.view_layers['ViewLayer'].use_pass_combined = True
    scene.view_layers['ViewLayer'].use_pass_z = True

    # Create node tree
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree

    # Clear default nodes
    for node in tree.nodes:
        tree.nodes.remove(node)

    # Create nodes for normalized disparity
    # Render Layers
    rl_node = tree.nodes.new('CompositorNodeRLayers')
    rl_node.location = mathutils.Vector((0, 500))
    # zFar
    zfar_node = tree.nodes.new('CompositorNodeValue')
    zfar_node.name = 'zFar'
    zfar_node.label = 'zFar'
    zfar_node.outputs[0].default_value = Args.zf 
    zfar_node.location = mathutils.Vector((0, 0))
    # zNear
    znear_node = tree.nodes.new('CompositorNodeValue')
    znear_node.name = 'zNear'
    znear_node.label = 'zNear'
    znear_node.outputs[0].default_value = Args.zn
    znear_node.location = mathutils.Vector((0, -100))
    # 1 / zFar
    inv_zfar_node = tree.nodes.new('CompositorNodeMath')
    inv_zfar_node.operation = 'DIVIDE'
    inv_zfar_node.name = '1 / zFar'
    inv_zfar_node.label = '1 / zFar'
    inv_zfar_node.inputs[0].default_value = 1.0
    inv_zfar_node.location = mathutils.Vector((500, 0))
    # 1 / zNear
    inv_znear_node = tree.nodes.new('CompositorNodeMath')
    inv_znear_node.operation = 'DIVIDE'
    inv_znear_node.name = '1 / zNear'
    inv_znear_node.label = '1 / zNear'
    inv_znear_node.inputs[0].default_value = 1.0
    inv_znear_node.location = mathutils.Vector((500, -200))
    # 1 / Z
    inv_z_node = tree.nodes.new('CompositorNodeMath')
    inv_z_node.operation  = 'DIVIDE'
    inv_z_node.name = '1 / Z'
    inv_z_node.label = '1 / Z'
    inv_z_node.inputs[0].default_value = 1.0
    inv_z_node.location = mathutils.Vector((500, 200))
    # 1 / Z minus 1 / zFar
    sub_inv_z_inv_zfar_node = tree.nodes.new('CompositorNodeMath')
    sub_inv_z_inv_zfar_node.operation = 'SUBTRACT'
    sub_inv_z_inv_zfar_node.name = '1 / Z minus 1 / zFar'
    sub_inv_z_inv_zfar_node.label = '1 / Z minus 1 / zFar'
    sub_inv_z_inv_zfar_node.location = mathutils.Vector((800, 150))
    # 1 / zNear minus 1 / zFar
    sub_inv_znear_inv_zfar_node = tree.nodes.new('CompositorNodeMath')
    sub_inv_znear_inv_zfar_node.operation = 'SUBTRACT'
    sub_inv_znear_inv_zfar_node.name = '1 / zNear minus 1 / zFar'
    sub_inv_znear_inv_zfar_node.label = '1 / zNear minus 1 / zFar'
    sub_inv_znear_inv_zfar_node.location = mathutils.Vector((800, -100))
    # 1 / (1 / zNear minus 1 / zFar)
    inv_sub_inv_znear_inv_zfar_node = tree.nodes.new('CompositorNodeMath')
    inv_sub_inv_znear_inv_zfar_node.operation = 'DIVIDE'
    inv_sub_inv_znear_inv_zfar_node.name = '1 / (1 / zNear minus 1 / zFar)'
    inv_sub_inv_znear_inv_zfar_node.label = '1 / (1 / zNear minus 1 / zFar)'
    inv_sub_inv_znear_inv_zfar_node.inputs[0].default_value = 1.0
    inv_sub_inv_znear_inv_zfar_node.location = mathutils.Vector((1100, -100))
    # Too loong
    mul_node = tree.nodes.new('CompositorNodeMath')
    mul_node.operation = 'MULTIPLY'
    mul_node.name = 'Multiplier'
    mul_node.label = 'Multiplier'
    mul_node.location = mathutils.Vector((1400, 50))
    # Output
    depth_output_node = tree.nodes.new('CompositorNodeOutputFile')
    depth_output_node.base_path = '//..//1_renderedScene//depth//'
    depth_output_node.name = 'Depth map'
    depth_output_node.label = 'Depth map'
    depth_output_node.format.file_format = 'PNG'
    depth_output_node.format.color_depth = '16' # TODO Use Args?
    depth_output_node.format.color_mode = 'BW'
    depth_output_node.format.compression = 0
    depth_output_node.file_slots[0].path = 'depth'
    depth_output_node.file_slots[0].use_node_format = True
    depth_output_node.file_slots[0].save_as_render = True
    depth_output_node.location = mathutils.Vector((1700, 50))
    
    # Link nodes
    links = tree.links
    links.new(rl_node.outputs['Depth'],                     inv_z_node.inputs[1])
    links.new(zfar_node.outputs[0],                         inv_zfar_node.inputs[1])
    links.new(znear_node.outputs[0],                        inv_znear_node.inputs[1])
    links.new(inv_zfar_node.outputs[0],                     sub_inv_znear_inv_zfar_node.inputs[1])
    links.new(inv_znear_node.outputs[0],                    sub_inv_znear_inv_zfar_node.inputs[0])
    links.new(inv_z_node.outputs[0],                        sub_inv_z_inv_zfar_node.inputs[0])
    links.new(inv_zfar_node.outputs[0],                     sub_inv_z_inv_zfar_node.inputs[1])
    links.new(sub_inv_znear_inv_zfar_node.outputs[0],       inv_sub_inv_znear_inv_zfar_node.inputs[1])
    links.new(sub_inv_z_inv_zfar_node.outputs[0],           mul_node.inputs[0])
    links.new(inv_sub_inv_znear_inv_zfar_node.outputs[0],   mul_node.inputs[1])
    links.new(mul_node.outputs[0],                          depth_output_node.inputs[0])

    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath) # Save changes
    print('Rendering...')
    bpy.ops.render.render(animation=True)

# Export camera parameters
    cam_params_path = os.path.dirname(bpy.path.abspath(bpy.data.filepath)) + '//..//1_renderedScene//'+  bpy.path.basename(bpy.data.filepath.replace('.blend','_camparams.json'))
    
    scale = 1
    permute = np.array([ 
        [0, 0,  1], 
        [-1, 0, 0], 
        [0, -1, 0] ] )
    
    metadataJSON = {      
        'Content_name': bpy.path.basename(bpy.data.filepath),
        'cameras': {
            'Resolution': [bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y],
            'Depth_range': [Args.zn, Args.zf],       # meters
            'BitDepthColor': 8,
            'BitDepthDepth': 16 }
        }  
    
    camerasJSON = [] 

    for camera in bpy.data.cameras:
        cam_data = bpy.data.objects[camera.name]
        IntrinsicM = getIntrinsicMatrix(cam_data.data)
        ExtrinsicM = getExtrinsicMatrix(cam_data)

        Focal            = [IntrinsicM[0,0], IntrinsicM[1,1]]
        Principle_point  = [IntrinsicM[0,2], IntrinsicM[1,2]]
        RotationMatrix   = np.transpose( permute.dot( ExtrinsicM[:,0:3] ).dot( np.transpose(permute) ) )
        Position         = scale * permute.dot(ExtrinsicM[:,3])
        EulerAngles      = RotationMatrixToEulerAngles(RotationMatrix)

        camJSON = {   
            'Name':             camera.name,
            'Position':         Position.tolist(), 
            'Rotation':         EulerAngles.tolist(),
            'Depthmap':         1,
            'Background':       0,
            'Resolution':       metadataJSON['cameras']['Resolution'],
            'Projection':       'Perspective',
            'Focal':            Focal,
            'Principle_point':  Principle_point,
            'Depth_range':      metadataJSON['cameras']['Depth_range'],
            'BitDepthColor':    metadataJSON['cameras']['BitDepthColor'],
            'BitDepthDepth':    metadataJSON['cameras']['BitDepthDepth'],
            'ColorSpace':       'YUV420',
            'DepthColorSpace':  'YUV420' 
        }

        camerasJSON.append(camJSON)
    
    metadataJSON['cameras'] = camerasJSON
  
    with open(cam_params_path, 'w') as outfile:
        json.dump(metadataJSON, outfile, indent=4)
    
    print(f'Camera parameters saved to {cam_params_path}')
    


if __name__ == '__main__':
    main()
    bpy.ops.wm.quit_blender()


