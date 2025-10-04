import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import lightgbm as lgb
import joblib
import os

# --- Configuration ---
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

FEATURES_CSV = os.path.join(DATA_DIR, "features.csv")
IMPACT_CSV = os.path.join(DATA_DIR, "size_impact.csv")
MODEL_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "inlining_impact_model_scaled.joblib")

def main():
    print("--- Starting Final Step: Model Training & Evaluation on Scaled Data ---")

    # 1. Load and Merge Data
    try:
        features_df = pd.read_csv(FEATURES_CSV)
        size_df = pd.read_csv(IMPACT_CSV)
    except FileNotFoundError as e:
        print(f"Error: {e}. Please ensure both 'features.csv' and 'size_impact.csv' exist.")
        return

    # Merge the two dataframes on the function and file name
    data = pd.merge(features_df, size_df, on=["function_name", "file_name"])
    print(f"\nSuccessfully loaded and merged data. Total records: {len(data)}")

    # 2. Prepare Data for Modeling
    # Define the features (X) and the target (y)
    feature_columns = [
        "cyclomatic_complexity", "parameter_count", "local_variable_count",
        "body_size_stmts", "token_count", "is_complex_return"
    ]
    X = data[feature_columns]
    y = data["size_increase_percent"]

    # **CRITICAL STEP**: Split data into training and testing sets
    # We'll use 80% for training and 20% for testing.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Data split into {len(X_train)} training samples and {len(X_test)} testing samples.")

    # 3. Train the LightGBM Regressor
    print("\n--- Training Model ---")
    model = lgb.LGBMRegressor(
        random_state=42,
        n_estimators=200,      # Increased estimators for a larger dataset
        learning_rate=0.05,
        num_leaves=31,
        reg_alpha=0.1,         # Added L1 regularization
        reg_lambda=0.1,        # Added L2 regularization
        verbose=-1             # **FIX**: Control verbosity in the constructor
    )
    # The 'verbose' argument has been removed from the fit method.
    model.fit(X_train, y_train)
    print("Model training complete.")

    # 4. Evaluate the Model on the unseen TEST set
    print("\n--- Model Evaluation on Test Set ---")
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"Mean Absolute Error (MAE): {mae:.2f}%")
    print(f"R-squared (R2 Score): {r2:.2f}")
    print("(This score reflects the model's performance on unseen data.)")

    # 5. Feature Importance
    print("\n--- Feature Importance ---")
    feature_imp = pd.DataFrame(sorted(zip(model.feature_importances_, X.columns)), columns=['Value','Feature'])
    print(feature_imp.sort_values(by="Value", ascending=False))

    # 6. Save the Trained Model
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    joblib.dump(model, MODEL_OUTPUT_PATH)
    print(f"\nModel saved successfully to '{MODEL_OUTPUT_PATH}'")


if __name__ == "__main__":
    main()