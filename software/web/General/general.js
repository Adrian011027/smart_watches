// Refactor: separación de estado, cache DOM, DocumentFragment, mejor manejo de horas/animaciones y reloj

const diasSemana = ["domingo", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado"];

const state = {
  currentDayIndex: new Date().getDay(),
  trabajadores: [],
  currentEmpPage: 0,
  pageSize: 5
};

const DOM = {};

document.addEventListener('DOMContentLoaded', init);

async function init() {
  cacheSelectors();
  setupInitialAnimations();
  bindUIEvents();

  try {
    const resp = await fetch('/empleados.json');
    if (!resp.ok) throw new Error('Error al obtener los empleados');
    state.trabajadores = await resp.json();
  } catch (err) {
    console.error('Error al cargar empleados:', err);
    state.trabajadores = [];
  }

  renderForCurrentState();
  startClock();
}

/* Cacheo de selectores */
function cacheSelectors() {
  DOM.titulo = document.querySelector('h2');
  DOM.clockContainer = document.querySelector('.clock-container');
  DOM.tableWrapper = document.getElementById('table-wrapper');
  DOM.nextDayBtn = document.getElementById('next-day-btn');
  DOM.todayBtn = document.getElementById('today-btn');
  DOM.prevEmpBtn = document.getElementById('prev-emp-page');
  DOM.nextEmpBtn = document.getElementById('next-emp-page');
  DOM.tasksDayLabel = document.getElementById('tasks-day');
  DOM.workerTable = document.getElementById('worker-table');
  DOM.tbody = DOM.workerTable.querySelector('tbody');
  DOM.theadRow = DOM.workerTable.querySelector('thead tr');
}

/* Animaciones iniciales (fade-in en cascada) */
function setupInitialAnimations() {
  if (DOM.titulo) {
    DOM.titulo.classList.add('fade-in');
    setTimeout(() => DOM.titulo.classList.add('show'), 100);
  }
  if (DOM.clockContainer) setTimeout(() => DOM.clockContainer.classList.add('show'), 500);
  if (DOM.tableWrapper) setTimeout(() => DOM.tableWrapper.classList.add('show'), 1000);
}

/* Bind de eventos UI */
function bindUIEvents() {
  if (DOM.nextDayBtn) DOM.nextDayBtn.addEventListener('click', () => {
    animateDayChange('left', () => {
      state.currentDayIndex = (state.currentDayIndex + 1) % 7;
      renderForCurrentState();
    });
  });

  if (DOM.todayBtn) DOM.todayBtn.addEventListener('click', () => {
    animateDayChange('right', () => {
      state.currentDayIndex = new Date().getDay();
      renderForCurrentState();
    });
  });

  if (DOM.prevEmpBtn) DOM.prevEmpBtn.addEventListener('click', () => {
    if (state.currentEmpPage > 0) {
      animateEmpPageChange('right', () => {
        state.currentEmpPage--;
        renderForCurrentState();
      });
    }
  });

  if (DOM.nextEmpBtn) DOM.nextEmpBtn.addEventListener('click', () => {
    const maxPage = Math.max(0, Math.floor((state.trabajadores.length - 1) / state.pageSize));
    if (state.currentEmpPage < maxPage) {
      animateEmpPageChange('left', () => {
        state.currentEmpPage++;
        renderForCurrentState();
      });
    }
  });
}

/* Render principal según estado */
function renderForCurrentState() {
  const dayName = diasSemana[state.currentDayIndex];
  if (DOM.tasksDayLabel) DOM.tasksDayLabel.textContent = dayName.toUpperCase();

  DOM.theadRow.innerHTML = '';
  DOM.tbody.innerHTML = '';

  const startIndex = state.currentEmpPage * state.pageSize;
  const visibleTrabajadores = state.trabajadores.slice(startIndex, startIndex + state.pageSize);
  buildHeader(visibleTrabajadores);

  const actividades = collectActivitiesForDay(dayName);
  const rowsData = actividades.sort((a, b) => compareHour(a.hora, b.hora));
  buildRows(rowsData, visibleTrabajadores);

  mergeCells(0);
  updateClockVisibility();

  const maxPage = Math.max(0, Math.floor((state.trabajadores.length - 1) / state.pageSize));
  if (DOM.prevEmpBtn) DOM.prevEmpBtn.disabled = (state.currentEmpPage <= 0);
  if (DOM.nextEmpBtn) DOM.nextEmpBtn.disabled = (state.currentEmpPage >= maxPage);
}

/* Construir encabezado usando DocumentFragment */
function buildHeader(visible) {
  const frag = document.createDocumentFragment();

  const horarioTh = document.createElement('th'); horarioTh.innerText = 'Horario'; frag.appendChild(horarioTh);
  const actividadTh = document.createElement('th'); actividadTh.innerText = 'Actividad'; frag.appendChild(actividadTh);

  visible.forEach(trab => {
    const th = document.createElement('th');
    const container = document.createElement('div');
    container.className = 'worker-header';

    const img = document.createElement('img');
    img.src = `/web/images/${trab.imagen || ''}`;
    img.alt = trab.nombre || '';
    container.appendChild(img);

    const text = document.createElement('div');
    text.className = 'worker-text';
    const name = document.createElement('span'); name.className = 'worker-name'; name.innerText = trab.nombre || '';
    const role = document.createElement('span'); role.className = 'worker-role'; role.innerText = trab.puesto || '';
    text.appendChild(name); text.appendChild(role);
    container.appendChild(text);

    th.appendChild(container);
    frag.appendChild(th);
  });

  // columnas vacías para completar pageSize
  for (let i = visible.length; i < state.pageSize; i++) {
    const thEmpty = document.createElement('th'); thEmpty.innerText = ''; frag.appendChild(thEmpty);
  }

  DOM.theadRow.appendChild(frag);
}

/* Recolecta actividades (unique por nombre) tomando la hora más temprana */
function collectActivitiesForDay(dayName) {
  const mapa = new Map();
  state.trabajadores.forEach(trab => {
    const tareas = (trab.tareas_asignadas && trab.tareas_asignadas[dayName]) || [];
    tareas.forEach(t => {
      const key = t.nombre || '';
      const existing = mapa.get(key);
      if (!existing) {
        mapa.set(key, { nombre: t.nombre, descripcion: t.descripcion || '', hora: t.hora || '' });
      } else {
        if (compareHour(t.hora, existing.hora) < 0) {
          mapa.set(key, { nombre: t.nombre, descripcion: t.descripcion || '', hora: t.hora || '' });
        }
      }
    });
  });
  return Array.from(mapa.values());
}

/* Construye filas usando DocumentFragment */
function buildRows(rowsData, visibleTrabajadores) {
  const frag = document.createDocumentFragment();
  const dayName = diasSemana[state.currentDayIndex];

  rowsData.forEach(rowData => {
    const tr = document.createElement('tr');

    const horarioCell = document.createElement('td');
    horarioCell.innerText = rowData.hora ? `${rowData.hora} hrs` : '-';
    tr.appendChild(horarioCell);

    const actividadCell = document.createElement('td');
    actividadCell.style.verticalAlign = 'top';
    actividadCell.style.textAlign = 'left';
    const nombreDiv = document.createElement('div'); nombreDiv.className = 'activity-name'; nombreDiv.innerText = rowData.nombre;
    const descDiv = document.createElement('div'); descDiv.className = 'activity-desc'; descDiv.innerText = rowData.descripcion || '';
    actividadCell.appendChild(nombreDiv); actividadCell.appendChild(descDiv);
    tr.appendChild(actividadCell);

    visibleTrabajadores.forEach(trab => {
      const td = document.createElement('td');
      const tareas = (trab.tareas_asignadas && trab.tareas_asignadas[dayName]) || [];
      const tarea = tareas.find(t => t.nombre === rowData.nombre);
      if (tarea) {
        td.className = getStatusClass(tarea.estatus, tarea.hora);
        td.innerText = '';
      } else {
        td.innerText = '-';
      }
      tr.appendChild(td);
    });

    // celdas vacías si faltan cols
    for (let i = visibleTrabajadores.length; i < state.pageSize; i++) {
      const tdEmpty = document.createElement('td'); tdEmpty.innerText = ''; tr.appendChild(tdEmpty);
    }

    frag.appendChild(tr);
  });

  DOM.tbody.appendChild(frag);
}

/* Fusionar celdas verticalmente en la columna indicada */
function mergeCells(columnIndex) {
  const rows = Array.from(DOM.tbody.rows);
  if (!rows.length) return;
  let prevCell = null;
  let spanCount = 1;
  for (let i = 0; i < rows.length; i++) {
    const cell = rows[i].cells[columnIndex];
    if (!cell) continue;
    const text = cell.innerText;
    if (prevCell && prevCell.innerText === text) {
      spanCount++;
      prevCell.rowSpan = spanCount;
      cell.remove();
    } else {
      prevCell = cell;
      spanCount = 1;
    }
  }
}

/* Comparador de horas (considera minutos), devuelve negativa si h1 < h2 */
function compareHour(h1 = '', h2 = '') {
  if (!h1 && !h2) return 0;
  if (!h1) return 1;
  if (!h2) return -1;
  const [H1, M1 = '0'] = h1.split(':');
  const [H2, M2 = '0'] = h2.split(':');
  const a = parseInt(H1, 10) || 0;
  const b = parseInt(H2, 10) || 0;
  const ma = parseInt(M1, 10) || 0;
  const mb = parseInt(M2, 10) || 0;
  return a - b || ma - mb;
}

/* Determina clase según estatus y si la hora ya pasó (considera minutos) */
function getStatusClass(estatus, hora) {
  if (hora) {
    const now = new Date();
    const [H = '0', M = '0'] = (hora || '').split(':');
    const taskDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), parseInt(H, 10) || 0, parseInt(M, 10) || 0);
    if (taskDate < now && estatus !== 0) return 'status-overdue';
  }
  switch (estatus) {
    case 1: return 'status-inprogress';
    case 2: return 'status-todo';
    case 3: return 'status-extras';
    case 0: return 'status-done';
    default: return '';
  }
}

