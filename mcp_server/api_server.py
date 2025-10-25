"""
REST API Wrapper per il Conveyor Belt MCP Server.
Espone gli strumenti MCP tramite endpoint HTTP REST.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import sys

# Add usecases/conveyorbelt to path for importing regression module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'usecases', 'conveyorbelt'))

from regression import ConveyorBeltRegression

app = FastAPI(
    title="Conveyor Belt Predictive Maintenance API",
    description="REST API for conveyor belt anomaly detection",
    version="1.0.0"
)

# Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/')
DB_NAME = os.getenv('DB_NAME', 'conveyor_data_40')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'health_metrics')
TRAINING_DATA_PATH = os.getenv('TRAINING_DATA_PATH', '/app/usecases/conveyorbelt/training_data.json')
MODEL_PATH = os.getenv('MODEL_PATH', '/app/models/model.joblib')
SCALER_PATH = os.getenv('SCALER_PATH', '/app/models/scaler.joblib')

FEATURES = ['Vibration', 'Temperature', 'Speed']
TARGET = 'PowerConsumption'

# Global predictor
predictor = None


# Pydantic models
class SensorReading(BaseModel):
    vibration: float
    temperature: float
    speed: float
    actual_power: Optional[float] = None


class BatchReadings(BaseModel):
    readings: List[dict]


class PredictionResponse(BaseModel):
    predicted_power: float
    actual_power: Optional[float]
    residual: Optional[float]
    anomaly_detected: bool


class MetricsResponse(BaseModel):
    mse: float
    r2: float


class CountResponse(BaseModel):
    record_count: int


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the model on startup."""
    global predictor
    
    print("Initializing predictor...")
    predictor = ConveyorBeltRegression(MONGO_URI, DB_NAME, COLLECTION_NAME)
    
    if predictor.load_training_data_from_json(TRAINING_DATA_PATH):
        if predictor.preprocess_data(FEATURES, TARGET):
            if predictor.train_model():
                predictor.evaluate_model()
                predictor.save_artifacts(MODEL_PATH, SCALER_PATH)
                print("✓ Model initialized successfully")
                return
    
    print("✗ Failed to initialize model")
    raise Exception("Model initialization failed")


# Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Conveyor Belt Predictive Maintenance API",
        "version": "1.0.0",
        "endpoints": {
            "POST /predict": "Predict power consumption for a single reading",
            "POST /predict/batch": "Predict for multiple readings",
            "GET /metrics": "Get model performance metrics",
            "GET /data/count": "Get MongoDB record count",
            "POST /model/reload": "Reload model from disk"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if predictor is None or predictor.model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(reading: SensorReading):
    """
    Predict power consumption and detect anomalies for a single reading.
    
    Example:
    ```json
    {
        "vibration": 0.8,
        "temperature": 30.0,
        "speed": 1.5,
        "actual_power": 2.0
    }
    ```
    """
    if predictor is None or predictor.model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")
    
    data = {
        'Vibration': reading.vibration,
        'Temperature': reading.temperature,
        'Speed': reading.speed
    }
    
    if reading.actual_power is not None:
        data['PowerConsumption'] = reading.actual_power
    
    try:
        result = predictor.predict_anomaly(data, FEATURES)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch")
async def predict_batch(batch: BatchReadings):
    """
    Check multiple readings for anomalies.
    
    Example:
    ```json
    {
        "readings": [
            {"Vibration": 0.8, "Temperature": 30.0, "Speed": 1.5, "PowerConsumption": 2.0},
            {"Vibration": 1.2, "Temperature": 35.5, "Speed": 1.5, "PowerConsumption": 4.0}
        ]
    }
    ```
    """
    if predictor is None or predictor.model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")
    
    try:
        results = []
        anomaly_count = 0
        
        for idx, reading in enumerate(batch.readings):
            result = predictor.predict_anomaly(reading, FEATURES)
            result['reading_index'] = idx
            results.append(result)
            
            if result.get('anomaly_detected', False):
                anomaly_count += 1
        
        return {
            'total_readings': len(batch.readings),
            'anomalies_detected': anomaly_count,
            'anomaly_rate': anomaly_count / len(batch.readings) if batch.readings else 0,
            'results': results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get model performance metrics (MSE and R2 score)."""
    if predictor is None or predictor.model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")
    
    try:
        metrics = predictor.evaluate_model()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/count", response_model=CountResponse)
async def get_data_count():
    """Get the number of records in MongoDB."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        count = predictor.get_mongodb_record_count()
        if count is not None:
            return {"record_count": count}
        else:
            raise HTTPException(status_code=500, detail="Failed to count records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/model/reload")
async def reload_model():
    """Reload the model from disk."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        if predictor.load_artifacts(MODEL_PATH, SCALER_PATH):
            return {"success": True, "message": "Model reloaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reload model")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)