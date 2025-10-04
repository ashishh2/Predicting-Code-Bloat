import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
import lightgbm as lgb
import joblib
import os
import sys

# --- Configuration ---
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
MODEL_PATH = os.path.join(OUTPUT_DIR, "inlining_impact_model.joblib")

FEATURES_CSV = os.path.join(DATA_DIR, "features.csv")
IMPACT_CSV = os.path.join(DATA_DIR, "size_impact.csv")


def main():
    """Main script to train and evaluate the model."""
    print("--- Starting Step 4: Model Training & Evaluation ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load and Merge Data
    try:
        features_df = pd.read_csv(FEATURES_CSV)
        size_df = pd.read_csv(IMPACT_CSV)
    except FileNotFoundError as e:
        print(f"Error: Could not find data file '{e.filename}'.")
        print("Please ensure you have run the previous scripts successfully.")
        sys.exit(1)

    # Merge the two dataframes on both function and file name for accuracy
    data = pd.merge(features_df, size_df, on=["function_name", "file_name"])
    print("\n--- Merged Training Dataset ---")
    print(data.to_string())

    # 2. Prepare Data for Modeling
    features = ["is_template", "cyclomatic_complexity", "call_site_count", "body_size_stmts"]
    X = data[features]
    y = data["size_increase_percent"]

    # 3. Train the LightGBM Regressor Model
    print("\n--- Training Model ---")

    # FIX: Add hyperparameters suitable for a very small dataset.
    # min_child_samples=1 tells the model it's okay to create a leaf node with just one sample.
    model = lgb.LGBMRegressor(
        random_state=42,
        min_child_samples=1,
        n_estimators=100
    )

    model.fit(X, y)
    print("Model training complete.")

    # 4. Evaluate the Model
    predictions = model.predict(X)
    mae = mean_absolute_error(y, predictions)
    r2 = r2_score(y, predictions)

    print("\n--- Model Evaluation ---")
    print(f"Mean Absolute Error (MAE): {mae:.2f}%")
    print(f"R-squared (R2 Score): {r2:.2f}")

    # Show feature importance
    print("\n--- Feature Importance ---")
    importance_df = pd.DataFrame({'feature': features, 'importance': model.feature_importances_})
    print(importance_df.sort_values('importance', ascending=False).to_string(index=False))

    # 5. Save the Trained Model
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved successfully to '{MODEL_PATH}'")

    # 6. Example Prediction
    print("\n--- Example Prediction ---")
    new_function_features = pd.DataFrame([{
        "is_template": 1,
        "cyclomatic_complexity": 5,
        "call_site_count": 2,
        "body_size_stmts": 15
    }])
    predicted_impact = model.predict(new_function_features)[0]
    print(f"Predicted size impact for a new complex template function: {predicted_impact:.2f}%")


if __name__ == "__main__":
    main()