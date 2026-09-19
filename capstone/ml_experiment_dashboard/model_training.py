import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, accuracy_score


def train_model(df, target_column):
    # Only use numeric columns for features, excluding the target column and any unnamed columns
    feature_columns = [
        column for column in df.columns
        if column != target_column and not column.startswith("Unnamed")
    ]
    numeric_feature_columns = df[feature_columns].select_dtypes(include="number").columns.tolist()

    if not numeric_feature_columns:
        raise ValueError("No numeric feature columns available to train a model.")

    # Clean the data by filling missing values with the mean for numeric features
    X = df[numeric_feature_columns].fillna(df[numeric_feature_columns].mean())
    y = df[target_column]

    # Determine if the problem is regression or classification based on the target column's data type
    # Regression if the target column is numeric, classification otherwise
    is_regression = pd.api.types.is_numeric_dtype(y)

    # Split the data into training and testing sets (80% training, 20% testing)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale the features using StandardScaler to ensure that they have a mean of 0 and a standard deviation of 1
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train the appropriate model based on the problem type and evaluate its performance
    if is_regression: # Regression problem
        model = LinearRegression()
        model.fit(X_train_scaled, y_train)
        predictions = model.predict(X_test_scaled) # Make predictions on the test set
        metric_name = "r2_score"
        metric_value = r2_score(y_test, predictions)
        model_name = "LinearRegression"
        problem_type = "regression"
    else: # Classification problem 
        model = LogisticRegression(max_iter=1000)
        model.fit(X_train_scaled, y_train)
        predictions = model.predict(X_test_scaled) # Make predictions on the test set
        metric_name = "accuracy"
        metric_value = accuracy_score(y_test, predictions)
        model_name = "LogisticRegression"
        problem_type = "classification"

    return {
        "problem_type": problem_type,
        "model": model_name,
        "target_column": target_column,
        "feature_columns": numeric_feature_columns,
        "metric_name": metric_name,
        "metric_value": round(float(metric_value), 4),
    }
