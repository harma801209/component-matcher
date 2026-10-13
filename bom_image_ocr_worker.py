"""CPU image-recognition worker; its packages are isolated from the web app."""
from __future__ import annotations

import argparse
import io
import json
import platform
import sys
from pathlib import Path

if sys.platform == 'win32' and sys.version_info >= (3,14):
    platform._wmi = None


def recognize_strips(recognizer, crops):
    import re
    import numpy as np
    results = [None] * len(crops)
    order = np.argsort([crop.shape[1] / crop.shape[0] for crop in crops])
    for start in range(0, len(order), recognizer.rec_batch_num):
        ids = order[start:start + recognizer.rec_batch_num]
        ratio = max(crops[idx].shape[1] / crops[idx].shape[0] for idx in ids)
        batch = np.asarray([recognizer.resize_norm_img(crops[idx], ratio) for idx in ids], dtype=np.float32)
        predictions = recognizer.session(batch)[0]
        for idx, prediction in zip(ids, predictions):
            crop = crops[idx]
            occupied = np.where((crop.mean(axis=2) < 170).sum(axis=0) > 0)[0]
            gaps = np.where(np.diff(occupied) > max(6, crop.shape[0] * .20))[0]
            spaces = [(occupied[g] + occupied[g+1])/2 for g in gaps]
            sequence, probabilities = prediction.argmax(axis=1), prediction.max(axis=1)
            raw_chars, spaced_chars, scores, uncertain = [], [], [], []
            previous_x = 0.0
            for step, char_id in enumerate(sequence):
                if char_id == 0 or (step and char_id == sequence[step-1]):
                    continue
                char = recognizer.postprocess_op.character[int(char_id)]
                x = (step+.5) * batch.shape[3] / len(sequence) * crop.shape[0] / recognizer.rec_image_shape[1]
                if spaced_chars and any(previous_x < gap <= x for gap in spaces):
                    spaced_chars.append(" ")
                raw_chars.append(char)
                spaced_chars.append(char)
                scores.append(float(probabilities[step]))
                # A high line average must not hide one ambiguous model digit.
                # CTC repeats one character over several frames. The leading
                # boundary frame can be weak even when its centre is certain.
                end = step + 1
                while end < len(sequence) and sequence[end] == char_id:
                    end += 1
                best_step = step + int(np.argmax(probabilities[step:end]))
                alternatives = np.argsort(prediction[best_step])[-2:][::-1]
                rival = next((int(value) for value in alternatives if value != char_id), 0)
                confidence = float(probabilities[best_step])
                margin = float(confidence - prediction[best_step, rival])
                if confidence < .75 or margin < .15:
                    uncertain.append({'index': len(raw_chars)-1, 'char': char,
                                      'alternative': recognizer.postprocess_op.character[rival],
                                      'score': confidence, 'margin': margin})
                previous_x = x
            raw = "".join(raw_chars)
            is_description = "/SMD" in raw.upper() or bool(re.search(r"\d\s*(?:[pnuµμ]F|Ω|W)\b", raw, re.I))
            results[idx] = ("".join(spaced_chars) if is_description else raw,
                            sum(scores) / max(1, len(scores)+1),
                            {'minimum': min(scores, default=0.0), 'uncertain': uncertain})
    return results


def load_recognizer():
    import rapidocr_onnxruntime
    from rapidocr_onnxruntime.ch_ppocr_v3_rec.text_recognize import TextRecognizer
    from rapidocr_onnxruntime.utils import read_yaml
    root = Path(rapidocr_onnxruntime.__file__).parent
    config = read_yaml(root / "config.yaml")["Rec"]
    config["model_path"] = str(root / config["model_path"])
    return TextRecognizer(config)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--packages', type=Path, required=True)
    parser.add_argument('--health', action='store_true')
    args = parser.parse_args()
    # Only this subprocess sees the new packages. Existing Streamlit, NumPy,
    # member and price modules in the parent process remain untouched.
    sys.path.insert(0, str(args.packages.resolve()))
    import numpy as np
    recognizer = load_recognizer()
    if args.health:
        # Probe real inference, not just import/installation metadata.
        recognizer([np.full((24, 120, 3), 255, dtype=np.uint8)])
        print(json.dumps({'ready': True}))
        return
    with np.load(io.BytesIO(sys.stdin.buffer.read()), allow_pickle=False) as payload:
        crops = [payload[str(idx)] for idx in range(len(payload.files))]
    print(json.dumps(recognize_strips(recognizer, crops), ensure_ascii=False))


if __name__ == '__main__':
    main()
