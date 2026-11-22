import { useCallback, useEffect, useRef, useState } from "react";

const AUTO_READ_KEY = "chitragupta_ai_autoread";

function getSpeechRecognitionCtor() {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function stripMarkdownForSpeech(text) {
  return String(text || "")
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/[*_#`~>-]+/g, " ")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

function pickPreferredVoice() {
  if (typeof window === "undefined" || !window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices() || [];
  if (!voices.length) return null;
  return (
    voices.find((v) => v.lang?.toLowerCase() === "en-in") ||
    voices.find((v) => v.lang?.toLowerCase().startsWith("en-")) ||
    voices[0]
  );
}

export function useVoiceAssistant() {
  const sttSupported = Boolean(getSpeechRecognitionCtor());
  const ttsSupported = typeof window !== "undefined" && "speechSynthesis" in window;

  const [voiceState, setVoiceState] = useState(sttSupported ? "ready" : "unavailable");
  const [voiceError, setVoiceError] = useState("");
  const [speakingId, setSpeakingId] = useState(null);
  const [autoRead, setAutoReadState] = useState(() => {
    try {
      return localStorage.getItem(AUTO_READ_KEY) === "true";
    } catch {
      return false;
    }
  });

  const recognitionRef = useRef(null);

  const setAutoRead = useCallback((next) => {
    setAutoReadState(Boolean(next));
    try {
      localStorage.setItem(AUTO_READ_KEY, String(Boolean(next)));
    } catch {
      // ignore storage errors
    }
  }, []);

  const stopSpeaking = useCallback(() => {
    if (!ttsSupported) return;
    try {
      window.speechSynthesis.cancel();
    } catch {
      // ignore synthesis errors
    }
    setSpeakingId(null);
  }, [ttsSupported]);

  const speak = useCallback(
    (messageId, rawText) => {
      if (!ttsSupported) return;
      const clean = stripMarkdownForSpeech(rawText);
      if (!clean) return;
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(clean);
        const voice = pickPreferredVoice();
        if (voice) utterance.voice = voice;
        utterance.lang = voice?.lang || "en-IN";
        utterance.rate = 1.0;
        utterance.onend = () => setSpeakingId(null);
        utterance.onerror = () => setSpeakingId(null);
        setSpeakingId(messageId);
        window.speechSynthesis.speak(utterance);
      } catch {
        setSpeakingId(null);
      }
    },
    [ttsSupported]
  );

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore stop errors
      }
    }
  }, []);

  const startListening = useCallback(
    (onTranscript) => {
      const Ctor = getSpeechRecognitionCtor();
      if (!Ctor) {
        setVoiceState("unavailable");
        setVoiceError("Voice input is not supported in this browser.");
        return;
      }

      stopSpeaking();
      setVoiceError("");

      try {
        const recognition = new Ctor();
        recognition.lang = "en-IN";
        recognition.interimResults = true;
        recognition.continuous = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
          setVoiceState("listening");
        };

        recognition.onresult = (event) => {
          setVoiceState("processing");
          let transcript = "";
          for (let i = 0; i < event.results.length; i += 1) {
            transcript += event.results[i][0].transcript;
          }
          if (transcript.trim()) {
            onTranscript(transcript.trim());
          }
        };

        recognition.onerror = (event) => {
          const code = event?.error;
          if (code === "not-allowed" || code === "service-not-allowed") {
            setVoiceState("denied");
            setVoiceError("Microphone permission was denied. Please allow microphone access in browser settings.");
          } else if (code === "no-speech") {
            setVoiceState("ready");
            setVoiceError("No speech detected. Please try again.");
          } else {
            setVoiceState("ready");
            setVoiceError("Voice recognition could not complete. You can type your question normally.");
          }
        };

        recognition.onend = () => {
          setVoiceState((current) => (current === "denied" || current === "unavailable" ? current : "ready"));
          recognitionRef.current = null;
        };

        recognitionRef.current = recognition;
        recognition.start();
      } catch {
        setVoiceState("ready");
        setVoiceError("Could not start microphone capture.");
      }
    },
    [stopSpeaking]
  );

  useEffect(() => {
    return () => {
      stopListening();
      stopSpeaking();
    };
  }, [stopListening, stopSpeaking]);

  return {
    sttSupported,
    ttsSupported,
    voiceState,
    voiceError,
    startListening,
    stopListening,
    speakingId,
    speak,
    stopSpeaking,
    autoRead,
    setAutoRead,
  };
}
