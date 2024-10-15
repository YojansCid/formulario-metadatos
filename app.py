from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

app = Flask(__name__)

# Definir la ruta para guardar los archivos TXT de registros
RUTA_ARCHIVOS_TXT = os.path.join(os.getcwd(), "Archivos_TXT")

# Crear la carpeta si no existe
if not os.path.exists(RUTA_ARCHIVOS_TXT):
    os.makedirs(RUTA_ARCHIVOS_TXT)

# Definir las rutas para guardar los datos localmente (opcional)
RUTA_DATOS = 'datos'
RUTA_EXCEL = os.path.join(RUTA_DATOS, 'compilado.xlsx')

# Configuración de Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Planilla_formulario_metadatos").sheet1  # Nombre de la hoja de cálculo

# Autenticación para Google Drive
gauth = GoogleAuth()
gauth.credentials = creds

# Inicializar Google Drive
drive = GoogleDrive(gauth)

# Definir la lista personalizada de palabras vacías en español
STOP_WORDS_SPANISH = [
    'a', 'actualmente', 'adelante', 'además', 'afirmó', 'agregó', 'ahora', 'ahí', 'al', 'algo', 'alguna', 'algunas',
    'alguno', 'algunos', 'algún', 'alrededor', 'ambos', 'ampleamos', 'ante', 'anterior', 'antes', 'apenas',
    'aproximadamente', 'aquel', 'aquellas', 'aquellos', 'aqui', 'aquí', 'arriba', 'aseguró', 'así', 'atras',
    'aunque', 'ayer', 'añadió', 'aún', 'bajo', 'bastante', 'bien', 'buen', 'buena', 'buenas', 'bueno', 'buenos',
    'cada', 'casi', 'cerca', 'cierta', 'ciertas', 'cierto', 'ciertos', 'cinco', 'comentó', 'como', 'con', 'conocer',
    'conseguimos', 'conseguir', 'considera', 'consideró', 'consigo', 'consigue', 'consiguen', 'consigues', 'contra',
    'cosas', 'creo', 'cual', 'cuales', 'cualquier', 'cuando', 'cuanto', 'cuatro', 'cuenta', 'cómo', 'da', 'dado',
    'dan', 'dar', 'de', 'debe', 'deben', 'debido', 'decir', 'dejó', 'del', 'demás', 'dentro', 'desde', 'después',
    'dice', 'dicen', 'dicho', 'dieron', 'diferente', 'diferentes', 'dijeron', 'dijo', 'dio', 'donde', 'dos',
    'durante', 'e', 'ejemplo', 'el', 'ella', 'ellas', 'ello', 'ellos', 'embargo', 'empleais', 'emplean', 'emplear',
    'empleas', 'empleo', 'en', 'encima', 'encuentra', 'entonces', 'entre', 'era', 'erais', 'eramos', 'eran', 'eras',
    'eres', 'es', 'esa', 'esas', 'ese', 'eso', 'esos', 'esta', 'estaba', 'estabais', 'estaban', 'estabas', 'estad',
    'estada', 'estadas', 'estado', 'estados', 'estais', 'estamos', 'estan', 'estando', 'estar', 'estaremos', 'estará',
    'estarán', 'estarás', 'estaré', 'estaréis', 'estaría', 'estaríais', 'estaríamos', 'estarían', 'estarías', 'estas',
    'este', 'estemos', 'esto', 'estos', 'estoy', 'estuve', 'estuviera', 'estuvierais', 'estuvieran', 'estuvieras',
    'estuvieron', 'estuviese', 'estuvieseis', 'estuviesen', 'estuvieses', 'estuvimos', 'estuviste', 'estuvisteis',
    'estuviéramos', 'estuviésemos', 'estuvo', 'está', 'estábamos', 'estáis', 'están', 'estás', 'esté', 'estéis',
    'estén', 'estés', 'ex', 'existe', 'existen', 'explicó', 'expresó', 'fin', 'fue', 'fuera', 'fuerais', 'fueran',
    'fueras', 'fueron', 'fuese', 'fueseis', 'fuesen', 'fueses', 'fui', 'fuimos', 'fuiste', 'fuisteis', 'fuéramos',
    'fuésemos', 'gran', 'grandes', 'gueno', 'ha', 'haber', 'habida', 'habidas', 'habido', 'habidos', 'habiendo',
    'habremos', 'habrá', 'habrán', 'habrás', 'habré', 'habréis', 'habría', 'habríais', 'habríamos', 'habrían',
    'habrías', 'habéis', 'había', 'habíais', 'habíamos', 'habían', 'habías', 'hace', 'haceis', 'hacemos', 'hacen',
    'hacer', 'hacerlo', 'haces', 'hacia', 'haciendo', 'hago', 'han', 'has', 'hasta', 'hay', 'haya', 'hayamos',
    'hayan', 'hayas', 'hayáis', 'he', 'hecho', 'hemos', 'hicieron', 'hizo', 'hoy', 'hube', 'hubiera', 'hubierais',
    'hubieran', 'hubieras', 'hubieron', 'hubiese', 'hubieseis', 'hubiesen', 'hubieses', 'hubimos', 'hubiste',
    'hubisteis', 'hubiéramos', 'hubiésemos', 'hubo', 'igual', 'incluso', 'la', 'las', 'le', 'les', 'lo', 'los',
    'luego', 'más', 'me', 'mi', 'mientras', 'mis', 'muy', 'ni', 'no', 'nos', 'nuestra', 'nuestro', 'o', 'otra',
    'otros', 'para', 'pero', 'poco', 'por', 'que', 'qué', 'quien', 'se', 'si', 'sido', 'sin', 'su', 'sus', 'tal',
    'también', 'te', 'tu', 'un', 'una', 'unas', 'uno', 'unos', 'y', 'ya'
]

