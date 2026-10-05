import { pipeline, env } from '@huggingface/transformers';
import fs from 'fs';
env.allowRemoteModels = false;
env.localModelPath = './package/models/';
const asr = await pipeline('automatic-speech-recognition', 'Xenova/whisper-base', { dtype: 'q8', device: 'cpu' });
const buf = fs.readFileSync(process.argv[2]);
const audio = new Float32Array(buf.buffer, buf.byteOffset, buf.length / 4);
const out = await asr(audio, { language: 'spanish', task: 'transcribe', chunk_length_s: 30, return_timestamps: true });
console.log(JSON.stringify(out, null, 1));
