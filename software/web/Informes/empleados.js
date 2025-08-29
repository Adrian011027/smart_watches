//////////////////////////////////////////////
// empleados.js
//////////////////////////////////////////////
import { mostrarTareasEmpleado } from './main.js';

export function createEmpleadoCard(empleado, index) {
  const card = document.createElement("div");
  card.classList.add("empleado-card");

  // Color segun index
  const colorClass = `card-color-${index % 6}`;
  card.classList.add(colorClass);

  // Imagen
  const foto = document.createElement("img");
  foto.src = "/web/Images/" + empleado.imagen;
  foto.alt = `Foto de ${empleado.nombre}`;

  // Info
  const infoDiv = document.createElement("div");
  infoDiv.classList.add("empleado-info");

  const nombre = document.createElement("h2");
  nombre.textContent = empleado.nombre;

  const puesto = document.createElement("p");
  puesto.textContent = empleado.puesto;

  infoDiv.appendChild(nombre);
  infoDiv.appendChild(puesto);

  card.appendChild(foto);
  card.appendChild(infoDiv);

  // CLIC => Mostrar tareas
  card.addEventListener("click", () => {
    window.currentEmpleado = empleado;
    mostrarTareasEmpleado(empleado);
  });

  return card;
}
