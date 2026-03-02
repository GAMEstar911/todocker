import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer

class LogisticsRunner:
    def __init__(self, data: pd.DataFrame, random_state: int = 100):
        # Enforce a row limit to prevent memory issues
        if len(data) > 50000:
            data = data.head(50000)
            
        self.data = data
        self.random_state = random_state
        self.target_column = data.columns[-1]
        self.feature_columns = [col for col in data.columns[:-1] if pd.api.types.is_numeric_dtype(data[col])]

    def preprocess_data(self) -> pd.DataFrame:
        # Keep only feature columns and the target column
        self.data = self.data[self.feature_columns + [self.target_column]]

        # Impute missing values for numeric features
        if self.data[self.feature_columns].isnull().any().any():
            imputer = SimpleImputer(strategy='mean')
            self.data[self.feature_columns] = imputer.fit_transform(self.data[self.feature_columns])

        if self.data.isnull().any().any():
            raise ValueError("Dataset contains missing values in the target column. Please clean the data before uploading.")

        return self.data

    def split_data(self, dataset: pd.DataFrame) -> dict:
        # Normalize numerical features
        numerical_features = self.feature_columns
        feature_mean = dataset[numerical_features].mean()
        feature_std = dataset[numerical_features].std()
        normalized_dataset = dataset.copy()
        normalized_dataset[numerical_features] = (dataset[numerical_features] - feature_mean) / feature_std
        
        # Convert target column
        target_series = normalized_dataset[self.target_column]

        # Check if the target variable looks like a regression problem
        if target_series.nunique() / len(target_series) > 0.5:
            raise ValueError(f"The target column '{self.target_column}' has too many unique values and appears to be a regression problem, not a classification problem. This tool is for classification tasks only.")

        # Convert target variable to numerical classes
        factorized_labels, unique_values = pd.factorize(target_series)
        self.class_labels = list(unique_values)

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

        # Generate the confusion matrix
        cm = confusion_matrix(split_data["test_labels"], y_pred)

        return {
            "test_accuracy": test_accuracy,
            "feature_columns": self.feature_columns,
            "confusion_matrix": cm.tolist(),
            "class_labels": self.class_labels
        }