#include <vector>

#include "eventos.h"
#include "funciones/control_carga.h"
#include "funciones/control_tareas/control_tareas.h"
#include "eventos/var_pantalla.h"
#include "funciones/control_tareas/var_tareas.h"

void marcarTareaCompletada(std::vector<Tarea> &listaTareas, lv_obj_t *boton, lv_obj_t *contenedor, lv_obj_t *contenedorPrincipal);

void AbrirTareasExtras(lv_event_t *e)
{
    lv_scr_load(ui_PantallaTareasExtras);                                // 🔹 Cambia a la pantalla de Tareas Extras
    lv_obj_set_parent(ui_ContInformacionReloj, ui_PantallaTareasExtras); // 🔹 Mueve el AppBar a la nueva pantalla
    lv_obj_set_parent(ui_ContAnimacionDeCarga, ui_PantallaTareasExtras); // 🔹 Mueve el AppBar a la nueva pantalla
}

void AbrirPendientes(lv_event_t *e)
{
    lv_scr_load(ui_PantallaPendientes);                                // 🔹 Cambia a la pantalla de Pendientes
    lv_obj_set_parent(ui_ContInformacionReloj, ui_PantallaPendientes); // 🔹 Mueve el AppBar a la nueva pantalla
    lv_obj_set_parent(ui_ContAnimacionDeCarga, ui_PantallaPendientes); // 🔹 Mueve el AppBar a la nueva pantalla
}

void completarTarea(lv_event_t *e)
{
    marcarTareaCompletada(listaTareas, ui_BtnCompletarTarea, ui_ContPContenido, ui_ContPanelPrincial);
}

void completarTareaExtra(lv_event_t *e)
{
    marcarTareaCompletada(listaTareasExtras, ui_BtnCompletarTareaExtra, ui_ContTEContenido, ui_ContTareasExtras);
}

void marcarTareaCompletada(std::vector<Tarea> &listaTareas,
                           lv_obj_t *boton,
                           lv_obj_t *contenedor,
                           lv_obj_t *contenedorPrincipal)
{
    if (!pantallaEncendida)
        return;

    for (size_t i = 0; i < listaTareas.size(); i++)
    {
        auto &t = listaTareas[i];
        if (t.estado == "En Progreso")
        {
            Serial.printf("✅ Tarea completada: %s\n", t.nombre.c_str());

            // 1️⃣ Cambiar estado y color (verde)
            t.estado = "Completado";    
            lv_obj_set_style_text_color(t.label, obtenerColorEstado("Completado"), 0);

            // 2️⃣ Guardamos datos para el timer
            struct TimerData {
                std::vector<Tarea>* lista;
                String taskId;
            };

            TimerData* data = new TimerData{&listaTareas, t.taskId};

            // 3️⃣ Timer para borrar después de 3s
            lv_timer_create([](lv_timer_t* timer){
                TimerData* data = static_cast<TimerData*>(timer->user_data);
                auto &lista = *data->lista;

                auto it = std::find_if(lista.begin(), lista.end(),
                                       [&](const Tarea& x){ return x.taskId == data->taskId; });

                if (it != lista.end()) {
                    // Borrar label
                    if (it->label) {
                        lv_obj_del(it->label);
                    }
                    // Borrar del vector
                    lista.erase(it);

                    // Promover siguiente
                    if (!lista.empty()) {
                        lista[0].estado = "En Progreso";
                        lv_obj_set_style_text_color(lista[0].label, obtenerColorEstado("En Progreso"), 0);
                        Serial.printf("🔄 Nueva tarea en progreso: %s\n", lista[0].nombre.c_str());
                    }
                }

                delete data;
                lv_timer_del(timer);
            }, 3000, data);

            // 4️⃣ Refrescar botones/UI
            actualizarEstadoBotonYContenedor(listaTareas, boton, contenedor, contenedorPrincipal);

            // 📡 Enviar al servidor por WebSocket
            JsonDocument doc;
            bool esTareaExtra = (&listaTareas == &listaTareasExtras);
            doc["accion"] = esTareaExtra ? "tarea_extra" : "tarea_terminada";
            doc["Tarea"] = t.nombre;
            doc["TaskID"] = t.taskId;
            doc["Empleado"] = t.idEmpleado;
            doc["uuid"] = loggin.Uuid;

            String jsonString;
            serializeJson(doc, jsonString);
            webSocket.sendTXT(jsonString);
            Serial.printf("📤 Mensaje enviado: %s\n", jsonString.c_str());

            return;
        }
    }

    Serial.println("⚠️ No hay tareas en progreso para completar.");
}
