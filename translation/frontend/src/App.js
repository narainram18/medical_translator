import React, { useState, useEffect, useCallback, useRef } from "react";
// The CSS file is provided separately and doesn't need to be imported here.
import "./App.css";

// --- Language Data ---
const languages = {
  English: "en",
  Hindi: "hi",
  Spanish: "es",
  French: "fr",
  German: "de",
  Arabic: "ar",
  Bengali: "bn",
  Chinese: "zh",
  "Chinese (Traditional)": "zt",
  Japanese: "ja",
  Korean: "ko",
  Russian: "ru",
  Portuguese: "pt",
  "Portuguese (Brazil)": "pb",
  Italian: "it",
  Dutch: "nl",
  Turkish: "tr",
  Albanian: "sq",
  Azerbaijani: "az",
  Basque: "eu",
  Bulgarian: "bg",
  Catalan: "ca",
  Czech: "cs",
  Danish: "da",
  Esperanto: "eo",
  Estonian: "et",
  Finnish: "fi",
  Galician: "gl",
  Greek: "el",
  Hebrew: "he",
  Hungarian: "hu",
  Indonesian: "id",
  Irish: "ga",
  Kyrgyz: "ky",
  Latvian: "lv",
  Lithuanian: "lt",
  Malay: "ms",
  Norwegian: "nb",
  Persian: "fa",
  Polish: "pl",
  Romanian: "ro",
  Slovak: "sk",
  Slovenian: "sl",
  Swedish: "sv",
  Tagalog: "tl",
  Thai: "th",
  Ukrainian: "uk",
  Urdu: "ur",
};

const speechRecognitionLangCodes = {
  en: "en-US",
  hi: "hi-IN",
  es: "es-ES",
  fr: "fr-FR",
  de: "de-DE",
  ar: "ar-SA",
  bn: "bn-IN",
  zh: "zh-CN",
  zt: "zh-TW",
  ja: "ja-JP",
  ko: "ko-KR",
  ru: "ru-RU",
  pt: "pt-PT",
  pb: "pt-BR",
  it: "it-IT",
  nl: "nl-NL",
  tr: "tr-TR",
};

// --- Custom Hook: Debounce ---
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

