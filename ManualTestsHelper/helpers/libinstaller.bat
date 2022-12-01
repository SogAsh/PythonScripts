pushd %~dp0
python -m pip install -r requirements.txt
python ini.py
popd
pause