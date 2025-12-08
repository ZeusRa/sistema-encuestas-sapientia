import sys
import os

# Agrega el directorio padre (backend) al sys.path para que los tests puedan importar 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
