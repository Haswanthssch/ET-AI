"""
AURA-EPC ML Model: XGBoost Schedule Delay Predictor
Trains and serves a binary classifier that predicts whether a given
task will be delayed based on schedule + supply chain features.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

MODELS_DIR = Path("./data/models")
MODEL_PATH = MODELS_DIR / "delay_predictor.joblib"
ENCODER_PATH = MODELS_DIR / "label_encoders.joblib"


def _build_features(schedule_df: pd.DataFrame, supply_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge schedule and supply chain data to create feature matrix.
    """
    supply_map = supply_df.set_index("equipment_tag")[["lead_time_days", "delay_days", "status"]].to_dict("index")

    rows = []
    for _, row in schedule_df.iterrows():
        tag = str(row.get("equipment_tag", ""))
        supply = supply_map.get(tag, {})
        features = {
            "duration_days": int(row["duration_days"]),
            "float_days": int(row.get("float_days", 0)),
            "is_critical": int(row.get("is_critical", 0)),
            "phase_encoded": str(row.get("phase", "UNKNOWN")),
            "lead_time_days": int(supply.get("lead_time_days", 0)),
            "supply_delay_days": int(supply.get("delay_days", 0)),
            "supply_status_encoded": str(supply.get("status", "On Track")),
            "has_equipment": int(bool(tag and tag != "nan")),
            # Synthetic label: delayed if float consumed or supply delay > float
            "delayed": int(
                int(supply.get("delay_days", 0)) > int(row.get("float_days", 0))
                or int(row.get("is_critical", 0)) == 1 and int(supply.get("delay_days", 0)) > 0
            ),
        }
        rows.append(features)
    return pd.DataFrame(rows)


def train_model(
    schedule_csv: str = "./data/master_schedule.csv",
    supply_csv: str = "./data/supply_chain.csv",
) -> dict[str, Any]:
    """Train XGBoost classifier and persist to disk."""
    if not XGB_AVAILABLE:
        return {"error": "xgboost not installed"}

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    schedule_df = pd.read_csv(schedule_csv)
    supply_df = pd.read_csv(supply_csv)

    df = _build_features(schedule_df, supply_df)

    # Encode categoricals
    le_phase = LabelEncoder()
    le_status = LabelEncoder()
    df["phase_encoded"] = le_phase.fit_transform(df["phase_encoded"])
    df["supply_status_encoded"] = le_status.fit_transform(df["supply_status_encoded"])

    feature_cols = [
        "duration_days", "float_days", "is_critical",
        "phase_encoded", "lead_time_days", "supply_delay_days",
        "supply_status_encoded", "has_equipment",
    ]
    X = df[feature_cols].values
    y = df["delayed"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)

    joblib.dump(model, MODEL_PATH)
    joblib.dump({"phase": le_phase, "status": le_status}, ENCODER_PATH)

    return {
        "status": "trained",
        "samples": len(df),
        "delayed_ratio": float(y.mean()),
        "accuracy": report.get("accuracy", 0),
    }


def predict_delay_probability(features: dict[str, Any]) -> float:
    """
    Predict delay probability for a single task.
    features keys: duration_days, float_days, is_critical, phase,
                   lead_time_days, supply_delay_days, supply_status, has_equipment
    """
    if not MODEL_PATH.exists():
        # Return heuristic if model not trained yet
        delay = features.get("supply_delay_days", 0)
        float_val = features.get("float_days", 0)
        critical = features.get("is_critical", 0)
        if critical and delay > 0:
            return min(0.95, 0.5 + delay / 100)
        if delay > float_val:
            return min(0.85, 0.3 + (delay - float_val) / 100)
        return 0.1

    model = joblib.load(MODEL_PATH)
    encoders = joblib.load(ENCODER_PATH)

    phase_enc = encoders["phase"]
    status_enc = encoders["status"]

    phase_str = features.get("phase", "UNKNOWN")
    status_str = features.get("supply_status", "On Track")

    try:
        phase_val = phase_enc.transform([phase_str])[0]
    except ValueError:
        phase_val = 0
    try:
        status_val = status_enc.transform([status_str])[0]
    except ValueError:
        status_val = 0

    X = np.array([[
        features.get("duration_days", 10),
        features.get("float_days", 5),
        features.get("is_critical", 0),
        phase_val,
        features.get("lead_time_days", 0),
        features.get("supply_delay_days", 0),
        status_val,
        features.get("has_equipment", 0),
    ]])
    prob = model.predict_proba(X)[0][1]
    return float(prob)

