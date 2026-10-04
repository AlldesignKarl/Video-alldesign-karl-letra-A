# Pipeline de producción

Orden de ejecución (todo en CPU):

1. `sam_video.py`: segmentación de la letra en los 394 frames con SAM 2.1-L (prompt: `prompt_fwd.json`).
2. `rot2.py` y `vscale.py`: medidas por frame (anchura de la huella, eje y zoom de cámara por flujo óptico vertical).
3. `build_maps.py`: ángulo de giro por frame, transformaciones de estabilización (`xforms.json`) y retemporizado (`timemap.json`).
4. `sam_holes.py`: seguimiento del hueco de la "A" y de la abertura entre patas en la cara floral (prompt: `hole_prompt.json`).
5. `stageA1.py`: super-resolución ×4 (Real-ESRGAN general v3) de cada recorte.
6. `stageA2.py`: sprite estabilizado con alfa refinado (filtro guiado) y descontaminación de color de bordes.
7. `scene.py`: escena 3D del fondo (Blender/bpy 4.2, Cycles), más un pase de profundidad.
8. `stageB.py`: interpolación RIFE 4.25, dolly-in con paralaje por profundidad, sombras, etalonaje, grano y rótulos (`overlay.py`).
9. `tts_kokoro.py` y `build_voice.py`: locución. `music.py`: música (MIDI → FluidSynth, FluidR3_GM). `mix.py`: mezcla a -14 LUFS.
