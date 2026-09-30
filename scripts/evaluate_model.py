"""
Leakage-aware evaluation of the gesture classifier.

collect_data.py saves each gesture instance as a burst of 20 consecutive
frames, appended to data/gestures.csv in capture order, so every block of
20 rows is one burst. Frames within a burst are near-duplicates: a random
row split puts frames of the same burst on both sides and the score says
more about memorisation than about new gestures.

This script compares:
  1. the random stratified 80/20 row split used by train_model.py;
  2. a burst-wise 80/20 split (no burst on both sides);
  3. 5 x 5 repeated stratified group k-fold over bursts.

It does not overwrite models/gesture_model.pkl.

    python scripts/evaluate_model.py
"""

import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold, train_test_split

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "gestures.csv")
BURST_FRAMES = 20


def make_model():
    # Same settings as train_model.py.
    return RandomForestClassifier(n_estimators=500, random_state=42, n_jobs=-1)


def main():
    df = pd.read_csv(DATA_PATH)
    y = df["label"].values
    X = df.drop(columns="label")
    bursts = np.arange(len(df)) // BURST_FRAMES

    if any(len(set(y[bursts == b])) != 1 for b in np.unique(bursts)):
        raise SystemExit("A 20-row block mixes labels; the CSV is not in burst order.")

    labels = sorted(set(y))
    print(f"{len(df)} samples, {bursts.max() + 1} bursts, {len(labels)} gestures\n")

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    pred = make_model().fit(X_tr, y_tr).predict(X_te)
    print(f"Random row split (leaks bursts):  accuracy {accuracy_score(y_te, pred):.3f}, "
          f"macro-F1 {f1_score(y_te, pred, average='macro'):.3f}")

    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42).split(X, y, bursts))
    pred = make_model().fit(X.iloc[tr], y[tr]).predict(X.iloc[te])
    print(f"Burst-wise split ({len(set(bursts[te]))} held-out bursts): accuracy {accuracy_score(y[te], pred):.3f}, "
          f"macro-F1 {f1_score(y[te], pred, average='macro'):.3f}")

    accs, f1s = [], []
    for rep in range(5):
        cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=rep)
        for tr_i, te_i in cv.split(X, y, bursts):
            p = make_model().fit(X.iloc[tr_i], y[tr_i]).predict(X.iloc[te_i])
            accs.append(accuracy_score(y[te_i], p))
            f1s.append(f1_score(y[te_i], p, average="macro"))
    print(f"5x5 grouped cross-validation:     accuracy {np.mean(accs):.3f} +- {np.std(accs, ddof=1):.3f}, "
          f"macro-F1 {np.mean(f1s):.3f} +- {np.std(f1s, ddof=1):.3f}")

    print("\nConfusion matrix, burst-wise split (rows = true):")
    cm = pd.DataFrame(confusion_matrix(y[te], pred, labels=labels), index=labels, columns=labels)
    print(cm.to_string())


if __name__ == "__main__":
    main()
