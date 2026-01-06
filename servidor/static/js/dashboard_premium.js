// =====================================================
// CASA DOMÓTICA - DASHBOARD PREMIUM
// =====================================================

let chartTempHum, chartSuelo;
let updateInterval;

// =====================================================
// INICIALIZACIÓN
// =====================================================

document.addEventListener('DOMContentLoaded', function () {
    console.log('🏠 Iniciando Dashboard Premium...');

    inicializarGraficas();
    cargarDatos();

    // Actualizar cada 5 segundos
    updateInterval = setInterval(cargarDatos, 5000);

    // Pausar actualizaciones cuando la pestaña no está visible
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            clearInterval(updateInterval);
        } else {
            updateInterval = setInterval(cargarDatos, 5000);
            cargarDatos();
        }
    });
});

// =====================================================
// GRÁFICAS
// =====================================================

function inicializarGraficas() {
    // Configuración común
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#999999',
                    font: { size: 12, family: 'Inter' },
                    padding: 15
                }
            }
        },
        scales: {
            x: {
                grid: {
                    color: '#2a2a2a',
                    lineWidth: 1
                },
                ticks: {
                    color: '#666666',
                    font: { size: 11 }
                }
            },
            y: {
                grid: {
                    color: '#2a2a2a',
                    lineWidth: 1
                },
                ticks: {
                    color: '#666666',
                    font: { size: 11 }
                }
            }
        }
    };

    // Gráfica Temperatura & Humedad (Líneas)
    const ctxTempHum = document.getElementById('chartTempHum').getContext('2d');
    chartTempHum = new Chart(ctxTempHum, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperatura (°C)',
                    data: [],
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 5
                },
                {
                    label: 'Humedad (%)',
                    data: [],
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 5
                }
            ]
        },
        options: commonOptions
    });

    // Gráfica Humedad del Suelo (Línea)
    const ctxSuelo = document.getElementById('chartSuelo').getContext('2d');
    chartSuelo = new Chart(ctxSuelo, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Humedad del Suelo (%)',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true,
                pointRadius: 0,
                pointHoverRadius: 5
            }]
        },
        options: commonOptions
    });
}

// =====================================================
// CARGA DE DATOS
// =====================================================

async function cargarDatos() {
    try {
        // Agregar timestamp para evitar caché del navegador
        const timestamp = new Date().getTime();

        // Cargar último estado
        const responseEstado = await fetch(`/api/ultimo-estado?_t=${timestamp}`);

        if (responseEstado.ok) {
            const data = await responseEstado.json();
            actualizarMetricas(data);
            actualizarEstadoConexion(true);
        } else {
            actualizarEstadoConexion(false);
        }

        // Cargar historial para gráficas
        const responseHistorial = await fetch(`/api/historial?horas=24&limite=50&_t=${timestamp}`);
        if (responseHistorial.ok) {
            const historial = await responseHistorial.json();
            actualizarGraficas(historial);
        }

    } catch (error) {
        console.error('Error al cargar datos:', error);
        actualizarEstadoConexion(false);
    }
}

// =====================================================
// ACTUALIZAR MÉTRICAS
// =====================================================

