@echo off
setlocal
set "ROOT=%~dp0.."
set "PYTHONPATH=%ROOT%\src"
set "PYTHONIOENCODING=utf-8"
python -m video_knowledge_pipeline.trusted_model_connector_mcp %*
