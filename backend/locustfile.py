import queue
import json
import time
import random
from datetime import datetime, timezone
from locust import HttpUser, task, between, TaskSet

# ==========================================
# ⚙️ CONFIGURACIÓN DE REALISMO
# ==========================================
DURACION_MINIMA = 120   # 2 minutos reales
DURACION_MAXIMA = 300   # 5 minutos reales
# ==========================================

TOKENS = {}
try:
    with open('tokens.json', 'r') as f:
        TOKENS = json.load(f)
    print(f"📂 Cargados {len(TOKENS)} tokens.")
except:
    print("⚠️ tokens.json no encontrado")

DOCTOR_QUEUE = queue.Queue()
for user in TOKENS.keys():
    if user.startswith("medico_"):
        DOCTOR_QUEUE.put(user)

class MedicoTasks(TaskSet):
    def on_start(self):
        self.username = None
        self.consultas_activas = {} # Memoria local del médico
        try:
            self.username = DOCTOR_QUEUE.get(block=False)
            token = TOKENS.get(self.username)
            self.headers = {'Authorization': f'Token {token}'}
            print(f"✅ {self.username} conectado.")
        except queue.Empty:
            self.user.stop()

    @task
    def trabajar(self):
        if not self.username: return

        with self.client.get("/api/medico/atenciones/actual/", headers=self.headers, catch_response=True) as res:
            if not res.ok: return
            data = res.json()
            tipo = data.get('tipo')
            atencion = data.get('atencion')

            # 1. INICIAR (Si hay cita próxima)
            if tipo == 'proxima' and atencion:
                aid = atencion['id']
                r = self.client.post(
                    f"/api/medico/atenciones/{aid}/iniciar/",
                    headers=self.headers,
                    name="Iniciar Consulta"
                )
                if r.ok:
                    duracion = random.randint(DURACION_MINIMA, DURACION_MAXIMA)
                    self.consultas_activas[aid] = {'inicio': time.time(), 'meta': duracion}
                    print(f"🟢 {self.username} inicia consulta ({duracion}s).")

            # 2. FINALIZAR (Si ya pasó el tiempo)
            elif tipo == 'en_curso' and atencion:
                aid = atencion['id']
                datos_locales = self.consultas_activas.get(aid)
                
                # Si no tenemos datos locales (ej. reinicio), asumimos que empezó hace poco
                if not datos_locales:
                    self.consultas_activas[aid] = {'inicio': time.time(), 'meta': DURACION_MINIMA}
                    return

                tiempo_real = time.time() - datos_locales['inicio']
                
                if tiempo_real >= datos_locales['meta']:
                    self.client.post(
                        f"/api/medico/atenciones/{aid}/finalizar/",
                        json={"observaciones": f"Duración: {int(tiempo_real)}s"},
                        headers=self.headers,
                        name="Finalizar Consulta"
                    )
                    del self.consultas_activas[aid]
                    print(f"🔴 {self.username} finalizó ({int(tiempo_real)}s).")

    def on_stop(self):
        if self.username: DOCTOR_QUEUE.put(self.username)

class WebsiteUser(HttpUser):
    tasks = [MedicoTasks]
    wait_time = between(5, 15)