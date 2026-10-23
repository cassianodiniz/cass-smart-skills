"""Folha de contato portátil: folha.py video.mp4 folha.png [inicio] [duracao] [fps]."""
import argparse
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

p = argparse.ArgumentParser()
p.add_argument('video')
p.add_argument('imagem')
p.add_argument('inicio', nargs='?', type=float, default=0)
p.add_argument('duracao', nargs='?', default='')
p.add_argument('fps', nargs='?', type=float, default=1)
a = p.parse_args()
video, output = Path(a.video).resolve(), Path(a.imagem).resolve()
total = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(video)], text=True))
duration = min(float(a.duracao) if a.duracao else total - a.inicio, total - a.inicio)
if a.inicio < 0 or duration <= 0 or a.fps <= 0:
    p.error('Início, duração ou frequência inválidos.')
fps = min(a.fps, 120 / duration)
rows = max(1, math.ceil(duration * fps / 6))
with tempfile.TemporaryDirectory() as tmp:
    shutil.copy2(Path(__file__).resolve().parents[1] / 'fonts/inter-700.ttf', Path(tmp) / 'inter.ttf')
    vf = f"fps={fps},scale=270:-2,drawtext=fontfile=inter.ttf:text='%{{pts\\:hms\\:{a.inicio}}}':x=8:y=8:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.6,tile=6x{rows}:padding=4"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(a.inicio), '-t', str(duration), '-i', str(video), '-vf', vf, '-frames:v', '1', str(output)], check=True, cwd=tmp)
print(str(output))
