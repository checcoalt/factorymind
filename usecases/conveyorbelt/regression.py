import pandas as pd
import json
from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import joblib


class ConveyorBeltRegression:
    """
    A class for building and evaluating a regression model for conveyor belt 
    predictive maintenance, using data from MongoDB.

    The model predicts future Power Consumption (kW) based on current machine health metrics.
    A significant difference between predicted and actual consumption (residual)
    indicates a potential failure (e.g., increased friction due to a blocked roller).
    """

    def __init__(self, mongo_uri, db_name, collection_name):
        """
        Initializes the model with MongoDB connection details.

        :param mongo_uri: The connection string for MongoDB (e.g., 'mongodb://localhost:27017/').
        :param db_name: The name of the database (e.g., 'conveyor_data').
        :param collection_name: The name of the collection containing sensor data (e.g., 'sensor_readings').
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.data = None
        self.model = None
        self.scaler = StandardScaler()

    def connect_and_fetch_data(self, query=None):
        """
        Establishes connection to MongoDB and fetches all relevant data.
        
        :param query: Optional MongoDB query to filter data (default: None for all data).
        :return: True if data fetching was successful, False otherwise.
        """
        try:
            self.client = MongoClient(self.mongo_uri)
            db = self.client[self.db_name]
            collection = db[self.collection_name]
            
            # Fetch all documents based on the query
            cursor = collection.find(query if query is not None else {})
            
            # Convert MongoDB cursor to a Pandas DataFrame
            self.data = pd.DataFrame(list(cursor))
            
            # Drop the MongoDB document ID
            if '_id' in self.data.columns:
                self.data = self.data.drop(columns=['_id'])
            
            print(f"Successfully fetched {len(self.data)} records from MongoDB.")
            return True
        except Exception as e:
            print(f"Error fetching data from MongoDB: {e}")
            return False

    def load_training_data_from_json(self, json_path):
        """
        Loads training data from a JSON file instead of MongoDB.
        
        :param json_path: Path to the JSON file containing training data.
        :return: True if data loading was successful, False otherwise.
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            self.data = pd.DataFrame(data)
            
            # Drop the MongoDB document ID if present
            if '_id' in self.data.columns:
                self.data = self.data.drop(columns=['_id'])
            
            print(f"Successfully loaded {len(self.data)} records from {json_path}.")
            return True
        except Exception as e:
            print(f"Error loading data from JSON: {e}")
            return False

    def preprocess_data(self, features, target):
        """
        Prepares the data for training: handling missing values, scaling, and splitting.

        :param features: List of column names to be used as input features (X).
        :param target: Name of the column to be predicted (y).
        """
        if self.data is None or self.data.empty:
            print("Error: No data loaded. Run connect_and_fetch_data or load_training_data_from_json first.")
            return False

        # Ensure all necessary columns are present and numeric
        required_cols = features + [target]
        for col in required_cols:
            if col not in self.data.columns:
                 raise ValueError(f"Missing required column: {col}")
            self.data[col] = pd.to_numeric(self.data[col], errors='coerce')

        # Simple handling of missing values (e.g., dropping rows with NaNs)
        self.data.dropna(subset=required_cols, inplace=True)
        print(f"Data remaining after cleaning: {len(self.data)} records.")

        # Separate features (X) and target (y)
        X = self.data[features]
        y = self.data[target]

        # Scale the features
        X_scaled = self.scaler.fit_transform(X)

        # Split the data into training and testing sets
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        print("Data preprocessed and split successfully.")
        return True

    def train_model(self):
        """
        Trains the Linear Regression model using the training data.
        """
        if not hasattr(self, 'X_train'):
            print("Error: Data not preprocessed. Run preprocess_data first.")
            return False

        print("Starting model training (Linear Regression)...")
        # Initialize the regression model
        self.model = LinearRegression()
        
        # Train the model
        self.model.fit(self.X_train, self.y_train)
        print("Model training complete.")
        return True

    def evaluate_model(self):
        """
        Evaluates the model's performance on the test set.
        
        :return: Dictionary with MSE and R2 score, or None if model not trained.
        """
        if self.model is None:
            print("Error: Model not trained. Run train_model first.")
            return None

        # Make predictions on the test set
        y_pred = self.model.predict(self.X_test)

        # Calculate evaluation metrics
        mse = mean_squared_error(self.y_test, y_pred)
        r2 = r2_score(self.y_test, y_pred)

        print("\n--- Model Evaluation ---")
        print(f"Mean Squared Error (MSE): {mse:.4f}")
        print(f"R-squared (R2 Score): {r2:.4f} (Closer to 1 is better)")
        print("------------------------")
        
        return {"mse": float(mse), "r2": float(r2)}

    def save_artifacts(self, model_path="model.joblib", scaler_path="scaler.joblib"):
        """
        Saves the trained model and the scaler object to disk.
        
        :param model_path: Path where to save the model.
        :param scaler_path: Path where to save the scaler.
        """
        if self.model is not None:
            joblib.dump(self.model, model_path)
            joblib.dump(self.scaler, scaler_path)
            print(f"Model saved to {model_path}")
            print(f"Scaler saved to {scaler_path}")

    def load_artifacts(self, model_path="model.joblib", scaler_path="scaler.joblib"):
        """
        Loads the trained model and scaler from disk.
        
        :param model_path: Path to the saved model.
        :param scaler_path: Path to the saved scaler.
        :return: True if successful, False otherwise.
        """
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            print("Model and scaler loaded successfully.")
            return True
        except Exception as e:
            print(f"Error loading model artifacts: {e}")
            return False

    def predict_anomaly(self, new_data_point, features):
        """
        Predicts the expected power consumption for a new data point and checks for anomalies.

        :param new_data_point: A dictionary containing the current sensor readings.
                                E.g., {'Vibration': 1.2, 'Temperature': 35.5, 'Speed': 1.5}
        :param features: List of features used for training.
        :return: Dictionary with prediction results and anomaly status.
        """
        if self.model is None or self.scaler is None:
            raise Exception("Model or Scaler not loaded/trained.")

        # Convert the new data point into a DataFrame
        new_df = pd.DataFrame([new_data_point])
        
        # Ensure the columns are in the correct order for scaling
        X_new = new_df[features]
        
        # Scale the new features using the fitted scaler
        X_new_scaled = self.scaler.transform(X_new)
        
        # Predict the target (Power Consumption)
        predicted_power = self.model.predict(X_new_scaled)[0]
        
        # Assuming the actual power consumption is also passed in the dict for residual check
        actual_power = new_data_point.get('PowerConsumption') 
        residual = None
        anomaly_detected = False
        
        if actual_power is not None:
            residual = actual_power - predicted_power
            print(f"\n--- Anomaly Check ---")
            print(f"Actual Power: {actual_power:.2f} kW")
            print(f"Predicted Power: {predicted_power:.2f} kW")
            print(f"Residual (Anomaly Score): {residual:.2f} kW")
            
            # Simple Anomaly Detection: If residual is significantly positive
            if residual > 0.5:  # Example threshold (should be set based on statistical analysis)
                print("ALERT: High positive residual detected! Potential high friction/blockage in the system.")
                anomaly_detected = True

        return {
            "predicted_power": float(predicted_power),
            "actual_power": float(actual_power) if actual_power is not None else None,
            "residual": float(residual) if residual is not None else None,
            "anomaly_detected": anomaly_detected
        }

    def get_mongodb_record_count(self):
        """
        Returns the number of records in the MongoDB collection.
        
        :return: Number of documents in the collection.
        """
        try:
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            collection = db[self.collection_name]
            
            count = collection.count_documents({})
            client.close()
            
            return count
        except Exception as e:
            print(f"Error counting documents: {e}")
            return None


