// =====================================================
// WEBSOCKET - TIEMPO REAL
// =====================================================

let socket = null;
let reconnectInterval = null;

function conectarWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    console.log('🔌 Conectando WebSocket:', wsUrl);

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('✓ WebSocket conectado');
        actualizarEstadoConexion(true);

        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }

        cargarDatosIniciales();
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('📨 WebSocket:', data);

            if (data.type === 'sensor_update') {
                actualizarSensorIndividual(data);
            } else if (data.type === 'sensor_data') {
                actualizarMetricas(data.data);
            } else if (data.type === 'actuator_change') {
                console.log(`Actuador ${data.device}:`, data.value);
            }
        } catch (error) {
            console.error('Error WebSocket:', error);
        }
    };

    socket.onerror = (error) => {
        console.error('✗ Error WebSocket');
        actualizarEstadoConexion(false);
    };

    socket.onclose = () => {
        console.log('✗ WebSocket desconectado');
        actualizarEstadoConexion(false);

        if (!reconnectInterval) {
            reconnectInterval = setInterval(() => {
                console.log('🔄 Reconectando...');
                conectarWebSocket();
            }, 5000);
        }
    };
}

function actualizarSensorIndividual(data) {
    const { sensor, value } = data;

    if (sensor === 'temperatura') {
        const elem = document.querySelector('.metric-card:nth-child(1) .metric-value');
        if (elem) elem.textContent = `${value.toFixed(1)}°C`;
    } else if (sensor === 'humedad') {
        const elem = document.querySelector('.metric-card:nth-child(2) .metric-value');
        if (elem) elem.textContent = `${value.toFixed(1)}%`;
    } else if (sensor === 'humedad_suelo') {
        const elem = document.querySelector('.metric-card:nth-child(3) .metric-value');
        if (elem) elem.textContent = `${value}%`;
    }

    actualizarUltimaActualizacion();
}

async function cargarDatosIniciales() {
    try {
        const [resEstado, resHistorial] = await Promise.all([
            fetch('/api/ultimo-estado'),
            fetch('/api/historial?horas=24&limite=50')
        ]);

        if (resEstado.ok) {
            const data = await resEstado.json();
            actualizarMetricas(data);
        }

        if (resHistorial.ok) {
            const historial = await resHistorial.json();
            actualizarGraficas(historial);
        }
    } catch (error) {
        console.error('Error cargando datos:', error);
    }
}

function actualizarMetricas(data) {
    if (!data || !data.sensores) return;

    const s = data.sensores;

    const tempElem = document.querySelector('.metric-card:nth-child(1) .metric-value');
    if (tempElem && s.temperatura !== undefined) {
        tempElem.textContent = `${s.temperatura.toFixed(1)}°C`;
    }

    const humElem = document.querySelector('.metric-card:nth-child(2) .metric-value');
    if (humElem && s.humedad !== undefined) {
        humElem.textContent = `${s.humedad.toFixed(1)}%`;
    }

    const sueloElem = document.querySelector('.metric-card:nth-child(3) .metric-value');
    if (sueloElem && s.humedad_suelo !== undefined) {
        sueloElem.textContent = `${s.humedad_suelo}%`;
    }

    actualizarUltimaActualizacion();
}

function actualizarUltimaActualizacion() {
    const elem = document.querySelector('.last-update');
    if (elem) {
        elem.textContent = `Última actualización: ${new Date().toLocaleTimeString('es-PE')}`;
    }
}

function actualizarEstadoConexion(conectado) {
    const elem = document.querySelector('.connection-status');
    if (elem) {
        elem.innerHTML = conectado
            ? '<span style="color: var(--accent-success);">● Conectado</span>'
            : '<span style="color: var(--accent-danger);">● Desconectado</span>';
    }
}

let chartTemp, chartHumedad, chartSuelo;

function actualizarGraficas(historial) {
    if (!historial || historial.length === 0) return;

    historial.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    const datos = historial.slice(-20);

    const labels = datos.map(d => new Date(d.timestamp).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' }));
    const temps = datos.map(d => d.temperatura);
    const hums = datos.map(d => d.humedad);
    const suelo = datos.map(d => d.humedad_suelo);

    const ctxTemp = document.getElementById('chartTemperatura');
    if (ctxTemp) {
        if (chartTemp) chartTemp.destroy();
        chartTemp = new Chart(ctxTemp, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Temperatura (°C)',
                    data: temps,
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: false } }
            }
        });
    }

    const ctxHum = document.getElementById('chartHumedad');
    if (ctxHum) {
        if (chartHumedad) chartHumedad.destroy();
        chartHumedad = new Chart(ctxHum, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Humedad (%)',
                    data: hums,
                    borderColor: 'rgb(6, 182, 212)',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: false } }
            }
        });
    }

    const ctxSuelo = document.getElementById('chartSuelo');
    if (ctxSuelo) {
        if (chartSuelo) chartSuelo.destroy();
        chartSuelo = new Chart(ctxSuelo, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Humedad Suelo (%)',
                    data: suelo,
                    borderColor: 'rgb(139, 92, 246)',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function () {
    console.log('🏠 Iniciando Dashboard Premium...');
    conectarWebSocket();
    setInterval(cargarDatosIniciales, 30000);
});
