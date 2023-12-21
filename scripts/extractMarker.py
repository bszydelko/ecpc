import bpy
import os
from mathutils import Vector
import numpy as np


def project_3d_point(camera: bpy.types.Object, p: Vector, render: bpy.types.RenderSettings = bpy.context.scene.render) -> Vector:
    """
    Given a camera and its projection matrix M;
    given p, a 3d point to project:

    Compute P’ = M * P
    P’= (x’, y’, z’, w')

    Ignore z'
    Normalize in:
    x’’ = x’ / w’
    y’’ = y’ / w’

    x’’ is the screen coordinate in normalised range -1 (left) +1 (right)
    y’’ is the screen coordinate in  normalised range -1 (bottom) +1 (top)

    :param camera: The camera for which we want the projection
    :param p: The 3D point to project
    :param render: The render settings associated to the scene.
    :return: The 2D projected point in normalized range [-1, 1] (left to right, bottom to top)
    """

    if camera.type != 'CAMERA':
        raise Exception("Object {} is not a camera.".format(camera.name))

    if len(p) != 3:
        raise Exception("Vector {} is not three-dimensional".format(p))

    # Get the two components to calculate M
    modelview_matrix = camera.matrix_world.inverted()
    projection_matrix = camera.calc_matrix_camera(
        bpy.data.scenes["Scene"].view_layers["ViewLayer"].depsgraph,
        x = render.resolution_x,
        y = render.resolution_y,
        scale_x = render.pixel_aspect_x,
        scale_y = render.pixel_aspect_y,
    )

    # Compute P’ = M * P
    p1 = projection_matrix @ modelview_matrix @ Vector((p.x, p.y, p.z, 1))

    # Normalize in: x’’ = x’ / w’, y’’ = y’ / w’
    p2 = Vector(((p1.x/p1.w, p1.y/p1.w)))

    return p2


def main():
    
    scene = bpy.data.scenes['Scene']
    frameStart  = scene.frame_start
    frameEnd    = scene.frame_end
    frameStep   = scene.frame_step
    
    markerPositionsGT = []
    render = bpy.context.scene.render
    
    for frameCurrent in range(frameStart, frameEnd+1, frameStep):
        bpy.context.scene.frame_set(frameCurrent)
        markerIn3D = bpy.data.objects['Ball'].matrix_world.to_translation()
        frameMarker = []
        for camera in bpy.data.cameras:
            
            cam_data = bpy.data.objects[camera.name]
        
            proj_p = project_3d_point(cam_data, markerIn3D)
            markerXY = Vector(((render.resolution_x-1) * (proj_p.x + 1) / 2, (render.resolution_y - 1) * (proj_p.y - 1) / (-2)))
            
            X = markerXY[0]
            Y = markerXY[1]
            
            if X > render.resolution_x or Y > render.resolution_y or X < 0 or Y < 0:
                frameMarker.append(-1)
                frameMarker.append(-1)
                frameMarker.append(0)
            else:
                frameMarker.append(X)
                frameMarker.append(Y)
                frameMarker.append(1)
        markerPositionsGT.append(frameMarker)
        
    with open(os.path.dirname(bpy.path.abspath(bpy.data.filepath)) + '\\markerPositionsGT.txt', 'w') as file:
        np.savetxt(file, markerPositionsGT, fmt='%.3f', delimiter='\t')
            
    return True


if __name__ == '__main__':
    print('Extracting ground truth marker positions...')
    main()
    bpy.ops.wm.quit_blender()
    print('Results saved to ' + os.path.dirname(bpy.path.abspath(bpy.data.filepath)) + '\\markerPositionsGT.txt')