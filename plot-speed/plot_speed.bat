@echo off
:loop
cls
python plot_speed.py .
ping -n 5 localhost >nul
goto loop