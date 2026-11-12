"""Step 1: cut, reframe (9:16), animate (zoom) and colour-grade every segment, then concat to base.mp4."""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from timeline import SEGMENTS, OUT, W, H, FPS

GRADE = {
    "master": "eq=contrast=1.04:saturation=1.06,colorbalance=rm=0.025:bm=-0.025",
    "broll": "eq=contrast=1.06:saturation=1.10:gamma=0.98,colorbalance=rs=0.04:bs=-0.04:rm=0.03:bm=-0.03,vignette=PI/5",
    "hook": "eq=contrast=1.08:saturation=1.12:gamma=0.96,colorbalance=rs=0.04:bs=-0.04:rm=0.03:bm=-0.03,vignette=PI/4.5",
    "dim": "eq=contrast=1.05:saturation=1.0:brightness=-0.10,colorbalance=rs=0.04:bs=-0.04,vignette=PI/4",
    "bg": "gblur=sigma=22,eq=brightness=-0.16:saturation=0.85,colorbalance=rs=0.03:bs=-0.03,vignette=PI/4",
}

def zoom_expr(z0, z1, d, style):
    if style == "hook" or (style == "bg" and z0 > 1.15):
        # crash zoom: fast ease-out, then slow drift
        return f"({z1}-0.03*t/{d}+({z0}-{z1})*exp(-7*t))"
    return f"({z0}+({z1}-{z0})*t/{d})"

def main():
    os.makedirs(f"{OUT}/seg", exist_ok=True)
    lst = []
    for i, (src, ss, d, z0, z1, style) in enumerate(SEGMENTS):
        out = f"{OUT}/seg/{i:02d}.mp4"
        Z = zoom_expr(z0, z1, d, style)
        vf = (f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
              f"scale=w='2*trunc({W//2}*{Z})':h='2*trunc({H//2}*{Z})':eval=frame:flags=bicubic,"
              f"crop={W}:{H},{GRADE[style]},format=yuv420p")
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", src, "-t", str(d), "-an",
               "-vf", vf, "-r", str(FPS), "-frames:v", str(round(d * FPS)),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", out]
        print(f"[{i:02d}] {os.path.basename(src)} ss={ss} d={d} {style}", flush=True)
        subprocess.run(cmd, check=True)
        lst.append(f"file '{os.path.abspath(out)}'")
    with open(f"{OUT}/seg/list.txt", "w") as f:
        f.write("\n".join(lst) + "\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{OUT}/seg/list.txt",
                    "-c", "copy", f"{OUT}/base.mp4"], check=True)

if __name__ == "__main__":
    main()