/* Mostrar/ocultar columnas de hora/min/seg y botón Hoy */
function updateClockVisibility() {
  const realClockCols = document.querySelectorAll('.clock-col-real');
  const isToday = (state.currentDayIndex === new Date().getDay());
  realClockCols.forEach(col => col.classList.toggle('hidden', !isToday));
  if (DOM.todayBtn) DOM.todayBtn.classList.toggle('hidden', isToday);
}

/* Animaciones reutilizables */
function animateEmpPageChange(direction, onComplete) {
  const exitClass = direction === 'left' ? 'slide-left-exit' : 'slide-right-exit';
  const enterClass = direction === 'left' ? 'slide-left-enter' : 'slide-right-enter';
  runTransition(DOM.tableWrapper, exitClass, enterClass, onComplete);
}

function animateDayChange(direction, onComplete) {
  const exitClass = direction === 'left' ? 'slide-left-exit' : 'slide-right-exit';
  const enterClass = direction === 'left' ? 'slide-left-enter' : 'slide-right-enter';
  runTransitionMultiple([DOM.tableWrapper, DOM.tasksDayLabel], exitClass, enterClass, onComplete);
}

function runTransition(el, exitClass, enterClass, onComplete) {
  if (!el) return onComplete && onComplete();
  el.classList.add(exitClass);
  const onEnd = () => {
    el.classList.remove(exitClass);
    el.removeEventListener('animationend', onEnd);
    onComplete && onComplete();
    el.classList.add(enterClass);
    const onEndEnter = () => { el.classList.remove(enterClass); el.removeEventListener('animationend', onEndEnter); };
    el.addEventListener('animationend', onEndEnter);
  };
  el.addEventListener('animationend', onEnd);
}

