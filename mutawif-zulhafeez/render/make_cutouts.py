"""Portrait cut-outs (alpha matte) of Ustaz Zulhafeez photos with MODNet, for the photo-reveal treatment."""
import onnxruntime as ort, numpy as np, sys
from PIL import Image, ImageOps, ImageFilter
sess=ort.InferenceSession(sys.argv[1]); iname=sess.get_inputs()[0].name
print([ (i.name,i.shape) for i in sess.get_inputs()],[o.name for o in sess.get_outputs()])
# usage: python3 make_cutouts.py modnet.onnx OUT_DIR photo1.jpg photo2.jpg ...
# model: https://huggingface.co/Xenova/modnet (onnx/model.onnx, Apache-2.0)
for p in sys.argv[3:]:
    im=ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    im.thumbnail((1600,1600))
    w,h=im.size; s=512/max(w,h); rw,rh=int(w*s)//32*32,int(h*s)//32*32
    x=np.asarray(im.resize((rw,rh),Image.BICUBIC),np.float32)/255.
    x=((x-0.5)/0.5).transpose(2,0,1)[None]
    m=sess.run(None,{iname:x})[0][0,0]
    a=Image.fromarray((np.clip(m,0,1)*255).astype(np.uint8)).resize((w,h),Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))
    o=im.convert("RGBA"); o.putalpha(a)
    name=p.split('/')[-1].rsplit('.',1)[0]; o.save(f"{sys.argv[2]}/{name}.png")
    prev=Image.new("RGBA",o.size,(30,40,90,255)); prev.alpha_composite(o); prev.thumbnail((400,400)); prev.convert("RGB").save(f"{sys.argv[2]}/prev_{name}.jpg")
