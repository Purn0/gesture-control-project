import os
import sys

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "gestures.csv")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "gesture_model.pkl")


def main():
    if not os.path.exists(DATA_PATH):
        print("Dataset not found.")
        return

    os.makedirs(MODELS_DIR, exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    if df.empty:
        print("Dataset is empty.")
        return

    expected_cols = 43

    if len(df.columns) != expected_cols:
        print(f"Unexpected column count: {len(df.columns)} (expected {expected_cols})")
        return

    print("Initial rows:", len(df))

    # keep only valid labels
    valid_labels = {
        "Open_Palm",
        "Closed_Fist",
        "Thumb_Up",
        "Victory",
        "Pointing_Up",
        "Thumb_Down",
        "Call_Me",
        "Rock"
    }
    df = df[df["label"].isin(valid_labels)].copy()

    # convert all feature columns to numeric, invalid strings become NaN
    feature_cols = [c for c in df.columns if c != "label"]

    for col in feature_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # drop bad rows
    bad_before = len(df)
    df = df.dropna(subset=feature_cols)
    removed = bad_before - len(df)

    print("Rows after cleaning:", len(df))
    print("Removed bad rows:", removed)

    if df.empty:
        print("No valid data left after cleaning.")
        return

    X = df[feature_cols]
    y = df["label"]

    print("\nClass counts:")
    print(y.value_counts())
    print("\nClasses:")
    print(sorted(y.unique()))

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"\nAccuracy: {acc * 100:.2f}%\n")
    print("Classification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            labels=sorted(valid_labels)
        )
    )

    print("Confusion Matrix:")
    cm = confusion_matrix(
        y_test,
        y_pred,
        labels=sorted(valid_labels)
    )

    print("\nConfusion Matrix:\n")
    print(cm)

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()