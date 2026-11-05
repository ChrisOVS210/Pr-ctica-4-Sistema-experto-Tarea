# Encuesta + modelo ejecutado en Arduino UNO

## Qué hace esta versión

El UNO plantea 10 preguntas, calcula en el propio Arduino un puntaje de un modelo logístico pequeño y envía respuestas y resultado por USB. `host.py` conversa con el Arduino y guarda cada encuesta en `records.csv`. El ordenador se usa para entrenar/exportar los coeficientes una vez; la clasificación de cada nueva encuesta se calcula en el UNO.

El ZIP original documenta Arduino UNO y Python. Incluía un perceptrón entrenado en el Arduino a partir de filas que Python enviaba, además de `Obesidad.csv` con 297 filas y las columnas `Edad, Sexo, IMC, Actividad, Calorias, Antecedentes, Obesidad`. El origen y método de etiquetado de ese CSV no están documentados. Se incluye una copia para reproducir el ejercicio académico, con advertencia: el resultado no se debe interpretar como diagnóstico ni como rendimiento validado. El modelo usa solamente Edad, IMC, Actividad y Antecedentes, que se pueden derivar de las respuestas actuales. La escala de `Actividad` y el significado de las etiquetas deben confirmarse con quien proporcionó el dataset.

## Archivos

- `Arduino/ObesidadEducativa/ObesidadEducativa.ino`: cuestionario, validación y cálculo del modelo en el UNO.
- `Arduino/ObesidadEducativa/model_params.h`: coeficientes para Arduino, generados con el CSV de entrenamiento.
- `train_model.py`: entrena el modelo en Python y genera el archivo de coeficientes dentro de la carpeta del sketch.
- `Obesidad.csv`: conjunto académico incluido en el ZIP de origen.
- `host.py`: interfaz de preguntas por USB y guardado local de resultados.
- `requirements.txt`: dependencias para el anfitrión y el entrenamiento.

## Pasos para ejecutar

1. Extrae estos archivos en una sola carpeta.
2. Abre PowerShell en esa carpeta e instala dependencias: `python -m pip install -r requirements.txt`.
3. Entrena/exporta los coeficientes: `python train_model.py`. Esto genera o actualiza `Arduino/ObesidadEducativa/model_params.h`. Si el profesor proporciona otro CSV con etiquetas confiables, usa `python train_model.py ruta\datos.csv`; requiere columnas `Edad, IMC, Actividad, Antecedentes, Obesidad` y etiquetas 0/1.
4. Abre `Arduino/ObesidadEducativa/ObesidadEducativa.ino` en Arduino IDE. `model_params.h` está en la misma carpeta del sketch. Selecciona **Arduino UNO**, el puerto correcto y carga el sketch.
5. Cierra el Monitor Serie. Si Windows asignó un puerto distinto a COM5, configura `$env:ARDUINO_PORT="COM5"` en PowerShell, reemplazando el puerto por el correcto.
6. Ejecuta `python host.py survey`. Python abrirá el puerto; contesta las preguntas en la terminal. `host.py` guarda el resultado en `records.csv` junto a los archivos.

Para verificarlo manualmente en Monitor Serie, cierra primero Python, usa 115200 baudios, envía `START` y responde con números (una respuesta por línea). Al final el UNO muestra `DONE|...|puntaje|clase`. El Monitor Serie por sí solo no guarda un archivo; para persistir el registro ejecuta `host.py survey`.

## Variables del modelo

Las preguntas están en este orden: edad; peso kg; estatura cm; días de actividad física semanal; horas sentado/a al día; días con bebidas azucaradas; porciones de frutas/verduras; horas de sueño; comidas procesadas semanal; antecedentes familiares (0=no, 1=sí, 2=prefiero no decir).

El vector que usa el modelo es `[edad, IMC, actividad, antecedentes]`; el UNO deriva `IMC = peso / estatura_en_metros²`. Se omiten las demás respuestas para la inferencia porque no existen columnas compatibles en el CSV académico. Si se responde “prefiero no decir” en antecedentes o alguna variable sale del rango observado al entrenar, el UNO evita estimar y entrega `NA`.

El `puntaje` que devuelve Arduino es la salida logística del modelo, no una probabilidad clínica calibrada. `clase` es 0 o 1 según el objetivo del CSV usado. No significa diagnóstico de una persona. Las etiquetas y variables de origen se deben validar antes de cualquier interpretación; las métricas de un conjunto pequeño tampoco sustituyen una evaluación independiente.

## Privacidad y uso educativo

- Explica el propósito y pide consentimiento antes de guardar. No recolectes nombres, teléfonos ni datos identificadores.
- `records.csv` contiene respuestas de salud sensibles; mantenlo local, restringe su acceso y bórralo cuando ya no sea necesario. No lo subas a repositorios públicos.
- Esta práctica es para aprendizaje. No uses el puntaje para diagnosticar, tratar o tomar decisiones sobre personas. No recolectes datos de menores con este prototipo.