# Funciones

def generar_id_unico():
    return datetime.now().strftime("%Y%m%d%H%M%S")

# Extraer palabras clave

def extraer_palabras_clave(texto, n_palabras=10):
    documentos = [texto]
    vectorizador = CountVectorizer(stop_words=STOP_WORDS_SPANISH)
    matriz_frecuencia = vectorizador.fit_transform(documentos)
    suma_palabras = np.array(matriz_frecuencia.sum(axis=0)).flatten()
    palabras = vectorizador.get_feature_names_out()
    palabras_importantes = [palabras[i] for i in suma_palabras.argsort()[::-1]]
    return ", ".join(palabras_importantes[:n_palabras])

@app.route('/generar_palabras_clave', methods=['POST'])
def generar_palabras_clave():
    try:
        resumen = request.json.get("resumen", "")
        if not resumen:
            return jsonify({"error": "No se proporcionó un resumen"}), 400
        palabras_clave = extraer_palabras_clave(resumen)
        return jsonify({"palabras_clave": palabras_clave})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        id_unico = generar_id_unico()
        titulo = request.form['titulo']
        resumen = request.form['resumen']
        palabras_clave = request.form['palabrasClave']
        proposito = request.form['proposito']
        fecha_creacion = request.form['fechaCreacion']
        fecha_actualizacion = request.form['fechaActualizacion']

        # Organización Responsable
        if request.form['organizacionResponsable'] == "OTRO":
            organizacion_responsable = request.form['otroOrganizacion']
        else:
            organizacion_responsable = request.form['organizacionResponsable']

        modificado = request.form['modificado']
        contacto = request.form['contacto']

        # Sistema de Referencia Espacial
        if request.form['sistemaReferencia'] == "OTRO":
            sistema_referencia = request.form['otroSistemaReferencia']
        else:
            sistema_referencia = request.form['sistemaReferencia']

        # Formato de Distribución
        if request.form['formatoDistribucion'] == "OTRO":
            formato_distribucion = request.form['otroFormato']
        else:
            formato_distribucion = request.form['formatoDistribucion']

        restricciones = request.form['restricciones']

        # Idioma
        if request.form['idioma'] == "OTRO":
            idioma = request.form['otroIdioma']
        else:
            idioma = request.form['idioma']

        # Conformidad
        if request.form['conformidad'] == "OTRO":
            conformidad = request.form['otroConformidad']
        else:
            conformidad = request.form['conformidad']

        ruta = request.form['ruta']

        try:
            # Guardar en la planilla con el ID único
            sheet.append_row([
                id_unico, titulo, resumen, palabras_clave, proposito,
                fecha_creacion, fecha_actualizacion, organizacion_responsable,
                modificado, contacto, sistema_referencia, formato_distribucion,
                restricciones, idioma, conformidad, ruta
            ])

            # Guardar registro en un archivo TXT individual
            archivo_txt_path = os.path.join(RUTA_ARCHIVOS_TXT, f"{id_unico}_{titulo}.txt")
            with open(archivo_txt_path, 'w', encoding='utf-8') as archivo_txt:
                archivo_txt.write(f"ID Único: {id_unico}\n")
                archivo_txt.write(f"Título: {titulo}\n")
                archivo_txt.write(f"Resumen: {resumen}\n")
                archivo_txt.write(f"Palabras Clave: {palabras_clave}\n")
                archivo_txt.write(f"Propósito: {proposito}\n")
                archivo_txt.write(f"Fecha de Creación: {fecha_creacion}\n")
                archivo_txt.write(f"Fecha de Actualización: {fecha_actualizacion}\n")
                archivo_txt.write(f"Organización Responsable: {organizacion_responsable}\n")
                archivo_txt.write(f"Modificado por Laboratorio: {modificado}\n")
                archivo_txt.write(f"Contacto: {contacto}\n")
                archivo_txt.write(f"Sistema de Referencia Espacial: {sistema_referencia}\n")
                archivo_txt.write(f"Formato de Distribución: {formato_distribucion}\n")
                archivo_txt.write(f"Restricciones de Uso: {restricciones}\n")
                archivo_txt.write(f"Idioma: {idioma}\n")
                archivo_txt.write(f"Conformidad: {conformidad}\n")
                archivo_txt.write(f"Ruta: {ruta}\n")

            # Subir archivo a Google Drive en la carpeta específica
            folder_id = '11UuTT-FWQfYWOUZkJfOOJt6-1qhE4r9A'
            archivo_drive = drive.CreateFile({'title': f"{id_unico}_{titulo}.txt", 'parents': [{'id': folder_id}]})
            archivo_drive.SetContentFile(archivo_txt_path)
            archivo_drive.Upload()

        except Exception as e:
            print(f"Error al guardar en Google Sheets o en archivo TXT: {e}")
            return f"Error al guardar en Google Sheets o en archivo TXT: {e}"

        return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)