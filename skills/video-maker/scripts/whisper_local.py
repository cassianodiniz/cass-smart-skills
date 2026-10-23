"""Adapter local: Whisper turbo via faster-whisper, com saída compatível com MLX."""
import argparse
import json
from pathlib import Path


def converter(segmentos):
    return [{'start': s.start, 'end': s.end, 'text': s.text,
             'words': [{'start': w.start, 'end': w.end, 'word': w.word,
                        'probability': w.probability} for w in (s.words or [])]}
            for s in segmentos]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('audio')
    p.add_argument('--model', required=True)
    p.add_argument('--language', default='pt')
    p.add_argument('--task', default='transcribe')
    p.add_argument('--word-timestamps', default='True')
    p.add_argument('--output-format', default='json')
    p.add_argument('--output-dir', required=True)
    a = p.parse_args()
    if a.model != 'faster-whisper/turbo':
        p.error('Esta distribuição usa o modelo Whisper large-v3-turbo (turbo).')
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        p.error('Transcritor local ausente; prepare as ferramentas com instalar_ferramentas.py --transcricao ou forneça a transcrição com tempos.')
    model = WhisperModel('turbo', device='cpu', compute_type='int8')
    segmentos, info = model.transcribe(a.audio, language=a.language, task=a.task,
                                      word_timestamps=True, condition_on_previous_text=True,
                                      vad_filter=False)
    data = converter(segmentos)
    out = Path(a.output_dir) / (Path(a.audio).stem + '.json')
    out.write_text(json.dumps({'text': ''.join(x['text'] for x in data), 'segments': data,
                              'language': info.language, 'backend': 'faster-whisper/turbo'},
                             ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
