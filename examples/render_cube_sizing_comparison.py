"""Diagnostic one-OBJ comparison of reference and sampled-turn-max cube sizing."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix
parser=argparse.ArgumentParser()
parser.add_argument('--mesh',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--target',type=float,default=70)
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from verified_pipeline.envelope_runner import calibrate_and_fit
from envelope_height_calibration.geometry import measure_blender_mesh
out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
if (out/'manifest.json').exists() or list(out.glob('cube_*.png')):raise SystemExit('Use a fresh output directory')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.view_settings.exposure=0;scene.view_settings.gamma=1
world=bpy.data.worlds.new('Diagnostic world');world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6;scene.world=world
cd=bpy.data.cameras.new('Camera');camera=bpy.data.objects.new('Camera',cd);scene.collection.objects.link(camera)
e=math.radians(18);camera.location=(0,-1.58*math.cos(e),1.58*math.sin(e))
camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler()
cd.type='PERSP';cd.sensor_fit='HORIZONTAL';cd.sensor_width=36
cd.lens=36/(2*math.tan(math.radians(60)/2));cd.clip_start=.01;cd.clip_end=100
scene.camera=camera
ld=bpy.data.lights.new('Diagnostic area','AREA');ld.energy=250;ld.shape='DISK';ld.size=3
lamp=bpy.data.objects.new('Diagnostic area',ld);scene.collection.objects.link(lamp)
lamp.location=(-2,-3,4);lamp.rotation_euler=(-lamp.location).to_track_quat('-Z','Y').to_euler()
mat=bpy.data.materials.new('Diagnostic grey');mat.use_nodes=True
bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.5,.5,.5,1);bs.inputs['Roughness'].default_value=.8
bpy.context.view_layer.update()
raw=a.mesh.read_bytes();vertices=[];faces=[]
for line in raw.splitlines():
    fields=line.split()
    if not fields:continue
    if fields[0]==b'v':vertices.append(tuple(map(float,fields[1:4])))
    elif fields[0]==b'f':
        indices=[int(token.split(b'/')[0]) for token in fields[1:]]
        faces.append([i-1 if i>0 else len(vertices)+i for i in indices])
v=np.array(vertices,dtype=float)[:,[0,2,1]]*np.array([1,-1,1])
views=[(angle,Matrix.Rotation(math.radians(angle),3,'Z')) for angle in range(360)]
records=[];calibrations={}
for mode in ('reference','turn_max'):
    result=calibrate_and_fit('cube',scene,camera,v,a.target,views,mode=mode)
    calibration=result['calibration'];fit=result['placement'];calibrations[mode]=calibration
    transformed=(v-np.array(fit['source_bbox_center']))*fit['uniform_scale']
    mesh=bpy.data.meshes.new(mode);mesh.from_pydata(transformed.tolist(),[],faces);mesh.update()
    obj=bpy.data.objects.new(mode,mesh);scene.collection.objects.link(obj);mesh.materials.append(mat)
    for poly in mesh.polygons:poly.use_smooth=True
    for yaw in (0,45,90):
        rotation=Matrix.Rotation(math.radians(yaw),3,'Z')
        obj.rotation_euler=(0,0,math.radians(yaw));bpy.context.view_layer.update()
        rotated=transformed@np.array(rotation).T
        measured=measure_blender_mesh(scene,camera,rotated)
        envelope=next(x['projection'] for x in calibration['views'] if x['view']==yaw)
        png=out/f'cube_{mode}_target{a.target:g}_yaw{yaw:03d}.png'
        scene.render.filepath=str(png);bpy.ops.render.render(write_still=True)
        records.append({'mode':mode,'yaw_deg':yaw,'target_percent':a.target,'placement':fit,
                        'envelope':envelope,'mesh_projection':measured,'image':png.name,
                        'image_sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
        print('FRAME_DONE',mode,yaw,flush=True)
    bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
manifest={'blender_version':bpy.app.version_string,'source_mesh':a.mesh.name,
          'source_mesh_sha256':hashlib.sha256(raw).hexdigest(),'static_rotation_deg':[90,0,0],
          'camera':{'distance_m':1.58,'elevation_deg':18,'horizontal_fov_deg':60,'resolution_px':[960,540]},
          'render_settings':{'engine':'CYCLES','device':'CPU','samples':12,'denoise':True,'world_strength':.6,'area_w':250,'area_size_m':3,'view_transform':'Standard'},
          'calibrations':calibrations,'records':records,
          'source_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('COMPARISON_COMPLETE',len(records),flush=True)
