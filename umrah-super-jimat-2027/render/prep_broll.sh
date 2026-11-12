#!/usr/bin/env bash
# HDR (HLG) -> SDR tonemap, portrait 1080x1920 @30fps, short selected segments of the real B-roll.
set -e
SRC=${SRC_DIR:-/home/user/src2}; W=${WORK:-/home/user/work}; mkdir -p $W/br
TM="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
SC="scale=1080:1920:flags=lanczos,setsar=1"
enc(){ ffmpeg -v error -y "$@" -an -c:v libx264 -crf 14 -preset medium -pix_fmt yuv420p -r 30; }
# 59.94 fps source -> natural 2x slow motion
enc -ss 0.5  -t 4.0 -i $SRC/broll/IMG_5542.MOV -vf "$TM,$SC,setpts=2*PTS" $W/br/jemaah1.mp4
enc -ss 37   -t 4.0 -i $SRC/broll/IMG_5542.MOV -vf "$TM,$SC,setpts=2*PTS" $W/br/jemaah2.mp4
enc -ss 85   -t 3.5 -i $SRC/broll/IMG_5542.MOV -vf "$TM,$SC,setpts=2*PTS" $W/br/jemaah3.mp4
enc -ss 70   -t 2.0 -i $SRC/broll/IMG_5542.MOV -vf "$TM,$SC,setpts=2*PTS" $W/br/jemaah4.mp4
enc -ss 0    -t 15.9 -i $SRC/broll/IMG_6637.MOV -vf "$TM,$SC" $W/br/lobi.mp4
enc -ss 0    -t 8.6 -i $SRC/broll/IMG_7522.MOV -vf "$TM,$SC" $W/br/haram.mp4
# Kaabah (landscape SDR, 1.6 s): portrait crop around the Kaabah + motion-interpolated 3x slow motion
enc -i $SRC/broll/IMG_7405.MOV -vf "crop=640:1080:560:0,minterpolate=fps=90:mi_mode=mci:mc_mode=aobmc,setpts=3*PTS,scale=1080:1920:flags=lanczos,unsharp=5:5:0.6,eq=contrast=1.06:saturation=1.1,setsar=1" $W/br/kaabah.mp4
ls -la $W/br
