# Sistema de asignación de horarios

Programa que arma automáticamente el horario de una institución educativa: decide **qué día, a qué hora y en qué salón** se dicta cada clase.

## ¿Qué hace?

Se le entregan cuatro listas (profesores, cursos, salones y franjas horarias) y el programa busca un horario donde:

- Ningún profesor, grupo o salón tenga dos clases al mismo tiempo.
- En lo posible, se respeten las horas en que cada profesor **no** puede dar clase.
- En lo posible, los grupos no tengan demasiadas clases seguidas.

La regla de los choques nunca se rompe. Las preferencias se intentan cumplir, y si alguna no se puede, el horario "cuesta" más.

## ¿Cómo funciona?

El programa empieza con un horario vacío y va ubicando las clases una por una, probando las opciones posibles hasta completar el horario. Para recorrer esas opciones se pueden elegir cinco métodos de búsqueda:

- **Amplitud (BFS)**
- **Costo uniforme**
- **Profundidad iterativa**
- **A\* (h1)** y **A\* (h2)**

Algunos solo buscan un horario válido. Otros, como costo uniforme y A\*, buscan el horario que mejor respeta las preferencias. Al final, la ventana muestra el horario en una tabla y cuántos pasos y cuánto tiempo necesitó cada método.

## ¿Cómo ejecutarlo?

1. Tener instalado **Python 3**.
2. Abrir una terminal en la carpeta del proyecto y ejecutar:

   ```bash
   python3 interfaz.py
   ```

3. En la ventana, cargar los cuatro archivos. En la carpeta `txt/` hay unos de ejemplo.
4. Elegir el método de búsqueda y la cantidad de días, y presionar **Generar Horario**.

Para correr las pruebas automáticas:

```bash
python3 -m unittest test_parte_a
```

## Integrantes

- Santiago Andrey Morales Valencia
- Dilan Joseph Sanchez Silva
- Valentina Betancourt Caicedo
