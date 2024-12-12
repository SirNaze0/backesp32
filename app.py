from flask import Flask, request, jsonify
import requests
import pandas as pd
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
# Configuración de Flask
app = Flask(__name__)
# Configurar CORS para permitir todos los orígenes y métodos
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE"], "allow_headers": "*"}})
# Configuración de Firebase
DATABASE_URL="https://esp32basico-default-rtdb.firebaseio.com"
ESTUDIANTES_URL = "https://esp32basico-default-rtdb.firebaseio.com/Estudiantes.json"  # URL de la rama Estudiantes
ASISTENCIA_URL = "https://esp32basico-default-rtdb.firebaseio.com/EstudiantesConAsistencia.json"  # URL de la rama EstudiantesConAsistencia
UPLOAD_FOLDER = './uploads'  # Carpeta temporal para guardar los archivos
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Verificar si el archivo tiene una extensión permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_estudiantes', methods=['POST'])
def upload_estudiantes():
    """
    Endpoint para subir un archivo Excel o CSV y agregar los datos a Firebase, 
    eliminando los datos previos antes de agregar los nuevos.
    """
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No se envió ningún archivo."}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"success": False, "message": "El archivo está vacío."}), 400

    if file and allowed_file(file.filename):
        try:
            # Guardar archivo temporalmente
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Leer archivo dependiendo de la extensión
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(filepath)

            # Convertir los datos a un formato esperado
            estudiantes = {}
            for _, row in df.iterrows():
                codigo = str(row['codigo'])  # Convertir código a string
                nombre = row['nombre']
                estudiantes[codigo] = {
                    "Android_id": 0,  # Valor por defecto
                    "Nombre": nombre
                }

            # Eliminar los datos existentes en la tabla Estudiantes
            delete_response = requests.delete(ESTUDIANTES_URL)

            # Verificar si la eliminación fue exitosa
            if delete_response.status_code == 200 or delete_response.status_code == 204:
                # Enviar nuevos datos a Firebase
                response = requests.patch(ESTUDIANTES_URL, json=estudiantes)

                if response.status_code == 200:
                    return jsonify({"success": True, "message": "Datos procesados y enviados correctamente.", "data": estudiantes}), 200
                else:
                    return jsonify({"success": False, "message": f"Error al enviar datos a Firebase: {response.status_code}"}), response.status_code
            else:
                return jsonify({"success": False, "message": f"Error al eliminar los datos existentes en Firebase: {delete_response.status_code}"}), delete_response.status_code

        except Exception as e:
            return jsonify({"success": False, "message": f"Error procesando el archivo: {str(e)}"}), 500
        finally:
            # Eliminar el archivo temporal
            if os.path.exists(filepath):
                os.remove(filepath)
    else:
        return jsonify({"success": False, "message": "El archivo no es válido. Sólo se permiten archivos CSV o Excel."}), 400


@app.route('/', methods=['GET'])
def home():
    """
    Endpoint de la raíz que muestra un mensaje de bienvenida.
    """
    return jsonify({
        "message": "¡Bienvenido a mi backend con Flask!",
        "status": "running"
    }), 200

@app.route('/get_estudiantes', methods=['GET'])
def get_estudiantes():
    """
    Endpoint para obtener la lista de estudiantes desde Firebase.
    """
    try:
        # Hacer una solicitud GET a Firebase para la tabla Estudiantes
        response = requests.get(ESTUDIANTES_URL)
        
        if response.status_code == 200:
            estudiantes = response.json()  # Convertir la respuesta JSON a un diccionario
            return jsonify({
                "success": True,
                "data": estudiantes
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": f"Error al obtener datos: {response.status_code}"
            }), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error inesperado: {str(e)}"
        }), 500

@app.route('/get_estudiantes_con_asistencia', methods=['GET'])
def get_estudiantes_con_asistencia():
    """
    Endpoint para obtener la lista de estudiantes con asistencia desde Firebase.
    """
    try:
        # Hacer una solicitud GET a Firebase para la tabla EstudiantesConAsistencia
        response = requests.get(ASISTENCIA_URL)
        
        if response.status_code == 200:
            asistencias = response.json()  # Convertir la respuesta JSON a un diccionario
            return jsonify({
                "success": True,
                "data": asistencias
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": f"Error al obtener datos: {response.status_code}"
            }), response.status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error inesperado: {str(e)}"
        }), 500

# Este bloque se coloca al final
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))