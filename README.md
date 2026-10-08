PrognosIQ
Predictive maintenance platform: simulated industrial machines stream sensortelemetry over MQTT and OPC-UA, ML models trained on NASA's C-MAPSS datasetpredict Remaining Useful Life (RUL), and failing assets automaticallygenerate maintenance work orders on a live dashboard.

Stack
Core API: FastAPI + PostgreSQL (TimescaleDB for time-series)
Frontend: Next.js + TypeScript
ML: scikit-learn baseline → PyTorch LSTM/1D-CNN, with MLflow + DVC
Telemetry: MQTT (Mosquitto) + OPC-UA (asyncua), Kafka in Phase 5
Infra: Docker, GitHub Actions, Prometheus + Grafana, Evidently
