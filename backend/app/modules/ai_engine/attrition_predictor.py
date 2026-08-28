"""
NexusTalent AI Attrition & Flight Risk Predictor
Trained Scikit-Learn Machine Learning Classifier predicting Employee Flight Risk Probability.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


class AttritionPredictorModel:
    """
    Supervised Machine Learning Model predicting employee flight risk based on:
    1. Salary ratio relative to market benchmark
    2. Overtime hours per month
    3. Years at company
    4. Years since last promotion
    5. Performance rating
    6. Remote status
    """

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        self.scaler = StandardScaler()
        self._train_synthetic_baseline()

    def _train_synthetic_baseline(self):
        # Generate synthetic realistic training corpus (500 synthetic employee samples)
        np.random.seed(42)
        n_samples = 500

        # Features: [salary_ratio, overtime_hrs, tenure_yrs, yrs_since_promotion, perf_score, is_remote]
        salary_ratio = np.random.uniform(0.7, 1.4, n_samples)
        overtime_hrs = np.random.uniform(0, 45, n_samples)
        tenure_yrs = np.random.uniform(0.5, 8.0, n_samples)
        yrs_since_promo = np.random.uniform(0, 5.0, n_samples)
        perf_score = np.random.uniform(1.0, 3.0, n_samples)
        is_remote = np.random.choice([0, 1], n_samples)

        X = np.column_stack([salary_ratio, overtime_hrs, tenure_yrs, yrs_since_promo, perf_score, is_remote])
        
        # Synthetic probabilistic ground truth: low salary + high overtime + high time without promotion -> higher risk
        risk_score = (
            (1.5 - salary_ratio) * 0.35 +
            (overtime_hrs / 40.0) * 0.30 +
            (yrs_since_promo / 4.0) * 0.25 -
            (perf_score / 3.0) * 0.10
        )
        y = (risk_score > 0.45).astype(int)

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

    def predict_employee_risk(
        self,
        salary_ratio: float,
        overtime_hours_month: float,
        tenure_years: float,
        years_since_last_promotion: float,
        performance_score: float,
        is_remote: bool
    ) -> Dict[str, Any]:
        features = np.array([[
            salary_ratio,
            overtime_hours_month,
            tenure_years,
            years_since_last_promotion,
            performance_score,
            1 if is_remote else 0
        ]])
        
        features_scaled = self.scaler.transform(features)
        prob = self.model.predict_proba(features_scaled)[0][1]
        risk_percentage = round(float(prob) * 100.0, 1)

        if risk_percentage >= 70:
            level = "Critical / High Risk"
            recommendations = [
                "Immediate 1-on-1 retention check-in with executive leadership",
                "Review compensation against latest market benchmark",
                "Reduce overtime load & re-balance project allocation"
            ]
        elif risk_percentage >= 40:
            level = "Moderate Risk"
            recommendations = [
                "Schedule career development & promotion trajectory discussion",
                "Check job satisfaction and peer dynamics"
            ]
        else:
            level = "Low Risk / Stable"
            recommendations = [
                "Employee is highly engaged and well-aligned with retention metrics."
            ]

        return {
            "flight_risk_percentage": risk_percentage,
            "risk_level": level,
            "key_drivers": {
                "salary_ratio": salary_ratio,
                "overtime_hours_month": overtime_hours_month,
                "tenure_years": tenure_years,
                "years_since_last_promotion": years_since_last_promotion
            },
            "retention_recommendations": recommendations
        }


# Singleton model instance
attrition_ai_model = AttritionPredictorModel()
