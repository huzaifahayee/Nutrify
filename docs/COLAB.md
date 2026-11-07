# Nutrify Colab (T4 GPU)

Copy each cell. Runtime: **Runtime → Change runtime type → T4 GPU**.

Zip `data/processed/` on your laptop and upload that zip to Drive first.

## 1. Drive, data, repo

```python
# Edit this path if your zip lives somewhere else on Drive.
DRIVE_ZIP = "/content/drive/MyDrive/Nutrify/processed.zip"
REPO_URL = "https://github.com/huzaifahayee/Nutrify.git"
BRANCH = "huzaifa/deliverable2"

from google.colab import drive
drive.mount("/content/drive")

!mkdir -p /content/data
!unzip -q -o "{DRIVE_ZIP}" -d /content/data
# Zip should unpack to /content/data/processed/{train,val,test}/...
# If the zip already contains a `processed/` folder, that path is correct.
# If it unpacked one extra folder, fix DATA_DIR below.

DATA_DIR = "/content/data/processed"
DRIVE_OUT = "/content/drive/MyDrive/Nutrify/colab_out"

!git clone {REPO_URL} /content/Nutrify || (cd /content/Nutrify && git fetch && git checkout {BRANCH} && git pull origin {BRANCH})
%cd /content/Nutrify
!git checkout {BRANCH}
!pip install -q -r requirements.txt

import os
os.makedirs(DRIVE_OUT, exist_ok=True)
print("cuda:", __import__("torch").cuda.is_available())
```

## 2. Copy outputs to Drive (run after every training cell)

```python
!mkdir -p "{DRIVE_OUT}"
!cp -r /content/Nutrify/checkpoints "{DRIVE_OUT}/" 2>/dev/null || true
!cp -r /content/Nutrify/results "{DRIVE_OUT}/" 2>/dev/null || true
print("copied checkpoints/ and results/ to", DRIVE_OUT)
```

## 3. Smoke (2 epochs)

```python
!python src/train.py --model efficientnet --data-dir {DATA_DIR} --epochs 2 --head-epochs 1 --batch-size 32 --num-workers 2
```

Then run the copy-to-Drive cell.

## 4. Tune (one factor at a time, 8 runs)

```python
!python src/tune.py --data-dir {DATA_DIR} --max-epochs 8 --num-workers 2
```

Then run the copy-to-Drive cell. Read the printed `python src/train.py ...` command.

## 5. Final EfficientNet run

Paste the command from step 4, or this default if tune has not finished:

```python
!python src/train.py --model efficientnet --data-dir {DATA_DIR} --epochs 20 --head-epochs 5 --lr 1e-3 --finetune-lr 1e-4 --batch-size 32 --dropout 0.3 --weight-decay 1e-4 --label-smoothing 0.1 --num-workers 2
```

Then run the copy-to-Drive cell. You want `results/hparam_results.csv`, `results/history_efficientnet.csv`, `results/curves_efficientnet.png`, `results/preds_efficientnet_test.csv`.

## 6. Put results in Git (pick one)

**(a) Laptop (safer).** Download the `results/` folder from Drive. On your laptop, on `huzaifa/deliverable2`:

```bash
git add results/hparam_results.csv results/history_efficientnet.csv results/curves_efficientnet.png results/preds_efficientnet_test.csv
git commit -m "Add EfficientNet tuning results, curves and test predictions"
git pull --rebase origin main
git push
```

**(b) Push from Colab.** In Colab: the key icon → Secrets → add `GITHUB_TOKEN` (a GitHub personal access token with repo scope).

**Never paste the token into a notebook cell.**

```python
from google.colab import userdata
token = userdata.get("GITHUB_TOKEN")

!git config user.name "Muhammad Huzaifa"
!git config user.email "huzaifahayee751@gmail.com"
!git add results/hparam_results.csv results/history_efficientnet.csv results/curves_efficientnet.png results/preds_efficientnet_test.csv
!git commit -m "Add EfficientNet tuning results, curves and test predictions"
!git pull --rebase origin {BRANCH}
!git push https://{token}@github.com/huzaifahayee/Nutrify.git HEAD:{BRANCH}
```

Do not `git add checkpoints/` or `*.pt`. Do not add `runs/`.
