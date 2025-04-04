import os
import tempfile
import ifcopenshell
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurar CORS para permitir peticiones desde el frontend
CORS_ORIGIN = os.environ.get('CORS_ORIGIN', '*')
CORS(app, resources={r"/*": {"origins": CORS_ORIGIN}})

# Crear directorios temporales si no existen
UPLOAD_FOLDER = "/mnt/disks/ifc_uploads"
MODIFY_FOLDER = "/mnt/disks/modify_ifc"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODIFY_FOLDER, exist_ok=True)

logger.info(f"Directorios de almacenamiento: UPLOAD_FOLDER={UPLOAD_FOLDER}, MODIFY_FOLDER={MODIFY_FOLDER}")

@app.route('/status', methods=['GET'])
def status():
    """Endpoint para verificar el estado del servidor"""
    logger.info("Verificando estado del servidor")
    return jsonify({"status": "online"}), 200

@app.route('/get_ifc_values', methods=['POST'])
def get_ifc_values():
    """Endpoint para obtener los valores actuales del archivo IFC"""
    try:
        logger.info("Procesando solicitud para obtener valores IFC")
        
        # Verificar si hay un archivo en la solicitud
        if 'file' not in request.files:
            logger.error("No se encontró el archivo en la solicitud")
            return jsonify({"error": "No se encontró el archivo"}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("Nombre de archivo vacío")
            return jsonify({"error": "Nombre de archivo vacío"}), 400
        
        # Guardar el archivo temporalmente
        temp_filename = secure_filename(file.filename)
        temp_filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(temp_filepath)
        logger.info(f"Archivo guardado temporalmente en {temp_filepath}")
        
        # Abrir el archivo IFC
        try:
            ifc_file = ifcopenshell.open(temp_filepath)
            logger.info("Archivo IFC abierto correctamente")
            
            # Obtener los valores de proyecto, sitio y edificio
            project_value = ""
            site_value = ""
            building_value = ""
            
            # Obtener el proyecto
            projects = ifc_file.by_type("IfcProject")
            if projects:
                project = projects[0]
                if project.Name:
                    project_value = project.Name
                elif project.LongName:
                    project_value = project.LongName
                logger.info(f"Valor del proyecto encontrado: {project_value}")
            
            # Obtener el sitio
            sites = ifc_file.by_type("IfcSite")
            if sites:
                site = sites[0]
                if site.Name:
                    site_value = site.Name
                elif site.LongName:
                    site_value = site.LongName
                logger.info(f"Valor del sitio encontrado: {site_value}")
            
            # Obtener el edificio
            buildings = ifc_file.by_type("IfcBuilding")
            if buildings:
                building = buildings[0]
                if building.Name:
                    building_value = building.Name
                elif building.LongName:
                    building_value = building.LongName
                logger.info(f"Valor del edificio encontrado: {building_value}")
            
            # Eliminar el archivo temporal
            os.remove(temp_filepath)
            logger.info(f"Archivo temporal eliminado: {temp_filepath}")
            
            return jsonify({
                "project": project_value,
                "site": site_value,
                "building": building_value
            }), 200
            
        except Exception as e:
            logger.error(f"Error al abrir o procesar el archivo IFC: {str(e)}")
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            return jsonify({"error": f"Error al procesar el archivo IFC: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error general: {str(e)}")
        return jsonify({"error": f"Error del servidor: {str(e)}"}), 500

@app.route('/modify_ifc', methods=['POST'])
def modify_ifc():
    """Endpoint para modificar los valores de un archivo IFC"""
    try:
        logger.info("Procesando solicitud para modificar archivo IFC")
        
        # Verificar si hay un archivo en la solicitud
        if 'file' not in request.files:
            logger.error("No se encontró el archivo en la solicitud")
            return jsonify({"error": "No se encontró el archivo"}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("Nombre de archivo vacío")
            return jsonify({"error": "Nombre de archivo vacío"}), 400
        
        # Obtener los valores del formulario
        ifc_project_value = request.form.get('ifcProjectValue', '')
        ifc_site_value = request.form.get('ifcSiteValue', '')
        ifc_building_value = request.form.get('ifcBuildingValue', '')
        save_to_folder = request.form.get('saveToFolder', 'modify_ifc')
        
        logger.info(f"Valores a modificar: Proyecto={ifc_project_value}, Sitio={ifc_site_value}, Edificio={ifc_building_value}")
        logger.info(f"Carpeta de destino: {save_to_folder}")
        
        # Guardar el archivo temporalmente
        temp_filename = secure_filename(file.filename)
        temp_filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(temp_filepath)
        logger.info(f"Archivo guardado temporalmente en {temp_filepath}")
        
        # Definir la ruta del archivo modificado
        parts = os.path.splitext(temp_filename)
        modified_filename = f"{parts[0]}_modified{parts[1]}"
        modified_filepath = os.path.join(
            MODIFY_FOLDER if save_to_folder == 'modify_ifc' else UPLOAD_FOLDER, 
            modified_filename
        )
        
        # Abrir y modificar el archivo IFC
        try:
            ifc_file = ifcopenshell.open(temp_filepath)
            logger.info("Archivo IFC abierto correctamente")
            
            # Modificar el proyecto
            if ifc_project_value:
                projects = ifc_file.by_type("IfcProject")
                if projects:
                    project = projects[0]
                    project.Name = ifc_project_value
                    logger.info(f"Valor del proyecto modificado a: {ifc_project_value}")
            
            # Modificar el sitio
            if ifc_site_value:
                sites = ifc_file.by_type("IfcSite")
                if sites:
                    site = sites[0]
                    site.Name = ifc_site_value
                    logger.info(f"Valor del sitio modificado a: {ifc_site_value}")
            
            # Modificar el edificio
            if ifc_building_value:
                buildings = ifc_file.by_type("IfcBuilding")
                if buildings:
                    building = buildings[0]
                    building.Name = ifc_building_value
                    logger.info(f"Valor del edificio modificado a: {ifc_building_value}")
            
            # Guardar el archivo modificado
            ifc_file.write(modified_filepath)
            logger.info(f"Archivo modificado guardado en: {modified_filepath}")
            
            # Eliminar el archivo original temporal
            os.remove(temp_filepath)
            logger.info(f"Archivo temporal eliminado: {temp_filepath}")
            
            # Devolver el archivo modificado
            return send_file(modified_filepath, as_attachment=True, download_name=modified_filename)
            
        except Exception as e:
            logger.error(f"Error al modificar archivo IFC: {str(e)}")
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            return jsonify({"error": f"Error al modificar el archivo IFC: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error general: {str(e)}")
        return jsonify({"error": f"Error del servidor: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