function runTransitionMultiple(elements, exitClass, enterClass, onComplete) {
  const els = elements.filter(Boolean);
  if (!els.length) return onComplete && onComplete();
  let exited = 0;
  const needed = els.length;
  els.forEach(el => {
    const onEnd = () => {
      el.classList.remove(exitClass);
      el.removeEventListener('animationend', onEnd);
      exited++;
      if (exited === needed) {
        onComplete && onComplete();
        let entered = 0;
        els.forEach(e2 => {
          const onEnterEnd = () => {
            e2.classList.remove(enterClass);
            e2.removeEventListener('animationend', onEnterEnd);
            entered++;
          };
          e2.classList.add(enterClass);
          e2.addEventListener('animationend', onEnterEnd);
        });
      }
    };
    el.classList.add(exitClass);
    el.addEventListener('animationend', onEnd);
  });
}

/* Reloj: intervalo por segundo y actualización de variables CSS */
let clockTimer = null;
function startClock() {
  updateTime(); // inmediata
  if (clockTimer) clearInterval(clockTimer);
  clockTimer = setInterval(updateTime, 1000);
}

function updateTime() {
  const now = new Date();
  const hours = now.getHours().toString().padStart(2, '0');
  const minutes = now.getMinutes().toString().padStart(2, '0');
  const seconds = now.getSeconds().toString().padStart(2, '0');
  const dayName = diasSemana[now.getDay()].toUpperCase();

  document.documentElement.style.setProperty('--timer-hours', `"${hours}"`);
  document.documentElement.style.setProperty('--timer-minutes', `"${minutes}"`);
  document.documentElement.style.setProperty('--timer-seconds', `"${seconds}"`);
  document.documentElement.style.setProperty('--timer-day', `"${dayName}"`);

  requestAnimationFrame(updateTime);
}
