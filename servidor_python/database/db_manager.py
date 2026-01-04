"""
Database Manager para Casa Domótica
Gestiona almacenamiento de datos de sensores y actuadores
"""

import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path='database/casa_domotica.db'):
        self.db_path = db_path
        
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones a BD"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def crear_tablas(self):
        """Crea las tablas necesarias en la BD"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de lecturas de sensores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lecturas_sensores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    temperatura REAL,
                    humedad REAL,
                    movimiento INTEGER,
                    distancia REAL,
                    humedad_suelo REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de estado de actuadores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS estado_actuadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    servo_angulo INTEGER,
                    ventilador_velocidad INTEGER,
                    bomba_activa BOOLEAN,
                    leds TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de alertas/eventos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alertas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT,
                    mensaje TEXT,
                    nivel TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Crear índices para mejorar consultas
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp_sensores 
                ON lecturas_sensores(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp_actuadores 
                ON estado_actuadores(timestamp)
            ''')
            
            print("✓ Tablas creadas/verificadas correctamente")
    
    # ====================== SENSORES ======================
    
    def insertar_lectura_sensores(self, temperatura, humedad, movimiento, 
                                   distancia, humedad_suelo):
        """Inserta una nueva lectura de sensores"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lecturas_sensores 
                (temperatura, humedad, movimiento, distancia, humedad_suelo)
                VALUES (?, ?, ?, ?, ?)
            ''', (temperatura, humedad, movimiento, distancia, humedad_suelo))
            
            return cursor.lastrowid
    
    def obtener_ultimas_lecturas(self, limite=100):
        """Obtiene las últimas N lecturas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM lecturas_sensores 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limite,))
            
            return cursor.fetchall()
    
    def obtener_lecturas_por_tiempo(self, horas=24):
        """Obtiene lecturas de las últimas X horas"""
        fecha_limite = datetime.now() - timedelta(hours=horas)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM lecturas_sensores 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (fecha_limite,))
            
            return cursor.fetchall()
    
    # ====================== ACTUADORES ======================
    
    def insertar_estado_actuadores(self, servo_angulo, ventilador_velocidad,
                                     bomba_activa, leds):
        """Inserta el estado actual de los actuadores"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO estado_actuadores 
                (servo_angulo, ventilador_velocidad, bomba_activa, leds)
                VALUES (?, ?, ?, ?)
            ''', (servo_angulo, ventilador_velocidad, bomba_activa, leds))
            
            return cursor.lastrowid
    
    def obtener_ultimo_estado_actuadores(self):
        """Obtiene el último estado de los actuadores"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM estado_actuadores 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            
            resultado = cursor.fetchone()
            
            if resultado:
                return {
                    "id": resultado[0],
                    "servo_angulo": resultado[1],
                    "ventilador_velocidad": resultado[2],
                    "bomba_activa": bool(resultado[3]),
                    "leds": json.loads(resultado[4]) if resultado[4] else {},
                    "timestamp": resultado[5]
                }
            return None
    
    # ====================== ALERTAS ======================
    
    def insertar_alerta(self, tipo, mensaje, nivel='info'):
        """Inserta una nueva alerta/evento"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alertas (tipo, mensaje, nivel)
                VALUES (?, ?, ?)
            ''', (tipo, mensaje, nivel))
            
            return cursor.lastrowid
    
    def obtener_alertas_recientes(self, limite=50):
        """Obtiene las alertas más recientes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM alertas 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limite,))
            
            return cursor.fetchall()
    
    # ====================== ESTADÍSTICAS ======================
    
    def obtener_estadisticas(self):
        """Calcula estadísticas generales del sistema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Estadísticas de temperatura
            cursor.execute('''
                SELECT 
                    AVG(temperatura) as temp_promedio,
                    MIN(temperatura) as temp_minima,
                    MAX(temperatura) as temp_maxima,
                    AVG(humedad) as hum_promedio,
                    AVG(humedad_suelo) as hum_suelo_promedio
                FROM lecturas_sensores
                WHERE timestamp >= datetime('now', '-24 hours')
            ''')
            
            stats = cursor.fetchone()
            
            # Total de movimientos detectados
            cursor.execute('''
                SELECT COUNT(*) 
                FROM lecturas_sensores 
                WHERE movimiento = 1 
                AND timestamp >= datetime('now', '-24 hours')
            ''')
            
            movimientos = cursor.fetchone()[0]
            
            # Total de registros
            cursor.execute('SELECT COUNT(*) FROM lecturas_sensores')
            total_registros = cursor.fetchone()[0]
            
            return {
                "temperatura": {
                    "promedio": round(stats[0], 2) if stats[0] else 0,
                    "minima": round(stats[1], 2) if stats[1] else 0,
                    "maxima": round(stats[2], 2) if stats[2] else 0
                },
                "humedad": {
                    "promedio": round(stats[3], 2) if stats[3] else 0
                },
                "humedad_suelo": {
                    "promedio": round(stats[4], 2) if stats[4] else 0
                },
                "movimientos_24h": movimientos,
                "total_registros": total_registros
            }
    
    def limpiar_datos_antiguos(self, dias=30):
        """Elimina datos más antiguos de X días"""
        fecha_limite = datetime.now() - timedelta(days=dias)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM lecturas_sensores 
                WHERE timestamp < ?
            ''', (fecha_limite,))
            
            cursor.execute('''
                DELETE FROM estado_actuadores 
                WHERE timestamp < ?
            ''', (fecha_limite,))
            
            return cursor.rowcount

# ====================== TESTS ======================

if __name__ == '__main__':
    print("Probando Database Manager...")
    
    db = DatabaseManager('test_db.db')
    db.crear_tablas()
    
    # Insertar datos de prueba
    print("\n1. Insertando lectura de sensores...")
    id_lectura = db.insertar_lectura_sensores(
        temperatura=25.5,
        humedad=65.0,
        movimiento=1,
        distancia=150.0,
        humedad_suelo=45.0
    )
    print(f"✓ Lectura insertada con ID: {id_lectura}")
    
    # Insertar estado de actuadores
    print("\n2. Insertando estado de actuadores...")
    id_estado = db.insertar_estado_actuadores(
        servo_angulo=90,
        ventilador_velocidad=50,
        bomba_activa=True,
        leds=json.dumps({"cuarto1": True, "sala": False})
    )
    print(f"✓ Estado insertado con ID: {id_estado}")
    
    # Obtener últimas lecturas
    print("\n3. Obteniendo últimas lecturas...")
    lecturas = db.obtener_ultimas_lecturas(5)
    print(f"✓ Se obtuvieron {len(lecturas)} lecturas")
    
    # Obtener estadísticas
    print("\n4. Obteniendo estadísticas...")
    stats = db.obtener_estadisticas()
    print(f"✓ Estadísticas: {json.dumps(stats, indent=2)}")
    
    print("\n✓ Todas las pruebas completadas!")
