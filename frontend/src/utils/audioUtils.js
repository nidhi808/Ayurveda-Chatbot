/**
 * Audio conversion utilities for whisper.cpp.
 * Converts browser MediaRecorder blobs (WebM/Opus) into 16kHz 16-bit mono RIFF WAV files,
 * ensuring 100% native compatibility with whisper.cpp without requiring server-side ffmpeg.
 */

export async function convertBlobTo16kHzWav(audioBlob) {
  try {
    const arrayBuffer = await audioBlob.arrayBuffer();
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    const OfflineContextClass = window.OfflineAudioContext || window.webkitOfflineAudioContext;

    if (!AudioContextClass || !OfflineContextClass) {
      return audioBlob;
    }

    const tempCtx = new AudioContextClass();
    const decodedBuffer = await tempCtx.decodeAudioData(arrayBuffer);
    await tempCtx.close();

    const targetSampleRate = 16000;
    const numFrames = Math.max(1, Math.ceil(decodedBuffer.duration * targetSampleRate));
    const offlineCtx = new OfflineContextClass(1, numFrames, targetSampleRate);

    const source = offlineCtx.createBufferSource();
    source.buffer = decodedBuffer;
    source.connect(offlineCtx.destination);
    source.start(0);

    const resampledBuffer = await offlineCtx.startRendering();
    return audioBufferToWav(resampledBuffer);
  } catch (err) {
    console.warn("[audioUtils] AudioContext conversion fallback:", err);
    return audioBlob;
  }
}

function audioBufferToWav(buffer) {
  const targetSampleRate = 16000;
  const inputData = buffer.getChannelData(0);

  // 44-byte standard RIFF WAVE header + 16-bit samples
  const wavBuffer = new ArrayBuffer(44 + inputData.length * 2);
  const view = new DataView(wavBuffer);

  // 1. RIFF Chunk Descriptor
  writeAsciiString(view, 0, "RIFF");
  view.setUint32(4, 36 + inputData.length * 2, true); // File size - 8
  writeAsciiString(view, 8, "WAVE");

  // 2. fmt sub-chunk
  writeAsciiString(view, 12, "fmt ");
  view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
  view.setUint16(20, 1, true);  // AudioFormat (1 for PCM)
  view.setUint16(22, 1, true);  // NumChannels (1 = Mono)
  view.setUint32(24, targetSampleRate, true); // SampleRate (16000)
  view.setUint32(28, targetSampleRate * 1 * 2, true); // ByteRate (16000 * 1 * 2 bytes)
  view.setUint16(32, 2, true);  // BlockAlign (1 * 16/8)
  view.setUint16(34, 16, true); // BitsPerSample (16 bits)

  // 3. data sub-chunk
  writeAsciiString(view, 36, "data");
  view.setUint32(40, inputData.length * 2, true); // Data size

  // Write 16-bit PCM integer samples
  let offset = 44;
  for (let i = 0; i < inputData.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, inputData[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return new Blob([view], { type: "audio/wav" });
}

function writeAsciiString(view, offset, string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}
