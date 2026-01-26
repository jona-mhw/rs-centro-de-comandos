// Variables globales
let selectedCamaId = null;
let selectedEstadoId = null;

// ==========================================
// MONITOR DE CAMAS
// ==========================================

function initMonitor() {
    // Tabs de torres
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const torreId = this.dataset.torreId;

            // Actualizar tabs
            document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            // Mostrar contenido de torre
            document.querySelectorAll('.torre-content').forEach(c => c.classList.remove('active'));
            document.querySelector(`.torre-content[data-torre-id="${torreId}"]`).classList.add('active');
        });
    });

    // Click en celdas hexagonales
    document.querySelectorAll('.hex-cell').forEach(cell => {
        cell.addEventListener('click', function() {
            openEstadoModal(this);
        });
    });

    // Modal handlers
    initModalHandlers();
}

function openEstadoModal(cell) {
    selectedCamaId = cell.dataset.camaId;
    const estadoActual = cell.dataset.estadoId;
    const codigo = cell.querySelector('.cama-codigo').textContent;
    const sectorCard = cell.closest('.sector-card');
    const sectorName = sectorCard.querySelector('h4').textContent;

    // Actualizar info del modal
    document.getElementById('modal-cama-codigo').textContent = codigo;
    document.getElementById('modal-cama-ubicacion').textContent = sectorName;

    // Limpiar seleccion anterior
    document.querySelectorAll('.estado-btn').forEach(btn => {
        btn.classList.remove('selected');
        if (btn.dataset.estadoId === estadoActual) {
            btn.classList.add('selected');
            selectedEstadoId = estadoActual;
        }
    });

    // Limpiar comentario
    document.getElementById('comentario').value = '';

    // Mostrar modal
    document.getElementById('estado-modal').classList.add('active');
}

function initModalHandlers() {
    // Cerrar modales
    document.querySelectorAll('.modal-close, .modal-cancel, .modal-overlay').forEach(el => {
        el.addEventListener('click', function() {
            this.closest('.modal').classList.remove('active');
        });
    });

    // Seleccion de estado
    document.querySelectorAll('.estado-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.estado-btn').forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            selectedEstadoId = this.dataset.estadoId;
        });
    });

    // Guardar estado
    document.getElementById('btn-guardar-estado')?.addEventListener('click', guardarEstado);
}

async function guardarEstado() {
    if (!selectedCamaId || !selectedEstadoId) {
        alert('Por favor seleccione un estado');
        return;
    }

    const comentario = document.getElementById('comentario').value;

    try {
        const response = await fetch(`/api/cama/${selectedCamaId}/estado`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                estado_id: parseInt(selectedEstadoId),
                comentario: comentario
            })
        });

        const data = await response.json();

        if (data.success) {
            // Actualizar celda
            const cell = document.querySelector(`.hex-cell[data-cama-id="${selectedCamaId}"]`);
            cell.style.setProperty('--cell-color', data.cama.estado.color);
            cell.dataset.estadoId = data.cama.estado.id;
            cell.querySelector('.cama-estado').textContent = data.cama.estado.nombre;
            cell.title = `${data.cama.codigo} - ${data.cama.estado.nombre}`;

            // Cerrar modal
            document.getElementById('estado-modal').classList.remove('active');

            // Actualizar estadisticas
            loadStats();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al guardar el estado');
    }
}

// ==========================================
// ESTADISTICAS
// ==========================================

async function loadStats() {
    try {
        const response = await fetch('/api/estadisticas');
        const data = await response.json();

        renderStatsChart(data);
        renderStatsLegend(data);
        renderStatsSummary(data);
    } catch (error) {
        console.error('Error cargando estadisticas:', error);
    }
}

function renderStatsChart(data) {
    const chartContainer = document.getElementById('stats-chart');
    if (!chartContainer) return;

    const total = data.total;
    const estados = Object.entries(data.por_estado);

    let cumulativePercent = 0;
    let segments = '';

    estados.forEach(([nombre, info]) => {
        const percent = info.porcentaje;
        const dashArray = `${percent} ${100 - percent}`;
        const dashOffset = 100 - cumulativePercent;

        segments += `
            <circle
                cx="50" cy="50" r="40"
                fill="none"
                stroke="${info.color}"
                stroke-width="20"
                stroke-dasharray="${dashArray}"
                stroke-dashoffset="${dashOffset}"
            />
        `;

        cumulativePercent += percent;
    });

    chartContainer.innerHTML = `
        <svg viewBox="0 0 100 100" width="180" height="180">
            ${segments}
        </svg>
        <div class="chart-center">
            <div class="chart-total">${total}</div>
            <div class="chart-label">Camas</div>
        </div>
    `;
}

function renderStatsLegend(data) {
    const legendContainer = document.getElementById('stats-legend');
    if (!legendContainer) return;

    const estados = Object.entries(data.por_estado);

    legendContainer.innerHTML = estados.map(([nombre, info]) => `
        <div class="legend-item">
            <span class="legend-color" style="background-color: ${info.color};"></span>
            <span class="legend-label">${nombre}</span>
            <span class="legend-value">${info.count}</span>
            <span class="legend-percent">${info.porcentaje}%</span>
        </div>
    `).join('');
}

