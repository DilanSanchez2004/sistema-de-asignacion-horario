
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk   

import cargador
from busquedas import ALGORITMOS
from problema import Problema


DIAS_DISPONIBLES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado"]
DIAS_DEFECTO = 3     
ARCHIVOS = [("profesores", "Cargar profesores.txt"),   
            ("cursos", "Cargar cursos.txt"),
            ("salones", "Cargar salones.txt"),
            ("franjas", "Cargar franjas.txt")]
COLOR_LIBRE = "#e6e6e6"      # gris: celda sin clase
COLOR_OCUPADA = "#cfe8ff"    # azul claro: celda con clase


class App:
    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        raiz.title("PROGRAMACION ACADEMICA UNIVERSITARIA")

      
        self.datos = {}         
        self.rutas = {}        
        self.estados = {}       
        self.filas_stats = {}    
        self._resultado = None  
        self._problema = None   
        self._dias = []        

        self._panel_carga()
        self._panel_config()
        self._panel_horario()
        self._panel_estadisticas()

    # ================= Paneles =================
    def _panel_carga(self):
       
        marco = ttk.LabelFrame(self.raiz, text="Archivos de entrada")
        marco.pack(fill="x", padx=8, pady=4)
        for fila, (clave, texto) in enumerate(ARCHIVOS):
            self.rutas[clave] = tk.StringVar(value="(sin cargar)")
            self.estados[clave] = tk.StringVar(value="")
            
            ttk.Button(marco, text=texto, width=22,
                       command=lambda c=clave: self._examinar(c)).grid(row=fila, column=0, padx=4, pady=2)
            ttk.Label(marco, textvariable=self.rutas[clave], width=50).grid(row=fila, column=1, sticky="w")
            ttk.Label(marco, textvariable=self.estados[clave]).grid(row=fila, column=2, sticky="w", padx=6)

    def _panel_config(self):
        
        marco = ttk.LabelFrame(self.raiz, text="Configuración")
        marco.pack(fill="x", padx=8, pady=4)
        ttk.Label(marco, text="Algoritmo:").pack(side="left", padx=4)
        self.algoritmo = tk.StringVar(value=list(ALGORITMOS)[0])
      
        ttk.Combobox(marco, textvariable=self.algoritmo, values=list(ALGORITMOS),
                     state="readonly", width=22).pack(side="left", padx=4)
        ttk.Label(marco, text="Máx. consecutivas (0 = sin límite):").pack(side="left", padx=8)
        self.max_consec = tk.IntVar(value=0)
        ttk.Spinbox(marco, from_=0, to=10, width=4, textvariable=self.max_consec).pack(side="left")
      
        ttk.Label(marco, text="Días:").pack(side="left", padx=8)
        self.n_dias = tk.IntVar(value=DIAS_DEFECTO)
        ttk.Spinbox(marco, from_=1, to=len(DIAS_DISPONIBLES), width=3,
                    textvariable=self.n_dias).pack(side="left")
        self.boton = ttk.Button(marco, text="Generar Horario", command=self._generar)
        self.boton.pack(side="left", padx=12)
        self.estado_ejec = tk.StringVar(value="")        
        ttk.Label(marco, textvariable=self.estado_ejec).pack(side="left")

    def _panel_horario(self):
       
        self.marco_horario = ttk.LabelFrame(self.raiz, text="HORARIO GENERADO")
        self.marco_horario.pack(fill="both", expand=True, padx=8, pady=4)
        ttk.Label(self.marco_horario, text="Cargue los 4 archivos y presione «Generar Horario».").pack(pady=20)

    def _panel_estadisticas(self):
        
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
       
        ruta = filedialog.askopenfilename(title=f"Seleccione {clave}.txt",
                                          filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if not ruta:
            return
        self.rutas[clave].set(ruta)
        try:
            self.datos[clave] = cargador.LECTORES[clave](ruta)
            self.estados[clave].set(f"✔ leído ({len(self.datos[clave])} registros)")
        except Exception as e:                         
            self.datos.pop(clave, None)              
            self.estados[clave].set(f"✖ error: {e}")

    # ================= Ejecución del algoritmo =================
    def _generar(self):
      
        faltan = [c for c, _ in ARCHIVOS if c not in self.datos]
        if faltan:
            messagebox.showwarning("Faltan archivos", "Cargue correctamente: " + ", ".join(faltan))
            return
        try:
            clases = cargador.construir_clases(self.datos["cursos"], self.datos["profesores"])
            limite = self.max_consec.get() or None    
            n_dias = self.n_dias.get()
            if not 1 <= n_dias <= len(DIAS_DISPONIBLES):
                raise ValueError(f"Los días deben estar entre 1 y {len(DIAS_DISPONIBLES)}")
            self._dias = DIAS_DISPONIBLES[:n_dias]   
            self._problema = Problema(clases, self._dias, self.datos["franjas"], self.datos["salones"],
                                      max_consecutivas=limite)
        except (ValueError, tk.TclError) as e:         
            messagebox.showerror("Datos inválidos", str(e))
            return

        funcion = ALGORITMOS[self.algoritmo.get()]    
        self.boton.config(state="disabled")          
        self.estado_ejec.set("Calculando...")
        self._resultado = None                         
       
        threading.Thread(target=lambda: self._correr(funcion), daemon=True).start()
        self.raiz.after(100, self._esperar)          

    def _correr(self, funcion):
        
        self._resultado = funcion(self._problema)

    def _esperar(self):
        
        if self._resultado is None:
            self.raiz.after(100, self._esperar)
            return
        self.boton.config(state="normal")
        self.estado_ejec.set("")
        self._mostrar_estadistica(self._resultado)
        self._dibujar_horario(self._resultado)

    # ================= Resultados =================
    def _mostrar_estadistica(self, r):
        
        solucion = "Sí" if r.encontrado else f"No ({r.motivo})"
        valores = (r.algoritmo, r.nodos_expandidos, f"{r.tiempo:.3f}s", solucion)
        if r.algoritmo in self.filas_stats:
            self.tabla.item(self.filas_stats[r.algoritmo], values=valores)
        else:
            self.filas_stats[r.algoritmo] = self.tabla.insert("", "end", values=valores)

    def _dibujar_horario(self, r):
       
        for w in self.marco_horario.winfo_children():
            w.destroy()
        if not r.encontrado:
            ttk.Label(self.marco_horario, text=f"Sin solución ({r.motivo})").pack(pady=10)
            return


        ocupadas = {}
        for c, a in self._problema.horario(r.estado):
            ocupadas.setdefault((a.dia, a.franja.id), []).append((c, a))
      
        max_clases = max((len(v) for v in ocupadas.values()), default=1)
        alto = 3 * max_clases + (max_clases - 1)

        for j in range(len(DIAS_DISPONIBLES) + 1):
            self.marco_horario.columnconfigure(j, weight=1 if j <= len(self._dias) else 0)
        ttk.Label(self.marco_horario, text="").grid(row=0, column=0)
        for j, dia in enumerate(self._dias, start=1):
            ttk.Label(self.marco_horario, text=dia, font=("TkDefaultFont", 10, "bold")).grid(row=0, column=j)
      
        for i, franja in enumerate(self._problema.franjas, start=1):
            ttk.Label(self.marco_horario, text=str(franja)).grid(row=i, column=0, padx=4)
            for j, dia in enumerate(self._dias, start=1):
                if (dia, franja.id) in ocupadas:
                    
                    bloques = [f"{c.nombre} ({c.grupo})\n{c.profesor.nombre}\n{a.salon.id}"
                               for c, a in ocupadas[(dia, franja.id)]]
                    texto, color = "\n──────────\n".join(bloques), COLOR_OCUPADA
                else:
                    texto, color = "", COLOR_LIBRE         # celda libre, en gris
                
                tk.Label(self.marco_horario, text=texto, bg=color, width=18, height=alto,
                         relief="groove").grid(row=i, column=j, padx=1, pady=1, sticky="nsew")


if __name__ == "__main__":
    raiz = tk.Tk()        
    App(raiz)             
    raiz.mainloop()       