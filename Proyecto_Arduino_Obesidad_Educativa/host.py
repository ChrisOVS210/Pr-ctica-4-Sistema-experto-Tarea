"""USB capture and local CSV logger for the Arduino UNO demo."""
import csv
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import serial

BASE = Path(__file__).resolve().parent
DATA = BASE / "records.csv"
PORT = os.environ.get("ARDUINO_PORT", "COM5")
BAUD = 115200

def read_line(ser, timeout=60):
    until = time.time() + timeout
    while time.time() < until:
        raw = ser.readline()
        if raw:
            msg = raw.decode("utf-8", errors="replace").strip()
            if msg:
                print("Arduino:", msg)
                return msg
    raise TimeoutError("Sin respuesta del Arduino; revisa cable, puerto y que el Monitor Serie esté cerrado.")

def survey():
    print("Cuestionario educativo voluntario. No es diagnóstico médico.")
    print("No ingreses nombre, teléfono ni otro identificador personal.\n")
    fields = ["record_id", "captured_at", "age_years", "weight_kg", "height_cm",
              "activity_days_week", "sitting_hours_day", "sugary_drink_days_week",
              "fruit_veg_servings_day", "sleep_hours_night", "processed_meals_week",
              "family_history", "model_score", "model_class"]
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        # Opening the USB port resets many UNO boards. Do not clear the buffer:
        # READY is printed at boot and must remain available for the host.
        time.sleep(2)
        deadline = time.time() + 8
        ready = False
        while time.time() < deadline:
            msg = ser.readline().decode(errors="replace").strip()
            if msg == "READY":
                ready = True
                break
        if not ready:
            raise TimeoutError("El Arduino no envió READY. Verifica el sketch y reinicia la placa.")
        ser.write(b"START\n")
        while True:
            msg = read_line(ser)
            if msg == "CANCELLED":
                print("Encuesta cancelada; no se guardó.")
                return
            if msg.startswith("ASK|") or msg.startswith("Pregunta|"):
                # Python is the respondent interface; Arduino validates and keeps the input.
                parts = msg.split("|", 2)
                qid = int(parts[1])
                prompt = parts[2] if len(parts) > 2 else f"Pregunta {qid}"
                val = input(f"{qid}/10. {prompt} (salir para cancelar): ").strip()
                if val.lower() == "salir":
                    ser.write(b"CANCEL\n")
                    continue
                if not val.isdigit():
                    print("Escribe un número entero.")
                    ser.write(b"ANSWER|invalid\n")
                else:
                    ser.write(f"ANSWER|{val}\n".encode())
                continue
            if msg.startswith("ERROR|"):
                print("Arduino rechazó la respuesta; vuelve a contestar.")
                continue
            if msg.startswith("DONE|"):
                parts = msg.split("|")
                if len(parts) != 4:
                    raise RuntimeError("Formato DONE incompleto; vuelve a cargar el sketch actualizado.")
                vals = [int(x) for x in parts[1].split(",")]
                if len(vals) != 10:
                    raise RuntimeError("Arduino no devolvió las diez respuestas.")
                score = "" if parts[2] == "NA" else parts[2]
                model_class = "" if parts[3] == "NA" else parts[3]
                break
    row = dict(zip(fields[2:12], vals))
    row.update(record_id=str(uuid.uuid4()), captured_at=datetime.now(timezone.utc).isoformat(),
               model_score=score, model_class=model_class)
    exists = DATA.exists()
    with DATA.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    print("Registro guardado en", DATA)
    if score:
        print(f"Puntaje del modelo académico en Arduino: {float(score):.1%}; clase estimada: {model_class}.")
    elif vals[9] == 2:
        print("El modelo no calculó puntaje porque se eligió 'prefiero no decir' en antecedentes familiares.")
    else:
        print("El modelo no calculó puntaje porque una variable quedó fuera del rango del conjunto de entrenamiento.")
    print("Demostración educativa; no es una probabilidad clínica ni un diagnóstico.")

if __name__ == "__main__":
    try:
        if len(sys.argv) != 2 or sys.argv[1] != "survey":
            print("Uso: python host.py survey")
            sys.exit(2)
        survey()
    except (ValueError, RuntimeError, TimeoutError, serial.SerialException) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)