function renderStatsSummary(data) {
    const summaryContainer = document.getElementById('stats-summary');
    if (!summaryContainer) return;

    // Mostrar solo los principales
    const principales = ['Disponible', 'Ocupada', 'En Limpieza'];
    const estados = Object.entries(data.por_estado).filter(([nombre]) => principales.includes(nombre));

    summaryContainer.innerHTML = estados.map(([nombre, info]) => `
        <div class="stat-item">
            <span class="stat-color" style="background-color: ${info.color};"></span>
            <span class="stat-label">${nombre}</span>
            <span class="stat-value">${info.count}</span>
        </div>
    `).join('');
}

// ==========================================
// MANTENEDOR DE UBICACIONES
// ==========================================

function initUbicaciones() {
    // Nueva torre
    document.getElementById('btn-nueva-torre')?.addEventListener('click', () => {
        openUbicacionModal('torre', null, 'Nueva Torre');
    });

    // Agregar piso
    document.querySelectorAll('.btn-add-piso').forEach(btn => {
        btn.addEventListener('click', function() {
            const torreId = this.closest('.torre-item').dataset.id;
            openUbicacionModal('piso', torreId, 'Nuevo Piso');
        });
    });

    // Agregar sector
    document.querySelectorAll('.btn-add-sector').forEach(btn => {
        btn.addEventListener('click', function() {
            const pisoId = this.closest('.piso-item').dataset.id;
            openUbicacionModal('sector', pisoId, 'Nuevo Sector');
        });
    });

    // Editar ubicacion
    document.querySelectorAll('.tree-item .btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const item = this.closest('.tree-item');
            const id = item.dataset.id;
            const nombre = item.querySelector('.tree-name').textContent;
            const tipo = item.classList.contains('torre-item') ? 'torre' :
                        item.classList.contains('piso-item') ? 'piso' : 'sector';

            openUbicacionModal(tipo, null, `Editar ${tipo}`, id, nombre);
        });
    });

    // Agregar cama
    document.querySelectorAll('.btn-add-cama').forEach(btn => {
        btn.addEventListener('click', function() {
            const sectorId = this.closest('.sector-item').dataset.id;
            openCamaModal(sectorId);
        });
    });

    // Eliminar ubicacion
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', async function() {
            if (!confirm('Desea eliminar esta ubicacion?')) return;

            const item = this.closest('.tree-item');
            const id = item.dataset.id;

            try {
                const response = await fetch(`/api/ubicacion/${id}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    item.remove();
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });

    // Eliminar cama
    document.querySelectorAll('.tag-delete').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.stopPropagation();
            if (!confirm('Desea eliminar esta cama?')) return;

            const tag = this.closest('.cama-tag');
            const camaId = tag.dataset.camaId;

            try {
                const response = await fetch(`/api/cama/${camaId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    tag.remove();
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });

    // Modal handlers
    initUbicacionModalHandlers();
}

function openUbicacionModal(tipo, padreId, titulo, id = null, nombre = '') {
    document.getElementById('ubicacion-modal-title').textContent = titulo;
    document.getElementById('ubicacion-id').value = id || '';
    document.getElementById('ubicacion-tipo').value = tipo;
    document.getElementById('ubicacion-padre-id').value = padreId || '';
    document.getElementById('ubicacion-nombre').value = nombre;

    // Mostrar/ocultar camas por fila segun tipo
    const camasPorFilaGroup = document.getElementById('camas-por-fila-group');
    if (tipo === 'sector') {
        camasPorFilaGroup.style.display = 'block';
    } else {
        camasPorFilaGroup.style.display = 'none';
    }

    document.getElementById('ubicacion-modal').classList.add('active');
}

function openCamaModal(ubicacionId) {
    document.getElementById('cama-ubicacion-id').value = ubicacionId;
    document.getElementById('cama-codigo').value = '';
    document.getElementById('cama-nombre').value = '';
    document.getElementById('cama-modal').classList.add('active');
}

function initUbicacionModalHandlers() {
    // Guardar ubicacion
    document.getElementById('btn-guardar-ubicacion')?.addEventListener('click', async () => {
        const id = document.getElementById('ubicacion-id').value;
        const tipo = document.getElementById('ubicacion-tipo').value;
        const padreId = document.getElementById('ubicacion-padre-id').value;
        const nombre = document.getElementById('ubicacion-nombre').value;
        const camasPorFila = document.getElementById('ubicacion-camas-por-fila').value;

        if (!nombre.trim()) {
            alert('El nombre es requerido');
            return;
        }

        const data = {
            nombre: nombre,
            tipo: tipo,
            padre_id: padreId ? parseInt(padreId) : null,
            camas_por_fila: parseInt(camasPorFila)
        };

        try {
            const url = id ? `/api/ubicacion/${id}` : '/api/ubicacion';
            const method = id ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                location.reload();
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });

    // Guardar cama
    document.getElementById('btn-guardar-cama')?.addEventListener('click', async () => {
        const ubicacionId = document.getElementById('cama-ubicacion-id').value;
        const codigo = document.getElementById('cama-codigo').value;
        const nombre = document.getElementById('cama-nombre').value;

        if (!codigo.trim()) {
            alert('El codigo es requerido');
            return;
        }

        try {
            const response = await fetch('/api/cama', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    codigo: codigo,
                    nombre: nombre,
                    ubicacion_id: parseInt(ubicacionId)
                })
            });

            if (response.ok) {
                location.reload();
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
}
