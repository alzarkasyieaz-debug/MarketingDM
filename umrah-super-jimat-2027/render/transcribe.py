"""Whisper large-v3 transcription of the Master Video in short windows (long windows collapsed on this recording)."""
import json,numpy as np,wave
from faster_whisper import WhisperModel
m=WhisperModel("large-v3",device="cpu",compute_type="int8",cpu_threads=4)
wf=wave.open("/home/user/work/master16k.wav");a=np.frombuffer(wf.readframes(wf.getnframes()),np.int16).astype(np.float32)/32768
out=[]
for s0,s1 in [(1.5,9.8),(9.3,16.0),(15.5,30.5),(29.0,67.5)]:
    segs,_=m.transcribe(a[int(s0*16000):int(s1*16000)],language="ms",word_timestamps=True,beam_size=5,condition_on_previous_text=False)
    for s in segs:
        print(f"[{s.start+s0:6.2f}-{s.end+s0:6.2f}] {s.text}",flush=True)
        out.append({"s":round(s.start+s0,2),"e":round(s.end+s0,2),"t":s.text,"w":[[round(w.start+s0,2),round(w.end+s0,2),w.word] for w in s.words]})
json.dump(out,open("/home/user/work/tx_windows.json","w"),ensure_ascii=False)
