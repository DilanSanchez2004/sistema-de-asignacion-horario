import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk   # ttk = widgets con aspecto moderno

import cargador
from busquedas import ALGORITMOS
from problema import Problema

# [CLAVE 1] Constantes de configuración. No hay archivo de días, por eso se fijan aquí.
DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
ARCHIVOS = [("profesores", "Cargar profesores.txt"),   # (clave, texto del botón)
            ("cursos", "Cargar cursos.txt"),
            ("salones", "Cargar salones.txt"),
            ("franjas", "Cargar franjas.txt")]
COLOR_LIBRE = "#e6e6e6"      # gris: celda sin clase
COLOR_OCUPADA = "#cfe8ff"    # azul claro: celda con clase


class App:
    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        raiz.title("PROGRAMACION ACADEMICA UNIVERSITARIA")

        # [CLAVE 2] Estado de la aplicación (todo lo que la ventana "recuerda"):
        self.datos = {}          # clave -> lo que devolvió el lector (profesores, cursos, ...)
        self.rutas = {}          # clave -> StringVar con la ruta mostrada
        self.estados = {}        # clave -> StringVar con "✔ leído" o el error
        self.filas_stats = {}    # nombre de algoritmo -> id de su fila en la tabla de estadísticas
        self._resultado = None   # lo escribe el hilo del algoritmo, lo lee el hilo principal
        self._problema = None    # Problema construido en la última ejecución (lo necesita la grilla)

        # Se construyen los 4 paneles en el orden en que aparecen en pantalla
        self._panel_carga()
        self._panel_config()
        self._panel_horario()
        self._panel_estadisticas()

    # ================= Paneles =================
    def _panel_carga(self):
        """[CLAVE 3] Panel 1: una fila por archivo con [botón] [ruta] [estado].
        StringVar es una variable "observable": si cambias su valor con .set(),
        el Label que la usa (textvariable=...) se actualiza solo."""
        marco = ttk.LabelFrame(self.raiz, text="Archivos de entrada")
        marco.pack(fill="x", padx=8, pady=4)
        for fila, (clave, texto) in enumerate(ARCHIVOS):
            self.rutas[clave] = tk.StringVar(value="(sin cargar)")
            self.estados[clave] = tk.StringVar(value="")
            # [CLAVE 4] lambda c=clave: truco para "congelar" la clave de ESTA
            # iteración. Sin "c=clave", los 4 botones llamarían con la última clave.
            ttk.Button(marco, text=texto, width=22,
                       command=lambda c=clave: self._examinar(c)).grid(row=fila, column=0, padx=4, pady=2)
            ttk.Label(marco, textvariable=self.rutas[clave], width=50).grid(row=fila, column=1, sticky="w")
            ttk.Label(marco, textvariable=self.estados[clave]).grid(row=fila, column=2, sticky="w", padx=6)

    def _panel_config(self):
        """Panel 2: combobox de algoritmo, spinbox de consecutivas y botón."""
        marco = ttk.LabelFrame(self.raiz, text="Configuración")
        marco.pack(fill="x", padx=8, pady=4)
        ttk.Label(marco, text="Algoritmo:").pack(side="left", padx=4)
        self.algoritmo = tk.StringVar(value=list(ALGORITMOS)[0])
        # [CLAVE 5] Los valores del combobox salen de las llaves de ALGORITMOS
        # (busquedas.py). Cuando se registren DFS/IDS/A* allá, aparecen solos.
        # state="readonly": el usuario elige de la lista, no escribe.
        ttk.Combobox(marco, textvariable=self.algoritmo, values=list(ALGORITMOS),
                     state="readonly", width=22).pack(side="left", padx=4)
        ttk.Label(marco, text="Máx. clases consecutivas (0 = sin límite):").pack(side="left", padx=8)
        self.max_consec = tk.IntVar(value=0)
        ttk.Spinbox(marco, from_=0, to=10, width=4, textvariable=self.max_consec).pack(side="left")
        self.boton = ttk.Button(marco, text="Generar Horario", command=self._generar)
        self.boton.pack(side="left", padx=12)
        self.estado_ejec = tk.StringVar(value="")        # muestra "Calculando..."
        ttk.Label(marco, textvariable=self.estado_ejec).pack(side="left")

    def _panel_horario(self):
        """Panel 3: solo crea el contenedor vacío; la grilla se dibuja en _dibujar_horario."""
        self.marco_horario = ttk.LabelFrame(self.raiz, text="HORARIO GENERADO")
        self.marco_horario.pack(fill="both", expand=True, padx=8, pady=4)

    def _panel_estadisticas(self):
        """Panel 4: Treeview = tabla de Tkinter. show="headings" oculta la columna
        de árbol y deja solo los encabezados."""
        marco = ttk.LabelFrame(self.raiz, text="ESTADISTICAS")
        marco.pack(fill="x", padx=8, pady=4)
        cols = ("algoritmo", "nodos", "tiempo", "solucion")
        self.tabla = ttk.Treeview(marco, columns=cols, show="headings", height=5)
        for c, t, w in zip(cols, ("Algoritmo", "Nodos explorados", "Tiempo", "Solución"),
                           (180, 130, 100, 180)):
            self.tabla.heading(c, text=t)
            self.tabla.column(c, width=w, anchor="center")
        self.tabla.pack(fill="x", padx=4, pady=4)

    # ================= Carga de archivos =================
    def _examinar(self, clave: str):
        """[CLAVE 6] Se ejecuta al presionar cualquiera de los 4 botones "Cargar".
        1) askopenfilename abre el explorador de archivos.
        2) Si el usuario cancela, devuelve "" y no se hace nada.
        3) Se intenta leer con el lector de esa clave (LECTORES[clave]).
        4) Éxito -> se guarda en self.datos y se muestra " leido (n registros)".
           Fallo -> se borra lo anterior y se muestra el error junto al botón."""
        ruta = filedialog.askopenfilename(title=f"Seleccione {clave}.txt",
                                          filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if not ruta:
            return
        self.rutas[clave].set(ruta)
        try:
            self.datos[clave] = cargador.LECTORES[clave](ruta)
            self.estados[clave].set(f"leido ({len(self.datos[clave])} registros)")
        except Exception as e:                         # formato inválido, archivo ilegible, etc.
            self.datos.pop(clave, None)                #verifica que no quede un dato viejo como si fuera válido
            self.estados[clave].set(f"error: {e}")

    # ================= Ejecución del algoritmo =================
    def _generar(self):
        """[CLAVE 7] Se ejecuta al presionar "Generar Horario". Pasos:
        a) Verificar que los 4 archivos estén cargados y sean válidos.
        b) Construir las Clase y el Problema (puede lanzar ValueError).
        c) Lanzar el algoritmo elegido en un HILO APARTE.
        d) Programar _esperar para recoger el resultado cuando termine."""
        faltan = [c for c, _ in ARCHIVOS if c not in self.datos]
        if faltan:
            messagebox.showwarning("Faltan archivos", "Cargue correctamente: " + ", ".join(faltan))
            return
        try:
            clases = cargador.construir_clases(self.datos["cursos"], self.datos["profesores"])
            limite = self.max_consec.get() or None     # 0 -> None = restricción blanda desactivada
            self._problema = Problema(clases, DIAS, self.datos["franjas"], self.datos["salones"],
                                      max_consecutivas=limite)
        except (ValueError, tk.TclError) as e:         # TclError: el spinbox tenía texto no numérico
            messagebox.showerror("Datos invalidos", str(e))
            return

        funcion = ALGORITMOS[self.algoritmo.get()]     # nombre elegido -> función de búsqueda
        self.boton.config(state="disabled")            # evita lanzar dos búsquedas a la vez
        self.estado_ejec.set("Calculando...")
        self._resultado = None                         # se usa None como señal de "aún no termina"
        # [CLAVE 8] ¿Por qué un hilo? BFS/UCS pueden tardar hasta 30 s. Si corrieran
        # en el hilo principal, Tkinter no podría redibujar y la ventana quedaría
        # "No responde". daemon=True: si se cierra la ventana, el hilo no la retiene.
        threading.Thread(target=lambda: self._correr(funcion), daemon=True).start()
        self.raiz.after(100, self._esperar)            # el hilo principal vuelve a mirar en 100 ms

    def _correr(self, funcion):
        """[CLAVE 9] Corre en el hilo secundario. REGLA: aquí NO se tocan widgets
        (Tkinter no es seguro entre hilos); solo se guarda el resultado."""
        self._resultado = funcion(self._problema)

    def _esperar(self):
        """[CLAVE 10] Polling con after(): cada 100 ms el hilo principal revisa si el
        resultado ya llegó. Si no, se vuelve a programar; si sí, se actualiza la
        pantalla. Esto no bloquea la ventana, que sigue respondiendo mientras tanto."""
        if self._resultado is None:
            self.raiz.after(100, self._esperar)
            return
        self.boton.config(state="normal")
        self.estado_ejec.set("")
        self._mostrar_estadistica(self._resultado)
        self._dibujar_horario(self._resultado)

    # ================= Resultados =================
    def _mostrar_estadistica(self, r):
        """[CLAVE 11] Una fila por algoritmo, como el boceto del enunciado. filas_stats
        recuerda el id de fila de cada algoritmo: si se vuelve a ejecutar, se
        ACTUALIZA esa fila (item) en vez de agregar otra (insert).
        Si no hubo solución se muestra el motivo (limite_tiempo, sin_solucion...)."""
        solucion = "Si" if r.encontrado else f"No ({r.motivo})"
        valores = (r.algoritmo, r.nodos_expandidos, f"{r.tiempo:.3f}s", solucion)
        if r.algoritmo in self.filas_stats:
            self.tabla.item(self.filas_stats[r.algoritmo], values=valores)
        else:
            self.filas_stats[r.algoritmo] = self.tabla.insert("", "end", values=valores)

    def _dibujar_horario(self, r):
        """[CLAVE 12] Dibuja la grilla: filas = franjas, columnas = días."""
        # Primero se destruyen los widgets de la grilla anterior (si no, se encimarían)
        for w in self.marco_horario.winfo_children():
            w.destroy()
        if not r.encontrado:
            ttk.Label(self.marco_horario, text=f"Sin solución ({r.motivo})").pack(pady=10)
            return

        # [CLAVE 13] Diccionario (día, id_franja) -> (clase, asignación). Sirve para
        # preguntar "¿qué hay en esta celda?" en una sola consulta en vez de recorrer
        # todas las clases por cada celda. Las celdas que no estén aquí quedan libres.
        ocupadas = {(a.dia, a.franja.id): (c, a) for c, a in self._problema.horario(r.estado)}

        # Fila 0 = encabezados de días (la columna 0 queda vacía para las horas)
        ttk.Label(self.marco_horario, text="").grid(row=0, column=0)
        for j, dia in enumerate(DIAS, start=1):
            ttk.Label(self.marco_horario, text=dia, font=("TkDefaultFont", 10, "bold")).grid(row=0, column=j)
        # Filas 1..n = una por franja; columna 0 = hora; columnas 1..5 = una por día
        for i, franja in enumerate(self._problema.franjas, start=1):
            ttk.Label(self.marco_horario, text=str(franja)).grid(row=i, column=0, padx=4)
            for j, dia in enumerate(DIAS, start=1):
                if (dia, franja.id) in ocupadas:
                    c, a = ocupadas[(dia, franja.id)]
                    # Materia, profesor y salón (lo que pide el enunciado), azul
                    texto, color = f"{c.nombre}\n{c.profesor.nombre}\n{a.salon.id}", COLOR_OCUPADA
                else:
                    texto, color = "", COLOR_LIBRE         # celda libre, en gris
                # tk.Label (no ttk) porque ttk.Label no permite cambiar el fondo con bg=
                tk.Label(self.marco_horario, text=texto, bg=color, width=18, height=4,
                         relief="groove").grid(row=i, column=j, padx=1, pady=1, sticky="nsew")


if __name__ == "__main__":
    raiz = tk.Tk()        # ventana principal
    App(raiz)             # construye todos los paneles
    raiz.mainloop()       # bucle de eventos: mantiene la ventana viva hasta que se cierre