# Standalone execution example
if __name__ == '__main__':
    
    # 1. Configuration
    MONGO_URI = 'mongodb://mongodb:27017/' 
    DB_NAME = 'conveyor_data_40'
    COLLECTION_NAME = 'health_metrics'
    
    FEATURES = ['Vibration', 'Temperature', 'Speed']
    TARGET = 'PowerConsumption'

    # 2. Initialize and train
    predictor = ConveyorBeltRegression(MONGO_URI, DB_NAME, COLLECTION_NAME)

    # Load training data from JSON
    if predictor.load_training_data_from_json('training_data.json'):
        if predictor.preprocess_data(FEATURES, TARGET):
            predictor.train_model()
            predictor.evaluate_model()
            predictor.save_artifacts()

            # 3. Example predictions
            normal_reading = {
                'Vibration': 0.8, 
                'Temperature': 30.0, 
                'Speed': 1.5, 
                'PowerConsumption': 2.0
            }
            print("\n--- Test 1: Normal Reading ---")
            result = predictor.predict_anomaly(normal_reading, FEATURES)
            print(f"Result: {result}")

            anomaly_reading = {
                'Vibration': 1.2, 
                'Temperature': 35.5, 
                'Speed': 1.5, 
                'PowerConsumption': 4.0 
            }
            print("\n--- Test 2: Potential Failure (High Friction) ---")
            result = predictor.predict_anomaly(anomaly_reading, FEATURES)
            print(f"Result: {result}")