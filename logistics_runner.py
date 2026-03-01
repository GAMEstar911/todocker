import pandas as pd
import numpy as np
import keras
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
        # Assumes the target column has two unique values
        unique_values = normalized_dataset[self.target_column].unique()
        if len(unique_values) != 2:
            raise ValueError(f"The target column '{self.target_column}' must have exactly two unique classes for logistic regression, but it has {len(unique_values)}.")
        
        # Automatically assign the first unique value to 0 and the second to 1
        self.target_map = {unique_values[0]: 0, unique_values[1]: 1}
        normalized_dataset['target_binary'] = normalized_dataset[self.target_column].map(self.target_map)

        features = normalized_dataset[self.feature_columns]
        labels = normalized_dataset["target_binary"]

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

    @staticmethod
    def create_model(input_features: list[str], learning_rate: float) -> keras.Model:
        model_inputs = [
            keras.Input(name=feature_name, shape=(1,))
            for feature_name in input_features
        ]
        concatenated_inputs = keras.layers.Concatenate()(model_inputs)
        model_output = keras.layers.Dense(
            units=1,
            name="dense_layer",
            activation=keras.activations.sigmoid,
        )(concatenated_inputs)

        model = keras.Model(inputs=model_inputs, outputs=model_output)
        model.compile(
            optimizer=keras.optimizers.RMSprop(learning_rate),
            loss=keras.losses.BinaryCrossentropy(),
            metrics=['accuracy'],
        )
        return model

    def run_experiment(self) -> dict:
        processed_data = self.preprocess_data()
        split_data = self.split_data(processed_data)

        # These settings can be exposed to the user in the future
        learning_rate=0.001
        number_epochs=60
        batch_size=100

        model = self.create_model(self.feature_columns, learning_rate)

        train_features_dict = {col: np.array(split_data["train_features"][col]) for col in self.feature_columns}

        history = model.fit(
            x=train_features_dict,
            y=split_data["train_labels"],
            batch_size=batch_size,
            epochs=number_epochs,
            validation_split=0.2, # Using a portion of training data for validation
            verbose=0 # Suppress verbose output
        )

        test_features_dict = {col: np.array(split_data["test_features"][col]) for col in self.feature_columns}
        
        test_loss, test_accuracy = model.evaluate(
            test_features_dict,
            split_data["test_labels"],
            verbose=0
        )

        return {
            "test_accuracy": test_accuracy,
            "training_history": history.history,
            "target_map": self.target_map,
            "feature_columns": self.feature_columns
        }