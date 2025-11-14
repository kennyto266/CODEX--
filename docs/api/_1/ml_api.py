"""
ML 服務 FastAPI 端點
提供模型訓練、預測和管理的 REST API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
import logging

# Import ML services
from src.ml.services.model_trainer import ModelTrainer
from src.ml.services.prediction_service import PredictionService
from src.ml.services.model_manager import ModelManager
from src.ml.services.hyperparameter_optimizer import HyperparameterOptimizer
from src.ml.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="BMAD ML Services API",
    description="Machine Learning Services for BMAD Quantitative Trading System",
    version="1.0.0"
)

# 全局變量存儲服務實例
services = {
    'trainers': {},
    'predictors': {},
    'managers': {},
    'optimizers': {},
    'registries': {}
}

# Pydantic 模塊定義
class ModelTrainingRequest(BaseModel):
    model_type: str = Field(..., description="模型類型")
    task_type: str = Field(default="regression", description="任務類型")
    experiment_name: Optional[str] = Field(None, description="實驗名稱")
    parallel: bool = Field(default=True, description="是否並行訓練")
    n_jobs: int = Field(default=-1, description="並行作業數")


class DataRequest(BaseModel):
    data: Union[List[Dict], Dict] = Field(..., description="輸入數據")
    columns: Optional[List[str]] = Field(None, description="列名")


class PredictionRequest(BaseModel):
    model_id: str = Field(..., description="模型ID")
    data: Union[List[Dict], Dict] = Field(..., description="預測數據")
    return_probability: bool = Field(default=False, description="是否返回概率")
    return_confidence: bool = Field(default=False, description="是否返回置信度")


class TradingSignalRequest(BaseModel):
    model_id: str = Field(..., description="模型ID")
    data: Union[List[Dict], Dict] = Field(..., description="輸入數據")
    price_column: str = Field(default="price", description="價格列名")
    signal_threshold: float = Field(default=0.02, description="信號閾值")
    prediction_horizon: int = Field(default=1, description="預測步長")


class HyperparameterOptimizationRequest(BaseModel):
    model_type: str = Field(..., description="模型類型")
    param_space: Dict[str, Any] = Field(..., description="參數空間")
    n_trials: int = Field(default=100, description="試驗次數")
    optimization_method: str = Field(default="bayesian", description="優化方法")


class ModelInfoResponse(BaseModel):
    model_id: str
    name: str
    version: str
    model_type: str
    task_type: str
    status: str
    performance_metrics: Dict[str, float]
    created_at: str


# API 路由
@app.get("/")
async def root():
    """API 根路徑"""
    return {
        "message": "BMAD ML Services API",
        "version": "1.0.0",
        "docs": "/docs",
        "services": {
            "model_training": "/train",
            "model_prediction": "/predict",
            "model_management": "/models",
            "hyperparameter_optimization": "/optimize",
            "trading_signals": "/signals",
            "model_registry": "/registry"
        }
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "available_models": list(services['managers'].keys()) if services['managers'] else []
        }
    }


# 模型訓練端點
@app.post("/train")
async def train_model(request: ModelTrainingRequest):
    """訓練模型"""
    try:
        # 創建訓練器
        trainer_id = f"trainer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        trainer = ModelTrainer(
            task_type=request.task_type,
            experiment_name=request.experiment_name or trainer_id
        )

        services['trainers'][trainer_id] = trainer

        return {
            "trainer_id": trainer_id,
            "status": "created",
            "message": "Model trainer created successfully"
        }

    except Exception as e:
        logger.error(f"Model training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train/{trainer_id}/models")
async def train_models(
    trainer_id: str,
    model_types: List[str],
    X_train: List[Dict],
    y_train: List[Union[float, int]],
    X_test: Optional[List[Dict]] = None,
    y_test: Optional[List[Union[float, int]]] = None
):
    """訓練多個模型"""
    try:
        if trainer_id not in services['trainers']:
            raise HTTPException(status_code=404, detail=f"Trainer {trainer_id} not found")

        trainer = services['trainers'][trainer_id]

        # 轉換數據格式
        X_train_df = pd.DataFrame(X_train)
        y_train_series = pd.Series(y_train)

        X_test_df = pd.DataFrame(X_test) if X_test else None
        y_test_series = pd.Series(y_test) if y_test else None

        # 訓練模型
        results = trainer.train_multiple_models(
            model_types=model_types,
            X_train=X_train_df,
            y_train=y_train_series,
            X_test=X_test_df,
            y_test=y_test_series,
            parallel=True
        )

        return {
            "trainer_id": trainer_id,
            "results": {
                k: {key: value for key, value in v.items() if key != 'model'}
                for k, v in results.items()
            },
            "message": f"Successfully trained {len([r for r in results.values() if 'error' not in r])} models"
        }

    except Exception as e:
        logger.error(f"Multi-model training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 模型管理端點
@app.get("/models")
async def list_models():
    """列出所有模型"""
    try:
        if not services['managers']:
            return {"models": [], "message": "No model managers available"}

        all_models = []
        for manager_id, manager in services['managers'].items():
            models = manager.list_models()
            for model in models:
                all_models.append(model)

        return {
            "models": all_models,
            "total": len(all_models)
        }

    except Exception as e:
        logger.error(f"List models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/{model_id}")
async def get_model(model_id: str):
    """獲取模型信息"""
    try:
        for manager in services['managers'].values():
            model_info = manager.get_model(model_id)
            if model_info:
                return {"model": model_info}

        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get model error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/models/{model_id}")
async def delete_model(model_id: str, version: Optional[str] = None):
    """刪除模型"""
    try:
        for manager in services['managers'].values():
            try:
                manager.delete_model(model_id, version)
                return {"message": f"Model {model_id} deleted successfully"}
            except ValueError:
                continue

        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete model error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 模型註冊端點
@app.post("/register")
async def register_model(
    name: str,
    model_type: str,
    task_type: str,
    model_data: Dict[str, Any]
):
    """註冊模型"""
    try:
        # 創建模型管理器（如果不存在）
        manager_id = "default_manager"
        if manager_id not in services['managers']:
            services['managers'][manager_id] = ModelManager()

        manager = services['managers'][manager_id]

        # 註冊模型
        model_id = manager.register_model(
            model=model_data['model'],
            name=name,
            model_type=model_type,
            task_type=task_type,
            performance_metrics=model_data.get('performance_metrics', {}),
            hyperparameters=model_data.get('hyperparameters', {}),
            description=model_data.get('description', ''),
            tags=model_data.get('tags', [])
        )

        return {
            "model_id": model_id,
            "message": "Model registered successfully"
        }

    except Exception as e:
        logger.error(f"Register model error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 預測端點
@app.post("/predict")
async def predict(request: PredictionRequest):
    """執行預測"""
    try:
        # 查找模型
        model = None
        model_info = None
        for manager in services['managers'].values():
            try:
                model, model_info = manager.load_model(request.model_id)
                break
            except ValueError:
                continue

        if model is None:
            raise HTTPException(status_code=404, detail=f"Model {request.model_id} not found")

        # 創建預測服務
        predictor = PredictionService()
        predictor.model_ = model
        predictor.model_metadata_ = model_info

        # 轉換數據格式
        if isinstance(request.data, dict):
            data = pd.DataFrame([request.data])
        else:
            data = pd.DataFrame(request.data)

        # 執行預測
        result = predictor.predict(
            data=data,
            return_probability=request.return_probability,
            return_confidence=request.return_confidence
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch")
async def batch_predict(
    model_id: str,
    data: List[Dict],
    batch_size: int = 1000
):
    """批量預測"""
    try:
        # 查找模型
        model = None
        model_info = None
        for manager in services['managers'].values():
            try:
                model, model_info = manager.load_model(model_id)
                break
            except ValueError:
                continue

        if model is None:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        # 創建預測服務
        predictor = PredictionService()
        predictor.model_ = model
        predictor.model_metadata_ = model_info

        # 執行批量預測
        data_df = pd.DataFrame(data)
        result = predictor.batch_predict(
            data=data_df,
            batch_size=batch_size
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 交易信號端點
@app.post("/signals")
async def generate_trading_signals(request: TradingSignalRequest):
    """生成交易信號"""
    try:
        # 查找模型
        model = None
        model_info = None
        for manager in services['managers'].values():
            try:
                model, model_info = manager.load_model(request.model_id)
                break
            except ValueError:
                continue

        if model is None:
            raise HTTPException(status_code=404, detail=f"Model {request.model_id} not found")

        # 創建預測服務
        predictor = PredictionService()
        predictor.model_ = model
        predictor.model_metadata_ = model_info

        # 轉換數據格式
        if isinstance(request.data, dict):
            data = pd.DataFrame([request.data])
        else:
            data = pd.DataFrame(request.data)

        # 生成交易信號
        result = predictor.generate_trading_signals(
            data=data,
            price_column=request.price_column,
            signal_threshold=request.signal_threshold,
            prediction_horizon=request.prediction_horizon
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trading signals error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 超參數優化端點
@app.post("/optimize")
async def optimize_hyperparameters(request: HyperparameterOptimizationRequest):
    """超參數優化"""
    try:
        # 創建優化器
        optimizer_id = f"optimizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        optimizer = HyperparameterOptimizer(task_type="regression")

        services['optimizers'][optimizer_id] = optimizer

        return {
            "optimizer_id": optimizer_id,
            "status": "created",
            "message": "Hyperparameter optimizer created",
            "note": "Data must be provided separately to run optimization"
        }

    except Exception as e:
        logger.error(f"Hyperparameter optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize/{optimizer_id}/run")
async def run_optimization(
    optimizer_id: str,
    model_type: str,
    param_space: Dict[str, Any],
    X_train: List[Dict],
    y_train: List[Union[float, int]],
    n_trials: int = 100
):
    """執行超參數優化"""
    try:
        if optimizer_id not in services['optimizers']:
            raise HTTPException(status_code=404, detail=f"Optimizer {optimizer_id} not found")

        optimizer = services['optimizers'][optimizer_id]

        # 轉換數據格式
        X_train_df = pd.DataFrame(X_train)
        y_train_series = pd.Series(y_train)

        # 執行優化
        result = optimizer.optimize_bayesian(
            model_class=lambda **kwargs: type('TempModel', (), {
                '__init__': lambda self, **kw: None,
                'fit': lambda self, X, y: None,
                'predict': lambda self, X: np.zeros(len(X))
            }),
            param_space=param_space,
            X_train=X_train_df,
            y_train=y_train_series,
            n_trials=n_trials
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Run optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 模型對比端點
@app.get("/compare")
async def compare_models(model_ids: str):
    """對比模型"""
    try:
        ids = model_ids.split(',')
        model_comparisons = []

        for manager in services['managers'].values():
            comparison_df = manager.compare_models(ids)
            if not comparison_df.empty:
                model_comparisons = comparison_df.to_dict('records')
                break

        return {
            "comparison": model_comparisons,
            "total_models": len(model_comparisons)
        }

    except Exception as e:
        logger.error(f"Compare models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 模型統計端點
@app.get("/statistics")
async def get_statistics():
    """獲取模型統計"""
    try:
        stats = {}
        for manager_id, manager in services['managers'].items():
            stats[manager_id] = manager.get_model_statistics()

        return {
            "statistics": stats,
            "total_managers": len(services['managers'])
        }

    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 實驗管理端點
@app.post("/experiments")
async def create_experiment(
    name: str,
    description: str = "",
    created_by: str = "api_user"
):
    """創建實驗"""
    try:
        # 創建模型註冊表（如果不存在）
        registry_id = "default_registry"
        if registry_id not in services['registries']:
            services['registries'][registry_id] = ModelRegistry()

        registry = services['registries'][registry_id]

        experiment_id = registry.create_experiment(
            name=name,
            description=description,
            created_by=created_by
        )

        return {
            "experiment_id": experiment_id,
            "message": "Experiment created successfully"
        }

    except Exception as e:
        logger.error(f"Create experiment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/experiments")
async def list_experiments():
    """列出實驗"""
    try:
        experiments = []
        for registry in services['registries'].values():
            exp_list = registry.list_experiments()
            experiments.extend([
                {
                    "experiment_id": exp.experiment_id,
                    "name": exp.name,
                    "description": exp.description,
                    "created_at": exp.created_at,
                    "created_by": exp.created_by,
                    "status": exp.status
                }
                for exp in exp_list
            ])
            break

        return {
            "experiments": experiments,
            "total": len(experiments)
        }

    except Exception as e:
        logger.error(f"List experiments error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 導出/導入端點
@app.post("/export")
async def export_models(manager_id: str, filepath: str):
    """導出模型註冊表"""
    try:
        if manager_id not in services['managers']:
            raise HTTPException(status_code=404, detail=f"Manager {manager_id} not found")

        manager = services['managers'][manager_id]
        manager.export_registry(filepath)

        return {
            "message": "Models exported successfully",
            "filepath": filepath
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/import")
async def import_models(
    manager_id: str,
    filepath: str,
    merge: bool = True
):
    """導入模型註冊表"""
    try:
        # 創建模型管理器（如果不存在）
        if manager_id not in services['managers']:
            services['managers'][manager_id] = ModelManager()

        manager = services['managers'][manager_id]
        manager.import_registry(filepath, merge=merge)

        return {
            "message": "Models imported successfully",
            "filepath": filepath
        }

    except Exception as e:
        logger.error(f"Import models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
