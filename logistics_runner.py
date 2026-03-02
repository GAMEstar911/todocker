import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

class LogisticsRunner:
    def __init__(self, data: pd.DataFrame, random_state: int = 100):
        self.data = data
        self.random_state = random_state
        self.target_column = data.columns[-1]
        self.feature_columns = [col for col in data.columns[:-1] if pd.api.types.is_numeric_dtype(data[col])]

    def preprocess_data(self) -> pd.DataFrame:
        # Keep only feature columns and the target column
        self.data = self.data[self.feature_columns + [self.target_column]]

        if self.data.isnull().any().any():
            raise ValueError("Dataset contains missing values. Please clean the data before uploading.")

        return self.data

    def split_data(self, dataset: pd.DataFrame) -> dict:
        # Normalize numerical features
        numerical_features = self.feature_columns
        feature_mean = dataset[numerical_features].mean()
        feature_std = dataset[numerical_features].std()
        normalized_dataset = dataset.copy()
        normalized_dataset[numerical_features] = (dataset[numerical_features] - feature_mean) / feature_std
        
        # Convert target column to binary (0/1)
        target_series = normalized_dataset[self.target_column]

        # Convert target variable to 0 and 1
        factorized_labels, unique_values = pd.factorize(target_series)
        self.target_map = {unique_values[i]: i for i in range(len(unique_values))}

        features = normalized_dataset[self.feature_columns]
        labels = factorized_labels

        # Using sklearn's train_test_split for simplicity
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=self.random_state
        )
        
        return {
            "train_features": X_train,
            "train_labels": y_train,
            "test_features": X_test,
            "test_labels": y_test,
        }

    def run_experiment(self) -> dict:
        processed_data = self.preprocess_data()
        split_data = self.split_data(processed_data)

        # Use Scikit-learn's Logistic Regression, configured for multiclass
        model = LogisticRegression(random_state=self.random_state, solver='lbfgs', max_iter=1000)
        
        # Train the model
        model.fit(split_data["train_features"], split_data["train_labels"])

        # Make predictions and calculate accuracy
        y_pred = model.predict(split_data["test_features"])
        test_accuracy = accuracy_score(split_data["test_labels"], y_pred)

        return {
            "test_accuracy": test_accuracy,
            "target_map": self.target_map,
            "feature_columns": self.feature_columns
        }