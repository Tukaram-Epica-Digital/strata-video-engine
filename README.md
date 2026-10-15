# strata-video-engine

Motor de render 3D **procedural en numpy puro** (sin OpenGL, sin motores
graficos) que genera los fotogramas del video explicativo del simulador Strata.

Copiado de `C:\almanaque\strata_video`.

## Como funciona

Se construye la geometria, se calcula su bounding box y la camara se ajusta para
que el cuadro quepa siempre en el area segura; despues se rotulan las piezas.
El guion compara reparto de pesos por capas (estilo Ollama / llama.cpp) contra
reparto por expertos (Strata).

| Modulo | Mision |
|---|---|
| `engine.py` | matematicas, mallas, camara `look_at`, splines, escritura PNG |
| `raster.py` | rasterizador con z-buffer + post (bloom, tonemap, vineta, grano) |
| `props.py` | piezas: placa base, GPU, CPU, RAM, SSD, tokens, paneles |
| `scenes.py` | guion animado y reparto de capas/expertos por fotograma |
| `framing.py` | `fit_view`: encuadre automatico segun bounding box |
| `labels.py`, `font.py` | texto y tipografia dibujada a mano |
| `bg.py`, `colmap.py`, `geo.py` | fondo, mapeado de color, geometria |
| `render.py` | render paralelo por procesos -> `f#####.png` |
| `preview.py`, `contact.py` | fotogramas sueltos y hoja de contacto |
| `validate.py`, `check_labels.py`, `test_labels.py` | comprobaciones |
| `diag.py`, `dbg.py`, `bench.py`, `hist.py`, `ascii.py` | diagnostico y medicion |
| `_patch1..13.py` | parches aplicados durante el desarrollo |

## Ejecutar

```bash
python -m pip install numpy
python render.py          # secuencia completa
python preview.py         # fotogramas de prueba
python contact.py         # hoja de contacto
```

`preview/` trae fotogramas de muestra ya generados.
