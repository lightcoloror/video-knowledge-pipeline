@echo off
setlocal
set "ROOT=%~dp0.."
set "PYTHONPATH=%ROOT%\src"
python -m video_knowledge_pipeline.openclaw_http %*
