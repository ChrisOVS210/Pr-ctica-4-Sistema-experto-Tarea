#include <Arduino.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "model_params.h"

// Arduino UNO questionnaire front end. No model is trained on the board.
// Protocol at 115200 baud, newline-delimited ASCII:
// board: READY, ASK|id|prompt, DONE|v1,...,v10|score|class, or ERROR|reason
// host:  START, ANSWER|integer
// Keep the Serial Monitor closed while the Python program owns the USB port.

struct Question { const char *prompt; int low; int high; };
const Question Q[] = {
  {"Edad en anios (18-120)", 18, 120},
  {"Peso actual en kg (30-300)", 30, 300},
  {"Estatura en cm (120-230)", 120, 230},
  {"Dias con actividad fisica >=30 min por semana (0-7)", 0, 7},
  {"Horas sentado/a por dia (0-16)", 0, 16},
  {"Dias por semana que tomas bebidas azucaradas (0-7)", 0, 7},
  {"Porciones de frutas/verduras al dia (0-10)", 0, 10},
  {"Horas de sueno por noche (0-16)", 0, 16},
  {"Comidas rapidas o muy procesadas por semana (0-21)", 0, 21},
  {"Antecedentes familiares de obesidad? 0=no, 1=si, 2=prefiero no decir", 0, 2}
};
const int NQ = sizeof(Q) / sizeof(Q[0]);
int answers[NQ];
char lineBuf[40];

float sigmoid(float z) {
  if (z > 20.0f) return 1.0f;
  if (z < -20.0f) return 0.0f;
  return 1.0f / (1.0f + exp(-z));
}

bool modelScore(float *score) {
  // The attached academic CSV has labels but no documented provenance.
  // Use only matching fields: age, BMI, activity days, family history.
  if (answers[9] == 2) return false; // missing family-history value
  float x[MODEL_FEATURES];
  x[0] = (float)answers[0];
  float heightM = (float)answers[2] / 100.0f;
  x[1] = (float)answers[1] / (heightM * heightM);
  x[2] = (float)answers[3];
  x[3] = (float)answers[9];
  for (int j = 0; j < MODEL_FEATURES; ++j) {
    if (x[j] < MODEL_MIN[j] || x[j] > MODEL_MAX[j]) return false;
  }
  float z = MODEL_BIAS;
  for (int j = 0; j < MODEL_FEATURES; ++j) {
    z += MODEL_WEIGHT[j] * ((x[j] - MODEL_MEAN[j]) / MODEL_SCALE[j]);
  }
  *score = sigmoid(z);
  return true;
}

bool readLine() {
  static size_t n = 0;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') { lineBuf[n] = '\0'; n = 0; return true; }
    if (n < sizeof(lineBuf) - 1) lineBuf[n++] = c;
    else { n = 0; Serial.println("ERROR|line_too_long"); }
  }
  return false;
}

void setup() {
  Serial.begin(115200);
  Serial.println("READY");
}

void loop() {
  if (!readLine()) return;
  if (strcmp(lineBuf, "START") != 0) { Serial.println("ERROR|expected_START"); return; }
  for (int i = 0; i < NQ; ++i) {
    bool accepted = false;
    while (!accepted) {
      Serial.print("ASK|"); Serial.print(i + 1); Serial.print('|'); Serial.println(Q[i].prompt);
      while (!readLine()) { }
      if (strcmp(lineBuf, "CANCEL") == 0) { Serial.println("CANCELLED"); return; }
      // Accept protocol form ANSWER|18 and a plain integer for Serial Monitor tests.
      char *answerText = lineBuf;
      if (strncmp(lineBuf, "ANSWER|", 7) == 0) answerText = lineBuf + 7;
      char *endp = nullptr;
      long val = strtol(answerText, &endp, 10);
      if (endp == answerText || *endp != '\0' || val < Q[i].low || val > Q[i].high) {
        Serial.println("ERROR|answer_out_of_range"); continue;
      }
      answers[i] = (int)val; accepted = true;
    }
  }
  Serial.print("DONE|");
  for (int i = 0; i < NQ; ++i) { if (i) Serial.print(','); Serial.print(answers[i]); }
  float score;
  if (modelScore(&score)) {
    Serial.print('|'); Serial.print(score, 4); Serial.print('|');
    Serial.println(score >= 0.5f ? 1 : 0);
  } else {
    Serial.println("|NA|NA");
  }
}