// --- Main App Component ---
function App() {
  const [history, setHistory] = useState([]);
  const [currentChat, setCurrentChat] = useState([
    {
      id: "welcome",
      text: "Welcome! Translate text or upload a prescription.",
      sender: "bot",
      lang: "en",
      keywords: [],
      recommendations: [],
      visualAid: null,
    },
  ]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [activeVisualAid, setActiveVisualAid] = useState(null);
  const [visualAidModalUrl, setVisualAidModalUrl] = useState(null);
  const [inputText, setInputText] = useState("");
  const [inputLang, setInputLang] = useState("en");
  const [targetLang, setTargetLang] = useState("hi");
  const [isListening, setIsListening] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [speakingMessageId, setSpeakingMessageId] = useState(null);
  const [signLanguageText, setSignLanguageText] = useState(null);
  const [visibleRecommendations, setVisibleRecommendations] = useState({});
  const [voices, setVoices] = useState([]);

  const debouncedInputText = useDebounce(inputText, 1000);
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const loadVoices = () => setVoices(window.speechSynthesis.getVoices());
    window.speechSynthesis.onvoiceschanged = loadVoices;
    loadVoices();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentChat, isTranslating]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputText]);

  useEffect(() => {
    const detectLanguage = async () => {
      if (debouncedInputText.trim().length > 10) {
        try {
          const res = await fetch("http://localhost:5001/detect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: debouncedInputText }),
          });
          const data = await res.json();
          if (
            data.language &&
            data.language !== inputLang &&
            Object.values(languages).includes(data.language)
          ) {
            setInputLang(data.language);
          }
        } catch (error) {
          console.error("Language detection error:", error);
        }
      }
    };
    detectLanguage();
  }, [debouncedInputText, inputLang]);

  const handleTranslate = async (textToTranslate = inputText) => {
    if (!textToTranslate.trim() || isTranslating) return;

    const isNewMessage =
      currentChat.length === 0 ||
      currentChat[currentChat.length - 1].text !== textToTranslate;

    let updatedChat = [...currentChat];
    if (isNewMessage) {
      const userMessage = {
        id: Date.now(),
        text: textToTranslate,
        sender: "user",
        lang: inputLang,
        keywords: [],
        recommendations: [],
        visualAid: null,
      };
      updatedChat.push(userMessage);
    }

    setCurrentChat(updatedChat);

    if (textToTranslate === inputText) {
      setInputText("");
    }

    setIsTranslating(true);

    try {
      const res = await fetch("http://localhost:5001/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: textToTranslate,
          source: inputLang,
          target: targetLang,
        }),
      });
      const data = await res.json();

      const visualAidUrl = data.visualAid;

      const botMessage = {
        id: Date.now() + 1,
        text: data.translatedText || "Translation failed",
        sender: "bot",
        lang: targetLang,
        keywords: data.keywords || [],
        recommendations: data.recommendations || [],
        visualAid: visualAidUrl || null,
      };
      const finalChat = [...updatedChat, botMessage];
      setCurrentChat(finalChat);
      if (botMessage.visualAid) {
        setActiveVisualAid(botMessage.visualAid);
      }

      if (activeChatId) {
        setHistory((prev) =>
          prev.map((h) =>
            h.id === activeChatId
              ? {
                  ...h,
                  chat: finalChat,
                  title: textToTranslate.substring(0, 30),
                }
              : h
          )
        );
      } else {
        const newChatId = Date.now();
        setHistory((prev) => [
          {
            id: newChatId,
            title: textToTranslate.substring(0, 30),
            chat: finalChat,
          },
          ...prev,
        ]);
        setActiveChatId(newChatId);
      }
    } catch (error) {
      console.error("Translation error:", error);
      const errorMessage = {
        id: Date.now() + 1,
        text: "Service unavailable.",
        sender: "bot",
        lang: "en",
        keywords: [],
        recommendations: [],
        visualAid: null,
      };
      setCurrentChat((prev) => [...prev, errorMessage]);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith("image/")) {
      const userMessage = {
        id: Date.now(),
        text: `Uploading and processing image: ${file.name}...`,
        sender: "user",
        lang: inputLang,
        keywords: [],
        recommendations: [],
        visualAid: null,
      };
      setCurrentChat((prev) => [...prev, userMessage]);

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch("http://localhost:5001/process_image", {
          method: "POST",
          body: formData,
        });
        const data = await res.json();

        if (res.ok) {
          const extractedText = data.extractedText;
          setCurrentChat((prev) =>
            prev.map((msg, index) =>
              index === prev.length - 1 ? { ...msg, text: extractedText } : msg
            )
          );
          handleTranslate(extractedText);
        } else {
          const errorMessage = {
            id: Date.now() + 1,
            text: `Error processing image: ${data.error}`,
            sender: "bot",
            lang: "en",
            keywords: [],
            recommendations: [],
            visualAid: null,
          };
          setCurrentChat((prev) => [...prev, errorMessage]);
        }
      } catch (error) {
        console.error("Image processing error:", error);
        const errorMessage = {
          id: Date.now() + 1,
          text: "Service unavailable. Failed to process image.",
          sender: "bot",
          lang: "en",
          keywords: [],
          recommendations: [],
          visualAid: null,
        };
        setCurrentChat((prev) => [...prev, errorMessage]);
      }
    }
    event.target.value = null;
  };

  const handleMicClick = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      startListening();
    }
  };

  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.error("Speech recognition not supported in your browser.");
      return;
    }

    recognitionRef.current = new SpeechRecognition();
    const recognition = recognitionRef.current;
    recognition.lang = speechRecognitionLangCodes[inputLang] || "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;

    let finalTranscript = "";
    recognition.onresult = (event) => {
      let interimTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      setInputText(finalTranscript + interimTranscript);
    };

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };
    recognition.onerror = (e) => {
      console.error("STT error:", e);
      setIsListening(false);
    };

    recognition.start();
  };

  const speakText = (text, lang, messageId) => {
    if (!text || !window.speechSynthesis) return;

    if (window.speechSynthesis.speaking && speakingMessageId === messageId) {
      window.speechSynthesis.cancel();
      setSpeakingMessageId(null);
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const targetLangCode = speechRecognitionLangCodes[lang] || lang;
    let foundVoice = voices.find((v) => v.lang === targetLangCode);
    if (!foundVoice) {
      foundVoice = voices.find((v) => v.lang.startsWith(lang));
    }

    utterance.voice = foundVoice;
    utterance.lang = targetLangCode;
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.onstart = () => setSpeakingMessageId(messageId);
    utterance.onend = () => setSpeakingMessageId(null);
    utterance.onerror = () => setSpeakingMessageId(null);

    window.speechSynthesis.speak(utterance);
  };

  const handleShowSignLanguage = (englishText) => {
    setSignLanguageText(englishText);
  };

  const toggleRecommendations = (messageId) => {
    setVisibleRecommendations((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  const startNewChat = () => {
    setActiveChatId(null);
    setCurrentChat([
      {
        id: "welcome",
        text: "How can I help you today?",
        sender: "bot",
        lang: "en",
        keywords: [],
        recommendations: [],
        visualAid: null,
      },
    ]);
    setActiveVisualAid(null);
  };

  const loadChatFromHistory = (chatId) => {
    const chat = history.find((h) => h.id === chatId);
    if (chat) {
      setActiveChatId(chatId);
      setCurrentChat(chat.chat);
      const lastBotMessageWithAid = [...chat.chat]
        .reverse()
        .find((m) => m.sender === "bot" && m.visualAid);
      setActiveVisualAid(
        lastBotMessageWithAid ? lastBotMessageWithAid.visualAid : null
      );
    }
  };

  const handleSosClick = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const mapsUrl = `https://www.google.com/maps/search/hospitals/@${latitude},${longitude},13z`;
          window.open(mapsUrl, "_blank");
        },
        (error) => {
          console.error("Geolocation error:", error);
          alert("Please enable location services and try again.");
        },
        {
          enableHighAccuracy: false,
          timeout: 5000,
          maximumAge: 0,
        }
      );
    } else {
      alert("Geolocation is not supported by your browser.");
    }
  };

  return (
    <div className="app-container">
      <HistorySidebar
        history={history}
        onSelectChat={loadChatFromHistory}
        onNewChat={startNewChat}
        isOpen={isSidebarOpen}
        activeChatId={activeChatId}
      />
      <div className={`chat-wrapper ${isSidebarOpen ? "sidebar-open" : ""}`}>
        <div className="chat-container">
          <header className="chat-header">
            <button
              className="sidebar-toggle"
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              aria-label="Toggle Sidebar"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fill="currentColor"
                  d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"
                ></path>
              </svg>
            </button>
            <h1>MediLingua Connect</h1>
            <div className="lang-selectors">
              <LanguageSelector
                label="From"
                value={inputLang}
                onChange={setInputLang}
              />
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  fill="currentColor"
                  d="m16.01 11l4.22-4.22l-1.42-1.41l-4.21 4.21l-1.89-1.9l-1.42 1.42l3.3 3.3zM9.5 16.5l-1.45-1.45L3 20.06l1.41 1.41L9.5 16.5zm-3.54-5.46l-4.55 4.55l1.41 1.41l4.55-4.55z"
                ></path>
              </svg>
              <LanguageSelector
                label="To"
                value={targetLang}
                onChange={setTargetLang}
              />
            </div>
          </header>

          <div className="main-content">
            <main className="chat-messages">
              {currentChat.map((msg) => (
                <div key={msg.id}>
                  <ChatMessage
                    msg={msg}
                    speakText={speakText}
                    speakingMessageId={speakingMessageId}
                    onShowSignLanguage={handleShowSignLanguage}
                    onToggleRecommendations={toggleRecommendations}
                  />
                  {msg.sender === "bot" &&
                    visibleRecommendations[msg.id] &&
                    msg.recommendations &&
                    msg.recommendations.length > 0 && (
                      <SymptomAnalysis recommendations={msg.recommendations} />
                    )}
                </div>
              ))}
              {isTranslating && <TypingIndicator />}
              <div ref={chatEndRef} />
            </main>
            <VisualAidPanel
              imageUrl={activeVisualAid}
              onShow={() => setVisualAidModalUrl(activeVisualAid)}
            />
          </div>

          <footer className="chat-input-area">
            <div className="input-wrapper">
              <button
                className="attach-btn"
                onClick={() => fileInputRef.current.click()}
                title="Upload Prescription Image"
                aria-label="Upload Prescription Image"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="currentColor"
                    d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5a2.5 2.5 0 0 1 5 0v10.5c0 .83-.67 1.5-1.5 1.5s-1.5-.67-1.5-1.5V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-1.93-1.57-3.5-3.5-3.5S8 3.07 8 5v11.5c0 2.76 2.24 5 5 5s5-2.24 5-5V6h-1.5z"
                  ></path>
                </svg>
              </button>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                style={{ display: "none" }}
                accept="image/*"
                aria-label="Upload Prescription Image"
              />
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={(e) =>
                  e.key === "Enter" &&
                  !e.shiftKey &&
                  (e.preventDefault(), handleTranslate())
                }
                placeholder="Type, speak, or upload a prescription..."
                rows={1}
                disabled={isTranslating}
                aria-label="Message Input"
              />
              <button
                onClick={handleMicClick}
                className={`mic-btn ${isListening ? "listening" : ""}`}
                title={isListening ? "Stop Listening" : "Start Listening"}
                aria-pressed={isListening}
                aria-label={isListening ? "Stop Listening" : "Start Listening"}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="currentColor"
                    d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.49 6-3.31 6-6.72h-1.7z"
                  ></path>
                </svg>
              </button>
            </div>
            <button
              onClick={handleSosClick}
              className="send-btn sos-btn"
              title="Find Nearest Hospital"
              aria-label="Find Nearest Hospital"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="#e8eaed"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M12 22s-7-4-7-12c0-4.418 3.134-8 7-8s7 3.582 7 8c0 8-7 12-7 12z"></path>
                <circle cx="12" cy="10" r="3"></circle>
              </svg>
            </button>
            <button
              onClick={() => handleTranslate()}
              className="send-btn"
              disabled={isTranslating || !inputText.trim()}
              title="Translate"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fill="currentColor"
                  d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"
                ></path>
              </svg>
            </button>
          </footer>
        </div>
      </div>

      {signLanguageText && (
        <SignLanguageModal
          text={signLanguageText}
          onClose={() => setSignLanguageText(null)}
        />
      )}
      {visualAidModalUrl && (
        <VisualAidModal
          imageUrl={visualAidModalUrl}
          onClose={() => setVisualAidModalUrl(null)}
        />
      )}
    </div>
  );
}

