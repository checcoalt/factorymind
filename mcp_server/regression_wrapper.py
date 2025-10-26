import numpy as np
import joblib
from typing import List, Union

class RegressionModel:
    """
    Wrapper per il tuo script di regressione esistente.
    Adatta questo codice al tuo modello specifico.
    """
    
    def __init__(self, model_path: str = "models/regression_model.pkl"):
        self.model_path = model_path
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Carica il modello salvato"""
        try:
            self.model = joblib.load(self.model_path)
            print(f"✓ Modello di regressione caricato da {self.model_path}")
        except FileNotFoundError:
            print(f"⚠ Modello non trovato in {self.model_path}, verrà creato un modello dummy")
            # Puoi inizializzare un modello vuoto o addestrarne uno nuovo
            self.model = None
    
    def predict(self, features: Union[List[float], np.ndarray]) -> Union[float, List[float]]:
        """
        Esegue una predizione
        
        Args:
            features: Feature per la predizione (array o lista)
        
        Returns:
            Predizione o lista di predizioni
        """
        if self.model is None:
            raise ValueError("Modello non caricato. Addestra o carica un modello prima di predire.")
        
        # Converti in array numpy se necessario
        X = np.array(features).reshape(1, -1) if isinstance(features, list) else features
        
        # Esegui la predizione
        prediction = self.model.predict(X)
        
        return float(prediction[0]) if len(prediction) == 1 else prediction.tolist()
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """
        Addestra il modello (inserisci qui la tua logica di training)
        
        Args:
            X_train: Feature di training
            y_train: Target di training
        """
        # Importa qui il tuo script di regressione esistente
        # from your_regression_script import train_model
        # self.model = train_model(X_train, y_train)
        
        pass
    
    def save_model(self, path: str = None):
        """Salva il modello"""
        save_path = path or self.model_path
        joblib.dump(self.model, save_path)
        print(f"✓ Modello salvato in {save_path}")
    
    def get_feature_importance(self) -> dict:
        """Restituisce l'importanza delle feature se disponibile"""
        if hasattr(self.model, 'feature_importances_'):
            return {
                f"feature_{i}": float(imp) 
                for i, imp in enumerate(self.model.feature_importances_)
            }
        return {}