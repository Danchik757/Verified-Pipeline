"""Create a side-by-side diagnostic figure from the saved cube comparison."""
import argparse, itertools, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path)
a=p.parse_args();out=a.out;m=json.loads((out/'manifest.json').read_text())
font_path=str(a.font) if a.font else '/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(font_path,19);small=ImageFont.truetype(font_path,17);title=ImageFont.truetype(font_path,26)
S=.64;W,H=round(960*S),round(540*S);PW,PH,HEADER=755,480,118
BG=(247,248,250);INK=(36,50,69);ORANGE=(174,98,10);MAGENTA=(168,20,140)
canvas=Image.new('RGB',(2*PW,HEADER+3*PH),BG);d=ImageDraw.Draw(canvas)
d.text((20,12),'A380 | cube target: 70% | same camera and yaw in each pair',font=title,fill=INK)
d.text((20,50),'LEFT: 70% in first frame (yaw 0). RIGHT: maximum 70% over the sampled full turn.',font=font,fill=INK)
d.text((20,82),'One fixed mesh scale per column. Magenta bracket: full projected cube height.',font=small,fill=INK)
f=960/(2*math.tan(math.radians(30)));e=math.radians(18)
for row,yaw in enumerate((0,45,90)):
 for col,mode in enumerate(('reference','turn_max')):
  rec=next(x for x in m['records'] if x['mode']==mode and x['yaw_deg']==yaw)
  panel=Image.new('RGB',(PW,PH),BG);dr=ImageDraw.Draw(panel)
  dr.text((18,5),f'{mode.upper()} | yaw {yaw} deg',font=font,fill=INK)
  src=Image.open(out/rec['image']).convert('RGBA');blue=Image.new('RGBA',(960,540),(173,217,230,255));blue.alpha_composite(src)
  x0,y0=38,45;panel.paste(blue.convert('RGB').resize((W,H),Image.Resampling.LANCZOS),(x0,y0))
  edge=m['calibrations'][mode]['physical_size_m'];points=[];q=math.radians(yaw);c,s=math.cos(q),math.sin(q)
  for x,y,z in itertools.product((-edge/2,edge/2),repeat=3):
   xx=c*x-s*y;yy=s*x+c*y;depth=1.58+math.cos(e)*yy-math.sin(e)*z
   points.append((x0+(480+f*xx/depth)*S,y0+(270+f*(-math.sin(e)*yy-math.cos(e)*z)/depth)*S))
  for i in range(8):
   for j in range(i+1,8):
    if i^j in (1,2,4):dr.line((*points[i],*points[j]),fill=ORANGE,width=2)
  dr.rectangle((x0,y0,x0+W,y0+H),outline=INK,width=2)
  bounds=rec['envelope']['bounds_px'];bx=x0+W+24;top=y0+bounds[2]*S;bottom=y0+bounds[3]*S
  dr.line((bx,top,bx,bottom),fill=MAGENTA,width=3)
  for y in (top,bottom):dr.line((bx-8,y,bx+8,y),fill=MAGENTA,width=3)
  actual=rec['envelope']['height_percent'];maximum=max(x['projection']['height_percent'] for x in m['calibrations'][mode]['views'])
  dr.text((18,414),f'Cube height now: {actual:.2f}% H; maximum: {maximum:.2f}% H',font=small,fill=INK)
  dr.text((18,442),f'Fixed cube edge: {edge:.6f} m; mesh scale: {rec["placement"]["uniform_scale"]:.6f}',font=small,fill=INK)
  canvas.paste(panel,(col*PW,HEADER+row*PH))
path=out/'a380_cube_reference_vs_turn_max_target70.png'
if path.exists():raise SystemExit('Refusing overwrite')
canvas.save(path);print(path)
