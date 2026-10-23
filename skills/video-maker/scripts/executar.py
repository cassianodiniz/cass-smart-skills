"""Rodar com o Python do ambiente isolado: executar.py montar.py plano.json."""
import os
from pathlib import Path
import runpy
import sys

scripts = Path(__file__).resolve().parent
if len(sys.argv) < 2 or Path(sys.argv[1]).name != sys.argv[1]:
    sys.exit('Informe o nome do script incluído e seus argumentos.')
script = scripts / sys.argv[1]
if script.suffix != '.py' or not script.is_file() or script.name in {'executar.py', 'instalar_ferramentas.py'}:
    sys.exit('Script de edição inválido.')
if not all(__import__('shutil').which(x) for x in ['ffmpeg', 'ffprobe']):
    import static_ffmpeg
    static_ffmpeg.add_paths(weak=True)
sys.path.insert(0, str(scripts))
sys.argv = [str(script), *sys.argv[2:]]
runpy.run_path(str(script), run_name='__main__')