// --- Child Components ---
const HistorySidebar = ({
  history,
  onSelectChat,
  onNewChat,
  isOpen,
  activeChatId,
}) => (
  <aside className={`history-sidebar ${isOpen ? "open" : ""}`}>
    <div className="sidebar-header">
      <button
        onClick={onNewChat}
        className="new-chat-btn"
        aria-label="Start New Chat"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            fill="currentColor"
            d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"
          ></path>
        </svg>
        New Chat
      </button>
    </div>
    <div className="history-list">
      {history.map((item) => (
        <div
          key={item.id}
          className={`history-item ${item.id === activeChatId ? "active" : ""}`}
          onClick={() => onSelectChat(item.id)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSelectChat(item.id);
          }}
          aria-label={`Load chat: ${item.title}`}
        >
          <p>{item.title}...</p>
        </div>
      ))}
    </div>
  </aside>
);

const ChatMessage = ({
  msg,
  speakText,
  speakingMessageId,
  onShowSignLanguage,
  onToggleRecommendations,
}) => {
  const renderMessageContent = () => {
    if (!msg.keywords || msg.keywords.length === 0) {
      return <p>{msg.text}</p>;
    }

    const keywordMap = new Map();
    msg.keywords.forEach((kw) => {
      keywordMap.set(kw.term.toLowerCase(), kw.english);
    });

    const sortedTerms = msg.keywords
      .map((kw) => kw.term)
      .sort((a, b) => b.length - a.length);
    const escapedTerms = sortedTerms.map((term) =>
      term.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&")
    );
    const regex = new RegExp(`(${escapedTerms.join("|")})`, "gi");
    const parts = msg.text.split(regex);

    return (
      <p>
        {parts.map((part, index) => {
          const englishTerm = keywordMap.get(part.toLowerCase());
          if (englishTerm) {
            return (
              <button
                key={index}
                className="keyword-btn"
                onClick={() => onShowSignLanguage(englishTerm)}
                aria-label={`Show sign language for ${englishTerm}`}
              >
                {part}
              </button>
            );
          }
          return <span key={index}>{part}</span>;
        })}
      </p>
    );
  };

  return (
    <div className={`message-wrapper ${msg.sender}`} role="listitem">
      <div className="message">
        {renderMessageContent()}
        <div className="message-actions">
          <button
            className={`action-btn ${
              speakingMessageId === msg.id ? "speaking" : ""
            }`}
            onClick={() => speakText(msg.text, msg.lang, msg.id)}
            title={speakingMessageId === msg.id ? "Stop" : "Speak"}
            aria-pressed={speakingMessageId === msg.id}
            aria-label={
              speakingMessageId === msg.id ? "Stop Speaking" : "Speak Message"
            }
          >
            {speakingMessageId === msg.id ? (
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fill="currentColor"
                  d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"
                ></path>
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fill="currentColor"
                  d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"
                ></path>
              </svg>
            )}
          </button>
          {msg.sender === "bot" &&
            msg.recommendations &&
            msg.recommendations.length > 0 && (
              <button
                className="action-btn"
                onClick={() => onToggleRecommendations(msg.id)}
                title="Show Recommendations"
                aria-expanded={false}
                aria-controls={`recommendations-${msg.id}`}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="currentColor"
                    d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"
                  ></path>
                </svg>
              </button>
            )}
        </div>
      </div>
    </div>
  );
};