function actualizarMetricas(data) {
    const sensores = data.sensores || {};
    const actuadores = data.actuadores || {};

    // TEMPERATURA
    const temp = sensores.temperatura || 0;
    document.getElementById('temperatura').textContent = temp.toFixed(1);

    const tempBadge = document.getElementById('tempBadge');
    if (temp > 30) {
        tempBadge.textContent = '🔥 Temperatura alta';
        tempBadge.className = 'metric-badge badge-danger';
    } else if (temp < 18) {
        tempBadge.textContent = '❄️ Temperatura baja';
        tempBadge.className = 'metric-badge badge-info';
    } else {
        tempBadge.textContent = '✓ Normal';
        tempBadge.className = 'metric-badge badge-success';
    }

    // HUMEDAD AMBIENTAL
    const hum = sensores.humedad || 0;
    document.getElementById('humedad').textContent = hum.toFixed(1);

    const humBadge = document.getElementById('humBadge');
    if (hum > 70) {
        humBadge.textContent = '💦 Muy húmedo';
        humBadge.className = 'metric-badge badge-info';
    } else if (hum < 30) {
        humBadge.textContent = '🏜️ Muy seco';
        humBadge.className = 'metric-badge badge-warning';
    } else {
        humBadge.textContent = '✓ Óptima';
        humBadge.className = 'metric-badge badge-success';
    }

    // HUMEDAD DEL SUELO
    const suelo = sensores.humedad_suelo || 0;
    document.getElementById('humedadSuelo').textContent = suelo;

    const sueloBadge = document.getElementById('sueloBadge');
    if (suelo < 30) {
        sueloBadge.textContent = '💧 Riego necesario';
        sueloBadge.className = 'metric-badge badge-warning';
    } else if (suelo > 70) {
        sueloBadge.textContent = '💦 Bien hidratado';
        sueloBadge.className = 'metric-badge badge-success';
    } else {
        sueloBadge.textContent = '✓ Adecuada';
        sueloBadge.className = 'metric-badge badge-info';
    }

    // ÚLTIMA ACTUALIZACIÓN
    const ahora = new Date();
    const horaStr = ahora.toLocaleTimeString('es-PE', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('ultimaActualizacion').textContent = horaStr;

    // ACTUADORES
    actualizarActuadores(actuadores);

    // EFICIENCIA (calculada basada en uso de actuadores)
    calcularEficiencia(actuadores);
}

// =====================================================
// ACTUALIZAR ACTUADORES
// =====================================================

function actualizarActuadores(actuadores) {
    // Ventilador
    const ventiladorStatus = document.getElementById('ventiladorStatus');
    const ventiladorActivo = actuadores.leds && actuadores.leds.cuarto1;

    if (ventiladorActivo) {
        ventiladorStatus.textContent = 'ON';
        ventiladorStatus.className = 'actuator-status active';
    } else {
        ventiladorStatus.textContent = 'OFF';
        ventiladorStatus.className = 'actuator-status inactive';
    }

    // Bomba
    const bombaStatus = document.getElementById('bombaStatus');
    const bombaActiva = actuadores.bomba_activa;

    if (bombaActiva) {
        bombaStatus.textContent = 'ON';
        bombaStatus.className = 'actuator-status active';
    } else {
        bombaStatus.textContent = 'OFF';
        bombaStatus.className = 'actuator-status inactive';
    }

    // Servo
    const servoAngulo = actuadores.servo_angulo || 90;
    document.getElementById('servoStatus').textContent = servoAngulo + '°';

    // LEDs individuales
    const leds = actuadores.leds || {};

    // LED Cuarto 1
    const ledCuarto1Status = document.getElementById('ledCuarto1Status');
    if (ledCuarto1Status) {
        if (leds.cuarto1) {
            ledCuarto1Status.textContent = 'ON';
            ledCuarto1Status.className = 'actuator-status active';
        } else {
            ledCuarto1Status.textContent = 'OFF';
            ledCuarto1Status.className = 'actuator-status inactive';
        }
    }

    // LED Cuarto 2
    const ledCuarto2Status = document.getElementById('ledCuarto2Status');
    if (ledCuarto2Status) {
        if (leds.cuarto2) {
            ledCuarto2Status.textContent = 'ON';
            ledCuarto2Status.className = 'actuator-status active';
        } else {
            ledCuarto2Status.textContent = 'OFF';
            ledCuarto2Status.className = 'actuator-status inactive';
        }
    }

    // LED Cuarto 3
    const ledCuarto3Status = document.getElementById('ledCuarto3Status');
    if (ledCuarto3Status) {
        if (leds.cuarto3) {
            ledCuarto3Status.textContent = 'ON';
            ledCuarto3Status.className = 'actuator-status active';
        } else {
            ledCuarto3Status.textContent = 'OFF';
            ledCuarto3Status.className = 'actuator-status inactive';
        }
    }
}

// =====================================================
// CALCULAR EFICIENCIA
// =====================================================

function calcularEficiencia(actuadores) {
    // Simulación: menos actuadores activos = mayor eficiencia
    const ventiladorActivo = actuadores.leds && actuadores.leds.cuarto1 ? 1 : 0;
    const bombaActiva = actuadores.bomba_activa ? 1 : 0;
    const leds = actuadores.leds || {};
    const ledsActivos = Object.values(leds).filter(v => v).length;

    // Cálculo simple de eficiencia (100% - uso de energía)
    const usoEnergia = (ventiladorActivo * 20) + (bombaActiva * 15) + (ledsActivos * 5);
    const eficiencia = Math.max(50, 100 - usoEnergia);

    document.getElementById('eficienciaValor').textContent = eficiencia;
    document.getElementById('eficienciaBar').style.width = eficiencia + '%';
}

// =====================================================
// ACTUALIZAR GRÁFICAS
// =====================================================

function actualizarGraficas(historial) {
    if (!historial || historial.length === 0) return;

    // Ordenar por timestamp
    historial.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    // Tomar muestras equidistantes (máximo 20 puntos)
    const muestras = historial.length > 20 ?
        historial.filter((_, i) => i % Math.ceil(historial.length / 20) === 0) :
        historial;

    // Preparar labels
    const labels = muestras.map(item => {
        const fecha = new Date(item.timestamp);
        return fecha.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' });
    });

    // Actualizar gráfica Temp & Hum
    chartTempHum.data.labels = labels;
    chartTempHum.data.datasets[0].data = muestras.map(item => item.temperatura);
    chartTempHum.data.datasets[1].data = muestras.map(item => item.humedad);
    chartTempHum.update('none');

    // Actualizar gráfica Suelo
    chartSuelo.data.labels = labels;
    chartSuelo.data.datasets[0].data = muestras.map(item => item.humedad_suelo);
    chartSuelo.update('none');
}

// =====================================================
// ESTADO DE CONEXIÓN
// =====================================================

function actualizarEstadoConexion(conectado) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    if (conectado) {
        statusDot.classList.remove('offline');
        statusText.textContent = 'Online';
    } else {
        statusDot.classList.add('offline');
        statusText.textContent = 'Offline';
    }
}

// =====================================================
// LIMPIEZA
// =====================================================

window.addEventListener('beforeunload', function () {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
