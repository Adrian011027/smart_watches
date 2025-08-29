// utils.js
// ===============================================

// ----------- 1. Empleados -----------------------
export async function obtenerEmpleados() {
  try {
    const response = await fetch("/empleados", { cache: "no-store" });
    if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("Error al obtener empleados:", error);
    return [];
  }
}

// ----------- 2. Backup -------------------------
export async function obtenerBackup() {
  try {
    const resp = await fetch("/backup.json", { cache: "no-store" });
    if (!resp.ok) throw new Error(`Error HTTP: ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.error("Error al obtener backup.json:", err);
    return [];
  }
}

/**
 * Convierte backup.json a un mapa:
 *   { [empleadoId]: [ tareasConEstatus0 ... ] }
 */
export function crearMapaTareasRealizadas(backupData = []) {
  const mapa = {};

  backupData.forEach(emp => {
    const terminadas = [];
    Object.entries(emp.tareas_asignadas || {}).forEach(([dia, tasks]) => {
      tasks.forEach(t => terminadas.push({ ...t, dia }));
    });
    mapa[emp.id] = terminadas;
  });

  return mapa;
}

// ----------- 3. Helpers generales --------------
export function animateCounter(element, target) {
  let current = 0;
  const duration = 1000;
  const stepTime = 20;
  const step = target / (duration / stepTime);
  const interval = setInterval(() => {
    current += step;
    if (current >= target) {
      current = target;
      clearInterval(interval);
    }
    element.textContent = Math.floor(current);
  }, stepTime);
}

/**
 * Devuelve TODAS las tareas (cualquier estatus) aplanadas en un solo array
 * añadiendo el campo `dia` capitalizado.
 */
export function getAllTasks(empleado) {
  const tasks = [];
  if (!empleado || !empleado.tareas_asignadas) return tasks;

  Object.entries(empleado.tareas_asignadas).forEach(([diaKey, dayTasks]) => {
    if (!Array.isArray(dayTasks)) return;
    const diaCapitalizado = diaKey.charAt(0).toUpperCase() + diaKey.slice(1);
    dayTasks.forEach(t => tasks.push({ ...t, dia: diaCapitalizado }));
  });

  return tasks;
}

// Día actual en minúsculas
export function getCurrentDayName() {
  const days = ["domingo", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado"];
  return days[new Date().getDay()];
}
export const capitalize = str => str.charAt(0).toUpperCase() + str.slice(1);

// ----------- 4. UI helper para detalle ---------
export function mostrarDetalleTareas(tasks, type) {
  const container = document.getElementById("calendario-container");
  container.innerHTML = "";
  container.style.display = "block";
  container.style.animation = "none";
  void container.offsetWidth; // reinicia anim
  container.style.animation = "fadeUp 0.5s ease forwards";

  const header = document.createElement("h2");
  header.textContent = `Detalle de tareas ${type}`;
  container.appendChild(header);

  const list = document.createElement("ul");
  list.classList.add("task-list");
  tasks.forEach(task => {
    const li = document.createElement("li");
    li.textContent = `${task.nombre} - ${task.hora || "-"} (${task.dia || ""})`;
    list.appendChild(li);
  });
  container.appendChild(list);

  const backBtn = document.createElement("button");
  backBtn.textContent = "Volver";
  backBtn.addEventListener("click", () => {
    if (window.currentEmpleado) {
      import("./menu.js").then(m => m.mostrarMenuOpciones(window.currentEmpleado));
    }
  });
  container.appendChild(backBtn);
}
