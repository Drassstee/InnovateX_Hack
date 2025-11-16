@echo off
echo ========================================
echo Installing requirements with CUDA PyTorch
echo ========================================
echo.

echo Step 1: Installing PyTorch with CUDA 12.1...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

echo.
echo Step 2: Installing other requirements...
pip install -r requirements.txt

echo.
echo ========================================
echo Installation complete!
echo ========================================
pause

