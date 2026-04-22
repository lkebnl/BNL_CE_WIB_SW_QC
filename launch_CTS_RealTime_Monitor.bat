@echo off
CALL C:\ProgramData\anaconda3\Scripts\activate.bat femb_env
cd /d "C:\Users\kelin\BNL_CE\BNL_CE_WIB_SW_QC"
python CTS_Real_Time_Monitor.py
pause
