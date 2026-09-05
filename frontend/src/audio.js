// Voice helpers: microphone capture, browser speech recognition, and read-aloud. Which path
// is used depends on /api/voice (server-side vs browser providers).
//
// Recordings are uploaded in the browser's native format (WebM/Opus in Chrome and Firefox,
// MP4/AAC in Safari) and converted on the server. Decoding them here with the Web Audio API
// is not reliable: Chrome rejects its own MediaRecorder output ("Unable to decode audio
// data") because a live recording carries no duration header.

export function canRecord() {
  return typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined";
}

export function browserRecognitionAvailable() {
  return typeof window !== "undefined" && !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

export function canSpeak() {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

const RECORDING_TYPES = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus", "audio/ogg"];

/**
 * Start recording. Returns a controller: stop() → Blob in the browser's native format,
 * cancel() to discard, level() → current microphone loudness 0..1 for the live waveform,
 * startedAt for the timer.
 */
export async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mime = RECORDING_TYPES.find((m) => MediaRecorder.isTypeSupported?.(m));
  const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
  const chunks = [];
  recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  const stopped = new Promise((resolve) => (recorder.onstop = resolve));
  recorder.start();
  const meter = createMeter(stream);
  const release = () => {
    stream.getTracks().forEach((t) => t.stop());
    meter.close();
  };
  return {
    startedAt: Date.now(),
    level: meter.level,
    async stop() {
      recorder.stop();
      await stopped;
      release();
      return new Blob(chunks, { type: recorder.mimeType || mime || "application/octet-stream" });
    },
    cancel() {
      try {
        recorder.stop();
      } catch {
        // already stopped
      }
      release();
    },
  };
}

// Taps the microphone stream for a loudness reading (nothing is connected to the speakers).
// Purely cosmetic: if the Web Audio API is unavailable the waveform just stays flat.
function createMeter(stream) {
  let ctx = null;
  let analyser = null;
  let samples = null;
  try {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    analyser.smoothingTimeConstant = 0.5;
    ctx.createMediaStreamSource(stream).connect(analyser);
    samples = new Uint8Array(analyser.fftSize);
    ctx.resume?.();
  } catch {
    analyser = null;
  }
  return {
    level() {
      if (!analyser) return 0;
      analyser.getByteTimeDomainData(samples);
      let sum = 0;
      for (let i = 0; i < samples.length; i++) {
        const x = (samples[i] - 128) / 128;
        sum += x * x;
      }
      return Math.min(1, Math.sqrt(sum / samples.length) * 4); // RMS, boosted for speech levels
    },
    close() {
      ctx?.close?.();
    },
  };
}

/** A filename whose extension matches the blob's type — some transcription APIs sniff it. */
export function recordingFilename(blob) {
  const type = (blob.type || "").split(";")[0].trim();
  const ext =
    { "audio/webm": "webm", "audio/mp4": "m4a", "audio/ogg": "ogg", "audio/wav": "wav", "audio/x-wav": "wav", "audio/mpeg": "mp3" }[type] || "bin";
  return `speech.${ext}`;
}

/** Browser-side recognition (Web Speech API). Resolves with the final transcript. */
export function recognizeInBrowser({ language = "en-IN", onInterim } = {}) {
  const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new Ctor();
  rec.lang = language;
  rec.interimResults = true;
  rec.continuous = false;
  let final = "";
  const done = new Promise((resolve, reject) => {
    rec.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) final += t;
        else interim += t;
      }
      onInterim?.(final + interim);
    };
    rec.onerror = (e) => reject(new Error(e.error || "speech recognition failed"));
    rec.onend = () => resolve(final.trim());
  });
  rec.start();
  return { done, stop: () => rec.stop(), cancel: () => rec.abort() };
}

/** Read text aloud with the browser's own voices. Returns a stop() function. */
export function speakInBrowser(text, { language = "en-IN" } = {}) {
  const u = new SpeechSynthesisUtterance(text);
  u.lang = language;
  const voices = window.speechSynthesis.getVoices();
  u.voice = voices.find((v) => v.lang === language) || voices.find((v) => v.lang.startsWith("en")) || null;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
  return () => window.speechSynthesis.cancel();
}

/** The answer as speech-friendly plain text: the direct answer, without the reasoning block. */
export function speakableText(answerText) {
  const cut = answerText.indexOf("\nReasoning:");
  const body = cut === -1 ? answerText : answerText.slice(0, cut);
  return body
    .replace(/\(offline mode[^)]*\)/g, "")
    .replace(/[*_`#>]/g, "")
    .replace(/^\s*[-•]\s*/gm, "")
    .replace(/\s+\n/g, "\n")
    .trim();
}
