##############################
# Agente Economico De IA v2  #
# Memoria persistente        #
##############################
#
# Cada chat se guarda como UN documento con:
#   - titulo y fecha de actualizacion
#   - resumen: memoria de largo plazo (lo viejo, resumido por el LLM)
#   - recientes: ultimos mensajes completos que se mandan al modelo
#   - pantalla: lo que se ve en la app (texto + datos para redibujar las graficas)
#
# El almacenamiento esta separado en su propia clase (AlmacenLocal). Asi, para
# pasar a Supabase solo hay que crear otra clase con los mismos 4 metodos.

import json
import os
from datetime import datetime


# =========================
# ALMACENAMIENTO
# =========================

class AlmacenLocal:
    """Guarda cada chat como un archivo JSON dentro de la carpeta 'historial'."""

    def __init__(self, carpeta):
        self.carpeta = carpeta
        os.makedirs(carpeta, exist_ok=True)

    def _ruta(self, chat_id):
        return os.path.join(self.carpeta, f"{chat_id}.json")

    def listar(self):
        """Lista de chats (id, titulo, actualizado), del mas reciente al mas viejo."""
        chats = []
        for archivo in os.listdir(self.carpeta):
            if not archivo.endswith(".json"):
                continue
            datos = self.cargar(archivo[:-5])
            if datos and datos.get("pantalla"):
                chats.append({
                    "id": datos["id"],
                    "titulo": datos.get("titulo", "Chat"),
                    "actualizado": datos.get("actualizado", ""),
                })
        return sorted(chats, key=lambda c: c["actualizado"], reverse=True)

    def cargar(self, chat_id):
        try:
            with open(self._ruta(chat_id), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def guardar(self, datos):
        ruta = self._ruta(datos["id"])
        temporal = ruta + ".tmp"
        with open(temporal, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
        os.replace(temporal, ruta)

    def eliminar(self, chat_id):
        try:
            os.remove(self._ruta(chat_id))
        except FileNotFoundError:
            pass


# =========================
# MEMORIA DE UN CHAT
# =========================

class MemoriaChat:
    """
    Memoria "infinita": el modelo siempre recibe los ultimos mensajes completos
    y, ademas, un resumen acumulado de todo lo anterior. Cuando los mensajes
    recientes pasan el limite, los mas viejos se resumen con el LLM y se
    integran al resumen. Nada se pierde: todo queda guardado en el almacen.
    """

    def __init__(self, client, almacen, chat_id=None, limite_recientes=10,
                 conservar_despues_de_resumir=4, modelo="openai/gpt-oss-120b"):
        self.client = client
        self.almacen = almacen
        self.limite_recientes = limite_recientes
        self.conservar = conservar_despues_de_resumir
        self.modelo = modelo

        datos = self.almacen.cargar(chat_id) if chat_id else None
        if datos:
            self.id = datos["id"]
            self.titulo = datos.get("titulo", "Chat")
            self.resumen = datos.get("resumen", "")
            self.recientes = datos.get("recientes", [])
            self.pantalla = datos.get("pantalla", [])
        else:
            self.id = datetime.now().strftime("%Y%m%d%H%M%S%f")
            self.titulo = "Nuevo chat"
            self.resumen = ""
            self.recientes = []
            self.pantalla = []

    # ---------- lo que usa la app ----------

    def mensajes_para_modelo(self):
        return list(self.recientes)

    def registrar_turno(self, pregunta, respuesta, visuales):
        """Guarda una pregunta y su respuesta (con los datos de las graficas)."""
        if not self.pantalla:
            titulo = " ".join(pregunta.split())
            self.titulo = titulo if len(titulo) <= 36 else titulo[:35].rstrip() + "…"

        self.pantalla.append({"role": "user", "content": pregunta, "visuales": []})
        self.pantalla.append({"role": "assistant", "content": respuesta, "visuales": visuales})

        self.recientes.append({"role": "user", "content": pregunta})
        self.recientes.append({"role": "assistant", "content": respuesta})
        if len(self.recientes) > self.limite_recientes:
            self._resumir_lo_viejo()

        self.guardar()

    def guardar(self):
        self.almacen.guardar({
            "id": self.id,
            "titulo": self.titulo,
            "actualizado": datetime.now().isoformat(timespec="seconds"),
            "resumen": self.resumen,
            "recientes": self.recientes,
            "pantalla": self.pantalla,
        })

    # ---------- resumen de largo plazo ----------

    def _resumir_lo_viejo(self):
        viejos = self.recientes[:-self.conservar]
        try:
            self.resumen = self._pedir_resumen(viejos)
            self.recientes = self.recientes[-self.conservar:]
        except Exception as e:
            # Si falla (por ejemplo por limite de Groq) no se pierde nada:
            # se vuelve a intentar en el siguiente mensaje.
            print(f"[MemoriaChat] No se pudo resumir: {e}")
            tope = self.limite_recientes * 3
            self.recientes = self.recientes[-tope:]

    def _pedir_resumen(self, mensajes):
        conversacion = "\n".join(
            f"{'Usuaria' if m['role'] == 'user' else 'Agente'}: {m['content'][:1200]}"
            for m in mensajes
        )
        prompt = (
            "Sos la memoria de un agente económico. Integrá la CONVERSACIÓN NUEVA "
            "al RESUMEN ANTERIOR y devolvé un solo resumen actualizado.\n"
            "- Español, máximo 150 palabras.\n"
            "- Conservá series de FRED consultadas, monedas, fechas, cifras clave "
            "y conclusiones.\n"
            "- No agregues nada que no esté en el texto.\n\n"
            f"RESUMEN ANTERIOR:\n{self.resumen or '(vacío)'}\n\n"
            f"CONVERSACIÓN NUEVA:\n{conversacion}\n\n"
            "Devolvé solo el resumen."
        )
        resp = self.client.chat.completions.create(
            model=self.modelo,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = (resp.choices[0].message.content or "").strip()
        if not texto:
            raise ValueError("Resumen vacío")
        return texto
