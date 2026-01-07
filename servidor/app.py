"""
Servidor Flask para Casa Domótica - SISTEMA COMPLETO
API REST con control manual/automático
"""

from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import csv
import io
from database.db_manager import DatabaseManager

app = Flask(__name__)
CORS(app)

# Inicializar base de datos
db = DatabaseManager()

# Estado del sistema
sistema_estado = {
    "modo": "automatico",  # "automatico" o "manual"
    "comandos_pendientes": {
        "ventilador": None,  # True/False/None
        "bomba": None,
        "servo": None,  # 0-180
        "leds": {}  # {"cuarto1": True/False}
    },
    "configuracion": {
        "temp_activacion": 30.0,
        "temp_desactivacion": 28.0,
        "humedad_suelo_seco": 30,
        "humedad_suelo_humedo": 70
    }
}

# ====================== HELPER FUNCTIONS ======================

def actualizar_estado_actuador_inmediato(**kwargs):
    """
    Actualiza el estado de actuadores en BD inmediatamente
    Esto asegura que el estado persista al refrescar la página
    """
    try:
        # Obtener estado actual o usar valores por defecto
        ultimo = db.obtener_ultimo_estado_actuadores() or {}
        
        # Actualizar con nuevos valores (mantener los existentes si no se especifican)
        servo_angulo = kwargs.get('servo_angulo', ultimo.get('servo_angulo', 90))
        ventilador_velocidad = kwargs.get('ventilador_velocidad', ultimo.get('ventilador_velocidad', 0))
        bomba_activa = kwargs.get('bomba_activa', ultimo.get('bomba_activa', False))
        leds = kwargs.get('leds', ultimo.get('leds', {}))
        
        # Asegurar que leds sea un dict
        if isinstance(leds, str):
            leds = json.loads(leds)
        
        # Insertar en base de datos
        db.insertar_estado_actuadores(
            servo_angulo=servo_angulo,
            ventilador_velocidad=ventilador_velocidad,
            bomba_activa=bomba_activa,
            leds=json.dumps(leds)
        )
        
        print(f"✓ Estado persistido en BD: servo={servo_angulo}°, ventilador={ventilador_velocidad}, bomba={bomba_activa}, leds={leds}")
        
    except Exception as e:
        print(f"✗ Error al persistir estado: {e}")


# ====================== RUTAS WEB ======================

@app.route('/')
def index():
    """Página principal del dashboard"""
    return render_template('index.html')

@app.route('/control')
def control():
    """Página de control manual"""
    return render_template('control.html')

@app.route('/historial')
def historial():
    """Página de historial"""
    return render_template('historial.html')

# ====================== API - DATOS ======================

