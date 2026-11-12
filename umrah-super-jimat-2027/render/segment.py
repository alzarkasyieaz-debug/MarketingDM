"""AI subject cut-out: per-frame presenter matte from the Master Video (rembg u2net_human_seg).
Writes a uint8 memmap (n_frames, 960, 540) indexed by master frame number (30 fps)."""
import os, subprocess, sys
import numpy as np
from PIL import Image
from rembg import new_session, remove

MASTER = os.environ.get("MASTER", "/home/user/src2/master.mov")
OUT = os.environ.get("WORK", "/home/user/work")
T0, T1, FPS = 1.6, 67.0, 30
W, H = 540, 960
f0, f1 = int(T0 * FPS), int(T1 * FPS)
mm = np.lib.format.open_memmap(f"{OUT}/masks.npy", mode="w+", dtype=np.uint8, shape=(f1, H, W))
sess = new_session("u2net_human_seg")
p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(f0 / FPS), "-i", MASTER, "-frames:v", str(f1 - f0),
                      "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
i = f0
while i < f1:
    buf = p.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    im = Image.frombuffer("RGB", (W, H), buf)
    mm[i] = np.asarray(remove(im, session=sess, only_mask=True, post_process_mask=False))
    if i % 100 == 0: print(i, f1, flush=True)
    i += 1
mm.flush(); print("done", i)
