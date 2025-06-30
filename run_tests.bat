@echo off
set PYTHONPATH=%CD%;%CD%\agents;%CD%\memory
pytest %*
