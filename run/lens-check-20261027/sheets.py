import sys, glob, os, datetime as dt, json
import cv2, numpy as np
root, spool = sys.argv[1], sys.argv[2]
played = {}
for line in open(os.path.join(spool, '..', 'played.jsonl'), encoding='utf-8'):
    d = json.loads(line); played[d['id']] = d
def label(img, text):
    img = img.copy(); cv2.rectangle(img, (0, 0), (img.shape[1], 22), (0, 0, 0), -1)
    cv2.putText(img, text, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA); return img
W = 256
def tile(imgs, per_row=6):
    rows = []
    for i in range(0, len(imgs), per_row):
        row = imgs[i:i+per_row]
        while len(row) < per_row: row.append(np.zeros_like(imgs[0]))
        rows.append(np.hstack(row))
    return np.vstack(rows)
for d in sorted(glob.glob(os.path.join(root, 'cw-*'))):
    inc = os.path.basename(d)
    files = sorted(glob.glob(os.path.join(d, '*.jpg')))
    rec = []
    for f in files:
        ms = int(os.path.basename(f)[:-4]); img = cv2.imread(f)
        if img is None: continue
        h = round(img.shape[0] * W / img.shape[1]); img = cv2.resize(img, (W, h))
        rec.append(label(img, 'REC ' + dt.datetime.fromtimestamp(ms/1000, dt.timezone.utc).strftime('%H:%M:%S.%f')[:-3]))
    sent = []
    jobs = [j for j in played if f"_{inc}-" in j and j.startswith("20261026T1")]
    for j in jobs:
        avi = os.path.join(spool, j + '.avi')
        cap = cv2.VideoCapture(avi)
        frames = []
        while True:
            ok, fr = cap.read()
            if not ok: break
            frames.append(fr)
        cap.release()
        if frames:
            idx = sorted(set([0, len(frames)//4, len(frames)//2, 3*len(frames)//4, len(frames)-1]))
            p = played[j]
            for k in idx:
                fr = frames[k]; h = round(fr.shape[0] * W / fr.shape[1]); fr = cv2.resize(fr, (W, h))
                sent.append(label(fr, f"SENT {j.split('_')[0][9:15]} f{k}/{len(frames)} {p['start'][11:19]}-{p['end'][11:19]}"))
    if not rec and not sent: continue
    hmax = max([i.shape[0] for i in rec + sent])
    def pad(i): return cv2.copyMakeBorder(i, 0, hmax - i.shape[0], 0, 0, cv2.BORDER_CONSTANT)
    parts = []
    if sent: parts.append(tile([pad(i) for i in sent]))
    if rec: parts.append(tile([pad(i) for i in rec]))
    out = np.vstack(parts)
    cv2.imwrite(os.path.join(root, f'{inc}_sheet.jpg'), out, [cv2.IMWRITE_JPEG_QUALITY, 80])
    print(inc, 'sent frames', len(sent), 'recorded frames', len(rec), '->', out.shape)
