# Aumentar límites generales para el servidor Flask
# Al inicio del archivo, después de las importaciones:

import os
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
# ... resto de importaciones

# Configuración del servidor para manejar archivos grandes y tiempos de ejecución prolongados
app = Flask(__name__)

# Aumentar límite de tamaño de subida a 500MB
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Si estás utilizando Gunicorn, añade en tu archivo de configuración o al iniciar Gunicorn:
# gunicorn app:app --timeout 900 --workers 2 --threads 4 --worker-class gthread

# Si estás utilizando un servidor uvicorn o similar, configura un mayor tiempo de espera
# uvicorn app:app --timeout-keep-alive 900

# Para la ruta del endpoint modify_ifc, asegúrate de aumentar los tiempos de espera y agregar manejo de archivos grandes:

@app.route('/modify_ifc', methods=['POST'])
def modify_ifc():
    try:
        # Obtener valores de los encabezados personalizados que enviamos desde el frontend
        processing_timeout = int(request.headers.get('X-Processing-Timeout', 600000)) / 1000  # Convertir a segundos
        file_size = int(request.headers.get('X-File-Size', 0))
        processing_mode = request.headers.get('X-Processing-Mode', 'complete')
        
        # Ajustar tiempo de operación basado en tamaño del archivo
        operation_timeout = min(max(processing_timeout, 600), 1200)  # Entre 10 y 20 minutos
        
        print(f"Iniciando procesamiento de archivo IFC. Tamaño: {file_size/1024/1024:.2f} MB. Modo: {processing_mode}")
        print(f"Timeout ajustado: {operation_timeout} segundos")
        
        # Establecer un timeout para esta operación específica
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"La operación excedió el tiempo máximo permitido ({operation_timeout} segundos)")
        
        # Configurar timeout para esta operación
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(operation_timeout))
        
        # Código existente para procesar el archivo
        file = request.files.get('file')
        if not file:
            return jsonify({"message": "No se proporcionó archivo"}), 400
            
        # Asegurarse de guardar el archivo en un directorio temporal con suficiente espacio
        temp_dir = '/tmp/ifc_processing'  # Ajustar según tu entorno
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        temp_filepath = os.path.join(temp_dir, filename)
        
        # Guardar archivo de manera eficiente
        file.save(temp_filepath)
        print(f"Archivo guardado en: {temp_filepath}")
        
        # Obtener los valores para modificar desde el formulario
        ifc_project_value = request.form.get('ifcProjectValue', '')
        ifc_site_value = request.form.get('ifcSiteValue', '')
        ifc_building_value = request.form.get('ifcBuildingValue', '')
        
        # Obtener valores actuales para procesamiento más eficiente
        current_values = {}
        
        # Si el archivo es grande, consideramos procesar por partes o con optimizaciones
        if file_size > 100 * 1024 * 1024:  # Más de 100MB
            print("Archivo grande detectado, aplicando optimizaciones de procesamiento")
            # Aquí podrías implementar optimizaciones específicas para archivos grandes
            # Por ejemplo, usar un subproceso con más memoria asignada
        
        # Procesar el archivo IFC (aquí va tu lógica actual)
        # ...
        # Tu código de procesamiento IFC aquí, que utiliza ifc_project_value, ifc_site_value, ifc_building_value
        # ...
        
        # Eliminar el temporizador una vez que el procesamiento ha terminado
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        
        # Después del procesamiento exitoso, enviar el archivo
        # Asumiendo que el archivo procesado se guarda en output_filepath
        return send_file(output_filepath, as_attachment=True)
        
    except TimeoutError as e:
        print(f"Error de timeout: {str(e)}")
        return jsonify({"message": f"El procesamiento ha excedido el tiempo máximo: {str(e)}"}), 504
    except Exception as e:
        print(f"Error en el procesamiento: {str(e)}")
        return jsonify({"message": f"Error al procesar el archivo IFC: {str(e)}"}), 500
    finally:
        # Limpiar recursos, archivos temporales, etc.
        try:
            if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            if 'output_filepath' in locals() and os.path.exists(output_filepath) and output_filepath != temp_filepath:
                # Solo eliminar si es diferente al archivo temporal original
                pass  # Decidir si eliminar o no
        except Exception as e:
            print(f"Error al limpiar recursos: {str(e)}")

# Endpoint para get_ifc_values similar, con ajustes de timeout
@app.route('/get_ifc_values', methods=['POST'])
def get_ifc_values():
    try:
        # Obtener timeout de los encabezados
        processing_timeout = int(request.headers.get('X-Processing-Timeout', 120000)) / 1000  # Convertir a segundos
        analysis_mode = request.headers.get('X-Analysis-Mode', 'fast')
        
        # Limitar el timeout a un valor razonable
        operation_timeout = min(max(processing_timeout, 60), 180)  # Entre 1 y 3 minutos
        
        print(f"Iniciando análisis de valores IFC. Modo: {analysis_mode}")
        print(f"Timeout ajustado: {operation_timeout} segundos")
        
        # Configurar timeout para esta operación
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"El análisis excedió el tiempo máximo permitido ({operation_timeout} segundos)")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(operation_timeout))
        
        # Resto del código existente para obtener valores
        # ...
        
        # Desactivar el temporizador
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        
        # Devolver valores
        return jsonify({
            'project': project_value,
            'site': site_value,
            'building': building_value
        })
        
    except TimeoutError as e:
        print(f"Error de timeout: {str(e)}")
        return jsonify({"message": f"El análisis ha excedido el tiempo máximo: {str(e)}"}), 504
    except Exception as e:
        print(f"Error en el análisis: {str(e)}")
        return jsonify({"message": f"Error al analizar el archivo IFC: {str(e)}"}), 500
    finally:
        # Limpiar recursos
        pass

# Añadir un endpoint de estado para verificaciones de salud
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "online"})


# Si usas script principal
if __name__ == '__main__':
    # Aumentar timeout del servidor de desarrollo
    # Nota: Esto solo afecta al servidor de desarrollo de Flask
    app.run(debug=True, threaded=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
