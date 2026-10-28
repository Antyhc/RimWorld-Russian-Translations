"""Render an original typographic fallback; never reads original mod artwork."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

def render(title,output,font_path):
    out=Path(output)
    if out.exists():raise ValueError('Output already exists')
    canvas=Image.new('RGB',(1024,1024),(27,34,44));draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype(str(font_path),104)
    words=title.split();lines=[];line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if draw.textbbox((0,0),candidate,font=font)[2]>880 and line:
            lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    y=350-len(lines)*62
    for line in lines:
        box=draw.textbbox((0,0),line,font=font)
        draw.text(((1024-box[2])/2,y),line,font=font,fill=(242,242,235));y+=126
    draw.rectangle((0,728,1023,1023),fill=(164,44,43))
    russian=ImageFont.truetype(str(font_path),172)
    box=draw.textbbox((0,0),'RUSSIAN',font=russian)
    draw.text(((1024-box[2])/2,772),'RUSSIAN',font=russian,fill=(255,255,255))
    out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,optimize=True)
    return {'design':'original_typographic_fallback','title':title,'dimensions':[1024,1024],'original_mod_art_used':False,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('title');ap.add_argument('output');ap.add_argument('--font',required=True);a=ap.parse_args()
    print(json.dumps(render(a.title,a.output,a.font)))
