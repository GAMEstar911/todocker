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

        # Validate the target column for binary classification
        if target_series.nunique() != 2:
            raise ValueError(f"The target column '{self.target_column}' is not suitable for logistic regression. It must have exactly 2 unique classes, but it has {target_series.nunique()}. Please use a dataset with a binary target variable (e.g., Yes/No, 0/1).")

        # Convert target variable to 0 and 1
        factorized_labels, unique_values = pd.factorize(target_series)
        self.target_map = {unique_values[i]: i for i in range(len(unique_values))}

        features = normalized_dataset[self.feature_columns]
        labels = factorized_labels

        # Using sklearn's train_test_split for simplicity
        X_train_full, X_test, y_train_full, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=self.random_state
        )
        
        # Split the training data into a smaller training set and a validation set
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_full, y_train_full, test_size=0.25, random_state=self.random_state
        )

        return {
            "train_features": X_train,
            "train_labels": y_train,
            "val_features": X_val,
            "val_labels": y_val,
            "test_features": X_test,
            "test_labels": y_test,
        }

    def run_experiment(self) -> dict:
        processed_data = self.preprocess_data()
        split_data = self.split_data(processed_data)

        # Use Scikit-learn's Logistic Regression with warm_start to simulate epochs
        model = LogisticRegression(random_state=self.random_state, warm_start=True, solver='liblinear', max_iter=1)
        
        training_accuracy = []
        validation_accuracy = []
        n_epochs = 30  # Number of training epochs

        for _ in range(n_epochs):
            model.fit(split_data["train_features"], split_data["train_labels"])
            
            # Calculate training accuracy
            train_pred = model.predict(split_data["train_features"])
            train_acc = accuracy_score(split_data["train_labels"], train_pred)
            training_accuracy.append(train_acc)
            
            # Calculate validation accuracy
            val_pred = model.predict(split_data["val_features"])
            val_acc = accuracy_score(split_data["val_labels"], val_pred)
            validation_accuracy.append(val_acc)

        # Final test accuracy after all epochs
        y_pred = model.predict(split_data["test_features"])
        test_accuracy = accuracy_score(split_data["test_labels"], y_pred)

        return {
            "test_accuracy": test_accuracy,
            "target_map": self.target_map,
            "feature_columns": self.feature_columns,
            "training_history": {
                "accuracy": training_accuracy,
                "val_accuracy": validation_accuracy
            }
        }