const TypingIndicator = () => (
  <div className="message-wrapper bot" aria-live="polite" aria-atomic="true">
    <div className="message">
      <div className="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  </div>
);

const LanguageSelector = ({ label, value, onChange }) => (
  <div className="lang-selector">
    <label>
      <span>{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={`${label} language selector`}
      >
        {Object.entries(languages).map(([name, code]) => (
          <option key={code} value={code}>
            {name}
          </option>
        ))}
      </select>
    </label>
  </div>
);

const SignLanguageModal = ({ text, onClose }) => {
  const encodedText = encodeURIComponent(text);
  const videoSrc = `https://www.spreadthesign.com/en.us/search/?q=${encodedText}`;

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`Sign language for ${text}`}
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button
          className="modal-close-btn"
          onClick={onClose}
          aria-label="Close Sign Language Modal"
        >
          ×
        </button>
        <h3>Sign Language for: "{text}"</h3>
        <iframe
          src={videoSrc}
          title={`Sign language for ${text}`}
          width="100%"
          height="400"
          frameBorder="0"
          allowFullScreen
        ></iframe>
      </div>
    </div>
  );
};

const SymptomAnalysis = ({ recommendations }) => (
  <div className="symptom-analysis-wrapper">
    <div className="symptom-analysis">
      <h4>Possible Departments to Consult</h4>
      <ul>
        {recommendations.map((dept, index) => (
          <li key={index}>{dept}</li>
        ))}
      </ul>
    </div>
  </div>
);

const VisualAidPanel = ({ imageUrl, onShow }) => {
  if (!imageUrl) {
    return <aside className="visual-aid-container"></aside>;
  }
  return (
    <aside className="visual-aid-container">
      <div className="visual-aid-card">
        <h4>Visual Aid</h4>
        <button
          className="visual-aid-btn"
          onClick={onShow}
          aria-label="View anatomical diagram"
        >
          View Diagram
        </button>
      </div>
    </aside>
  );
};

const VisualAidModal = ({ imageUrl, onClose }) => (
  <div
    className="modal-overlay"
    onClick={onClose}
    role="dialog"
    aria-modal="true"
    aria-label="Anatomical Diagram Modal"
  >
    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
      <button
        className="modal-close-btn"
        onClick={onClose}
        aria-label="Close Anatomical Diagram Modal"
      >
        ×
      </button>
      <h3>Anatomical Diagram</h3>
      <img
        src={imageUrl}
        alt="Anatomical diagram"
        className="visual-aid-image"
      />
    </div>
  </div>
);

export default App;
