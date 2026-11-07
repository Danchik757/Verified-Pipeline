"""Bounded target-engine scene/pose integration check; raw OBJ inputs are explicit."""
import argparse,hashlib,json,math,os,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix
p=argparse.ArgumentParser();p.add_argument('--code',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.out;out.mkdir(parents=True,exist_ok=True)
if (out/'manifest.json').exists():raise RuntimeError('Refusing overwrite')
sys.path.insert(0,str(a.code/'src'))
from verified_pipeline.envelope_runner import calibrate_and_fit
from envelope_height_calibration.geometry import measure_blender_mesh,measure_blender_envelope
assert bpy.app.version[:2]==(4,2),bpy.app.version_string
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='OPTIX'
devices=[{'name':d.name,'id':d.id,'type':d.type,'use':d.use} for d in prefs.devices]
assert sum(d['use'] for d in devices)==1,devices
assert any(d['type']=='OPTIX' and d['use'] for d in devices)
scene=bpy.context.scene
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=8;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=640;scene.render.resolution_y=360;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
world=bpy.data.worlds.new('Neutral diagnostic');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6;scene.world=world
cd=bpy.data.cameras.new('Calibration camera');cam=bpy.data.objects.new('Calibration camera',cd);scene.collection.objects.link(cam)
e=math.radians(18);cam.location=(0,-1.58*math.cos(e),1.58*math.sin(e));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
cd.type='PERSP';cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=36/(2*math.tan(math.radians(60)/2));cd.clip_start=.01;cd.clip_end=100;scene.camera=cam
ld=bpy.data.lights.new('Diagnostic area','AREA');ld.energy=250;ld.size=3
lamp=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(lamp);lamp.location=(-2,-3,4);lamp.rotation_euler=(-lamp.location).to_track_quat('-Z','Y').to_euler()
mat=bpy.data.materials.new('Diagnostic grey');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.5,.5,.5,1);bs.inputs['Roughness'].default_value=.8
bpy.context.view_layer.update()
expected_inputs=json.loads((a.inputs/'inputs.json').read_text())
views=[(angle,Matrix.Rotation(math.radians(angle),3,'Z')) for angle in range(360)]
records=[];cases=[]
for name in ('A380','spanner','bunny'):
 path=a.inputs/f'{name}.obj';raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha==expected_inputs[name]
 vertices=[];faces=[]
 for line in raw.splitlines():
  fields=line.split()
  if not fields:continue
  if fields[0]==b'v':vertices.append(tuple(map(float,fields[1:4])))
  elif fields[0]==b'f':
   ids=[int(x.split(b'/')[0]) for x in fields[1:]];faces.append([i-1 if i>0 else len(vertices)+i for i in ids])
 v=np.array(vertices,dtype=float)[:,[0,2,1]]*np.array([1,-1,1])
 for kind in ('sphere','cube'):
  result=calibrate_and_fit(kind,scene,cam,v,70,views,mode='turn_max')
  fit=result['placement'];cal=result['calibration'];size=cal['physical_size_m'];scale=fit['uniform_scale'];center=np.array(fit['source_bbox_center'])
  assert abs(cal['achieved_percent']-70)<1e-5
  reference_size=.7004953999152395 if kind=='sphere' else .5034316217297103
  assert abs(size-reference_size)<1e-6,(kind,size)
  centered=v-center
  extent=np.linalg.norm(centered*scale,axis=1).max() if kind=='sphere' else np.abs(centered*scale).max()
  assert extent<=size/2+1e-9
  mesh=bpy.data.meshes.new(f'{name}_{kind}');mesh.from_pydata(centered.tolist(),[],faces);mesh.update()
  obj=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(obj);mesh.materials.append(mat)
  obj.scale=(scale,)*3
  for poly in mesh.polygons:poly.use_smooth=True
  case_dir=out/f'{name.lower()}_{kind}';case_dir.mkdir()
  for frame,yaw in enumerate(range(0,360,30)):
   obj.rotation_euler=(0,0,math.radians(yaw));bpy.context.view_layer.update()
   actual=np.array([obj.matrix_world@vertex.co for vertex in mesh.vertices])
   rotation=np.array(Matrix.Rotation(math.radians(yaw),3,'Z'))
   expected=(centered*scale)@rotation.T
   delta=float(np.abs(actual-expected).max());assert delta<1e-6,delta
   measured=measure_blender_mesh(scene,cam,actual)
   envelope=measure_blender_envelope(scene,cam,kind,(0,0,0),size,Matrix.Rotation(math.radians(yaw),3,'Z'))
   assert envelope['height_percent']<=70+1e-5
   assert max(measured['overflow_px'].values())<1e-5
   scene.frame_set(frame);png=case_dir/f'frame_{frame:03d}.png';scene.render.filepath=str(png);bpy.ops.render.render(write_still=True)
   assert scene.cycles.device=='GPU' and prefs.compute_device_type=='OPTIX'
   records.append({'mesh':name,'kind':kind,'frame':frame,'yaw_deg':yaw,'time_s':frame/6,'scale':list(obj.scale),'object_matrix':[list(row) for row in obj.matrix_world],'world_vertex_max_error_m':delta,'mesh_projection':measured,'envelope_projection':envelope,'png':str(png.relative_to(out)),'sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
   print('FRAME_DONE',len(records),name,kind,frame,flush=True)
  cases.append({'mesh':name,'kind':kind,'source_sha256':sha,'calibration':cal,'placement':fit,'frame_count':12,'fps':6,'directory':case_dir.name})
  bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
manifest={'blender_version':bpy.app.version_string,'blender_build_hash':bpy.app.build_hash.decode(),'code_commit':(a.code/'SOURCE_COMMIT').read_text().strip(),'device_type':prefs.compute_device_type,'render_device':scene.cycles.device,'devices':devices,'cuda_visible_devices':os.environ.get('CUDA_VISIBLE_DEVICES'),'camera':{'distance_m':float(cam.location.length),'lens_mm':cd.lens,'horizontal_fov_deg':math.degrees(cd.angle_x),'resolution_px':[640,360],'elevation_deg':18},'samples':8,'denoise':False,'static_rotation_deg':[90,0,0],'cases':cases,'frames':records}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('PLACEMENT_OPTIX_COMPLETE',len(records),flush=True)
