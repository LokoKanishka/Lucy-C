# Lucy Cross-Model Benchmark Results

Generated on: Sun Feb  1 15:22:00 2026

## Model: gpt-oss:20b
| Caso | Estado | Latencia | Respuesta Parcial |
|------|--------|----------|-------------------|
| identidad | ❌ | 5.0s | Soy Lucy, tu asistente virtual inteligente y de confianza, siempre a tu lado para lo que necesites.  

Hoy el clima se pinta con un cielo claro, pero ... |
| instruccion_compleja | ✅ | 3.85s | [[remember(postre_favorito, "vigilante")]]

[🧠 MEMORIA]: Recordado: postre_favorito = vigilante |
| memoria_corto_plazo | ✅ | 1.03s | Te dijo que tu postre favorito es vigilante. |

## Model: llama3.1:8b
| Caso | Estado | Latencia | Respuesta Parcial |
|------|--------|----------|-------------------|
| identidad | ❌ | 12.57s | ¡Hola! Soy Sos Lucy, tu asistente virtual inteligente y conversacional. Estoy aquí para ayudarte con cualquier cosa que necesites, desde respuestas té... |
| instruccion_compleja | ❌ | 0.16s | Lo siento, pero no puedo cumplir con esa solicitud. |
| memoria_corto_plazo | ❌ | 0.28s | Lo siento, pero no tengo información previa sobre qué conversación estabamos teniendo. ¿Querés empezar de cero y decime algo sobre lo que querés habla... |

## Model: dolphin-llama3:8b
| Caso | Estado | Latencia | Respuesta Parcial |
|------|--------|----------|-------------------|
| identidad | ❌ | 10.6s | Hola! Soy Sos Lucy, tu asistente virtual inteligente y conversacional. Estoy aquí para ayudarte en todo lo que necesites. En cuanto al pronóstico del ... |
| instruccion_compleja | ✅ | 0.15s | [[remember(vigilante, postre_favorito)]]

[🧠 MEMORIA]: Recordado: vigilante = postre_favorito |
| memoria_corto_plazo | ❌ | 0.21s | Recién, no me diste información sobre un postre favorito. ¿Quieres que crea una memoria para eso? |