@app.route('/api/datos/datos', methods=['POST'])
@app.route('/api/datos', methods=['POST'])
def recibir_datos():
    """
    Endpoint para recibir datos del ESP32
    POST: Guarda datos de sensores y actuadores en BD
    """
    try:
        datos = request.get_json()
        
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        print(f"📊 Datos recibidos del ESP32: {datos}")
        
        # Extraer datos
        sensores = datos.get('sensores', {})
        actuadores = datos.get('actuadores', {})
        
        # Guardar en base de datos
        db.insertar_lectura_sensores(
            temperatura=sensores.get('temperatura'),
            humedad=sensores.get('humedad'),
            movimiento=sensores.get('movimiento', 0),
            distancia=sensores.get('distancia'),
            humedad_suelo=sensores.get('humedad_suelo')
        )
        
        db.insertar_estado_actuadores(
            servo_angulo=actuadores.get('servo_angulo', 90),
            ventilador_velocidad=actuadores.get('ventilador_velocidad', 0),
            bomba_activa=actuadores.get('bomba_activa', False),
            leds=json.dumps(actuadores.get('leds', {}))
        )
        
        print("✓ Datos guardados en base de datos")
        
        return jsonify({"status": "success", "mensaje": "Datos guardados"}), 200
        
    except Exception as e:
        print(f"✗ Error en /api/datos: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ultimo-estado', methods=['GET'])
def ultimo_estado():
    """Obtiene el último estado de sensores y actuadores"""
    try:
        sensores = db.obtener_ultimas_lecturas(1)
        actuadores = db.obtener_ultimo_estado_actuadores()
        
        if sensores and len(sensores) > 0:
            ultimo_sensor = sensores[0]
            response = jsonify({
                "sensores": {
                    "temperatura": ultimo_sensor[1],
                    "humedad": ultimo_sensor[2],
                    "movimiento": ultimo_sensor[3],
                    "distancia": ultimo_sensor[4],
                    "humedad_suelo": ultimo_sensor[5],
                    "timestamp": str(ultimo_sensor[6])
                },
                "actuadores": actuadores if actuadores else {}
            })
            # Prevenir caché del navegador
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response, 200
        else:
            return jsonify({"mensaje": "No hay datos disponibles"}), 404
            
    except Exception as e:
        print(f"Error en /api/ultimo-estado: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/historial', methods=['GET'])
def obtener_historial():
    """
    Obtiene historial de lecturas
    GET params:
        - limite: número de registros (default: 100)
        - horas: filtrar últimas X horas
    """
    try:
        limite = request.args.get('limite', 100, type=int)
        horas = request.args.get('horas', type=int)
        
        if horas:
            lecturas = db.obtener_lecturas_por_tiempo(horas)
        else:
            lecturas = db.obtener_ultimas_lecturas(limite)
        
        # Formatear datos
        historial = []
        for lectura in lecturas:
            historial.append({
                "id": lectura[0],
                "temperatura": lectura[1],
                "humedad": lectura[2],
                "movimiento": lectura[3],
                "distancia": lectura[4],
                "humedad_suelo": lectura[5],
                "timestamp": str(lectura[6])
            })
        
        response = jsonify(historial)
        # Prevenir caché del navegador
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response, 200
        
    except Exception as e:
        print(f"Error en /api/historial: {e}")
        return jsonify({"error": str(e)}), 500

# ====================== API - CONTROL ======================

@app.route('/api/sistema/modo', methods=['GET', 'POST'])
def modo_sistema():
    """Obtener o cambiar modo del sistema (automático/manual)"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            modo = data.get('modo', 'automatico')
            
            if modo not in ['automatico', 'manual']:
                return jsonify({"error": "Modo inválido"}), 400
            
            sistema_estado['modo'] = modo
            print(f"🔄 Modo cambiado a: {modo}")
            
            # Si cambia a automático, limpiar comandos pendientes
            if modo == 'automatico':
                sistema_estado['comandos_pendientes'] = {
                    "ventilador": None,
                    "bomba": None,
                    "servo": None,
                    "leds": {}
                }
            
            return jsonify({
                "status": "success",
                "modo": modo
            }), 200
        else:
            return jsonify({
                "modo": sistema_estado['modo']
            }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/control/ventilador', methods=['POST'])
def controlar_ventilador():
    """Control manual del ventilador"""
    try:
        if sistema_estado['modo'] != 'manual':
            return jsonify({"error": "Sistema en modo automático"}), 400
        
        data = request.get_json()
        estado = data.get('estado', False)  # True/False
        
        sistema_estado['comandos_pendientes']['ventilador'] = estado
        print(f"🌀 Comando ventilador: {'ON' if estado else 'OFF'}")
        
        # Persistir estado inmediatamente en BD
        actualizar_estado_actuador_inmediato(ventilador_velocidad=100 if estado else 0)
        
        return jsonify({
            "status": "success",
            "ventilador": estado
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/control/bomba', methods=['POST'])
def controlar_bomba():
    """Control manual de la bomba"""
    try:
        if sistema_estado['modo'] != 'manual':
            return jsonify({"error": "Sistema en modo automático"}), 400
        
        data = request.get_json()
        estado = data.get('estado', False)  # True/False
        
        sistema_estado['comandos_pendientes']['bomba'] = estado
        print(f"💧 Comando bomba: {'ON' if estado else 'OFF'}")
        
        # Persistir estado inmediatamente en BD
        actualizar_estado_actuador_inmediato(bomba_activa=estado)
        
        return jsonify({
            "status": "success",
            "bomba": estado
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/control/servo', methods=['POST'])
def controlar_servo():
    """Control manual del servomotor"""
    try:
        if sistema_estado['modo'] != 'manual':
            return jsonify({"error": "Sistema en modo automático"}), 400
        
        data = request.get_json()
        angulo = data.get('angulo', 90)
        
        if not (0 <= angulo <= 180):
            return jsonify({"error": "Ángulo debe estar entre 0 y 180"}), 400
        
        sistema_estado['comandos_pendientes']['servo'] = angulo
        print(f"🔄 Comando servo: {angulo}°")
        
        # Persistir estado inmediatamente en BD
        actualizar_estado_actuador_inmediato(servo_angulo=angulo)
        
        return jsonify({
            "status": "success",
            "servo": angulo
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/control/led', methods=['POST'])
def controlar_led():
    """Control manual de LEDs individuales"""
    try:
        
        data = request.get_json()
        nombre = data.get('nombre')  # sala, cocina, cuarto, bano, pasillo
        estado = data.get('estado', False)
        
        if not nombre:
            return jsonify({"error": "Debe especificar el nombre del LED"}), 400
        
        if 'leds' not in sistema_estado['comandos_pendientes']:
            sistema_estado['comandos_pendientes']['leds'] = {}
        
        sistema_estado['comandos_pendientes']['leds'][nombre] = estado
        print(f"💡 Comando LED {nombre}: {'ON' if estado else 'OFF'}")
        
        # Persistir estado inmediatamente en BD
        # Obtener LEDs actuales y actualizar el específico
        ultimo = db.obtener_ultimo_estado_actuadores() or {}
        leds_actuales = ultimo.get('leds', {})
        if isinstance(leds_actuales, str):
            leds_actuales = json.loads(leds_actuales)
        leds_actuales[nombre] = estado
        actualizar_estado_actuador_inmediato(leds=leds_actuales)
        
        return jsonify({
            "status": "success",
            "led": nombre,
            "estado": estado
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comandos', methods=['GET'])
def obtener_comandos():
    """
    ESP32 consulta comandos pendientes
    Retorna modo, comandos y configuración
    """
    try:
        respuesta = {
            "modo": sistema_estado['modo'],
            "comandos": {},
            "configuracion": sistema_estado['configuracion']  # ← AGREGADO
        }
        
        # Solo enviar comandos si hay pendientes en modo manual
        if sistema_estado['modo'] == 'manual':
            comandos = sistema_estado['comandos_pendientes'].copy()
            
            # Filtrar comandos None
            respuesta['comandos'] = {
                k: v for k, v in comandos.items() 
                if v is not None and v != {}
            }
        
        return jsonify(respuesta), 200
        
    except Exception as e:
        print(f"Error en /api/comandos: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/configuracion', methods=['GET', 'POST'])
def configuracion():
    """Obtener o actualizar configuración de umbrales"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            
            # Actualizar configuración
            if 'temp_activacion' in data:
                sistema_estado['configuracion']['temp_activacion'] = float(data['temp_activacion'])
            if 'temp_desactivacion' in data:
                sistema_estado['configuracion']['temp_desactivacion'] = float(data['temp_desactivacion'])
            if 'humedad_suelo_seco' in data:
                sistema_estado['configuracion']['humedad_suelo_seco'] = int(data['humedad_suelo_seco'])
            if 'humedad_suelo_humedo' in data:
                sistema_estado['configuracion']['humedad_suelo_humedo'] = int(data['humedad_suelo_humedo'])
            
            print(f"⚙️ Configuración actualizada: {sistema_estado['configuracion']}")
            
            return jsonify({
                "status": "success",
                "configuracion": sistema_estado['configuracion']
            }), 200
        else:
            return jsonify(sistema_estado['configuracion']), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====================== API - EXPORTAR ======================

@app.route('/api/exportar/csv', methods=['GET'])
def exportar_csv():
    """Exportar historial a CSV"""
    try:
        horas = request.args.get('horas', 24, type=int)
        lecturas = db.obtener_lecturas_por_tiempo(horas)
        
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            'ID', 'Timestamp', 'Temperatura (°C)', 'Humedad (%)', 
            'Humedad Suelo (%)', 'Movimiento', 'Distancia (cm)'
        ])
        
        # Datos
        for lectura in lecturas:
            writer.writerow([
                lectura[0],  # ID
                lectura[6],  # Timestamp
                lectura[1],  # Temperatura
                lectura[2],  # Humedad
                lectura[5],  # Humedad suelo
                lectura[3],  # Movimiento
                lectura[4]   # Distancia
            ])
        
        # Preparar respuesta
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=historial_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
    except Exception as e:
        print(f"Error en /api/exportar/csv: {e}")
        return jsonify({"error": str(e)}), 500

# ====================== INICIO DEL SERVIDOR ======================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏠 SERVIDOR CASA DOMÓTICA - SISTEMA COMPLETO")
    print("="*60)
    print("Inicializando base de datos...")
    
    try:
        db.crear_tablas()
        print("✓ Base de datos lista\n")
    except Exception as e:
        print(f"✗ Error en base de datos: {e}\n")
    
    print("📡 Servidor iniciando en http://0.0.0.0:5000")
    print("   Dashboard: http://localhost:5000")
    print("   Control: http://localhost:5000/control")
    print("   Historial: http://localhost:5000/historial")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
