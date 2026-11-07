"""Encode diagnostic videos and verify lossless decoded frames against PNG pixels."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out
m=json.loads((out/'manifest.json').read_text());results=[]
def run(args):return subprocess.check_output(args,stderr=subprocess.STDOUT,text=True)
for frame in m['frames']:assert hashlib.sha256((out/frame['png']).read_bytes()).hexdigest()==frame['sha256']
for case in m['cases']:
 d=out/case['directory'];seq=str(d/'frame_%03d.png');lossless=d/'turn_lossless.mkv';preview=d/'turn_preview.mp4'
 run(['ffmpeg','-v','error','-framerate','6','-i',seq,'-frames:v','12','-c:v','ffv1','-pix_fmt','bgra','-threads','2',str(lossless)])
 run(['ffmpeg','-v','error','-framerate','6','-i',seq,'-filter_complex','color=c=0xADD9E6:s=640x360:r=6[bg];[bg][0:v]overlay=shortest=1,format=yuv420p','-frames:v','12','-c:v','libx264','-crf','18','-threads','2',str(preview)])
 original=run(['ffmpeg','-v','error','-framerate','6','-i',seq,'-pix_fmt','bgra','-f','framemd5','-'])
 decoded=run(['ffmpeg','-v','error','-i',str(lossless),'-pix_fmt','bgra','-f','framemd5','-'])
 hashes=lambda s:[line.split(',')[-1].strip() for line in s.splitlines() if line and not line.startswith('#')]
 oh,dh=hashes(original),hashes(decoded);assert len(oh)==12 and oh==dh
 for video in (lossless,preview):
  probe=json.loads(run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,width,height,avg_frame_rate','-of','json',str(video)]))['streams'][0]
  assert int(probe['nb_read_frames'])==12 and probe['width']==640 and probe['height']==360 and probe['avg_frame_rate']=='6/1'
 (d/'original_pixels.framemd5').write_text(original);(d/'decoded_pixels.framemd5').write_text(decoded)
 results.append({'mesh':case['mesh'],'kind':case['kind'],'frames':12,'lossless_decoded_pixels_exact':True,'decoded_frame_hashes':dh,'lossless_sha256':hashlib.sha256(lossless.read_bytes()).hexdigest(),'preview_sha256':hashlib.sha256(preview.read_bytes()).hexdigest()})
 print('VIDEO_OK',case['directory'],flush=True)
(out/'video_validation.json').write_text(json.dumps({'ffmpeg_version':run(['ffmpeg','-version']).splitlines()[0],'results':results},indent=2)+'\n')
