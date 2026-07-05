REQUISITOS:
- Python 3.11 (SOLO ESE ME FUNCIONA A MI)
- MediaPipe 0.10.35 (Ese calcula postura)
- OpenCV
- Streamlit


PowerShell o GitBash pon esto muñaño:
-     git clone https://github.com/renzo-lorenzo/SEMINARIO1.git
-     cd SEMINARIO1


Dentro de la carpeta SEMINARIO01 pon esto:
-     py -3.11 -m venv venv
-     .\venv\Scripts\activate
Te debera salir una vaina asi "(venv) PS C:\...\SEMINARIO1>"


Ahora ejecuta esto:
-     python -m pip install -r requirements.txt
te debe salir "Python 3.11.x" y "mediapipe 0.10.14"


Si quieres correr la app, escribe esto
-     python -m streamlit run app.py
