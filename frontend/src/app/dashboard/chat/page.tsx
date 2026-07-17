'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { ChatAPI } from '@/lib/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Message {
  role: 'user' | 'bot';
  content: string;
  streaming?: boolean;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatBotMessage(content: string): string {
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // **bold**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Lines starting with "- " become list items
  const lines = html.split('\n');
  let inList = false;
  const result: string[] = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ')) {
      if (!inList) { result.push('<ul style="margin:8px 0 8px 20px;padding:0;list-style:disc;">'); inList = true; }
      result.push(`<li style="margin:4px 0;">${trimmed.slice(2)}</li>`);
    } else {
      if (inList) { result.push('</ul>'); inList = false; }
      if (trimmed === '') {
        result.push('<br/>');
      } else {
        result.push(`<p style="margin:4px 0;">${trimmed}</p>`);
      }
    }
  }
  if (inList) result.push('</ul>');
  return result.join('');
}

// ─── Typing Indicator ─────────────────────────────────────────────────────────

function TypingDots() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '6px 0' }}>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: '#a78bfa',
            animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
    </div>
  );
}

// ─── Message Bubble ───────────────────────────────────────────────────────────

function MessageBubble({ msg }: { msg: Message }) {
  const isBot = msg.role === 'bot';
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isBot ? 'row' : 'row-reverse',
        alignItems: 'flex-start',
        gap: 10,
        maxWidth: '100%',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 18,
          background: isBot
            ? 'linear-gradient(135deg,#7c3aed,#a855f7)'
            : 'linear-gradient(135deg,#374151,#4b5563)',
          marginTop: 2,
        }}
      >
        {isBot ? '🎓' : '👤'}
      </div>

      {/* Bubble */}
      <div
        style={{
          maxWidth: 'min(75%, 540px)',
          background: isBot ? 'var(--bg3)' : 'linear-gradient(135deg,#7c3aed,#6d28d9)',
          border: `1px solid ${isBot ? 'var(--border2)' : 'transparent'}`,
          borderRadius: isBot ? '4px 16px 16px 16px' : '16px 4px 16px 16px',
          padding: '12px 16px',
          color: 'var(--text)',
          fontSize: 14,
          lineHeight: 1.65,
          wordBreak: 'break-word',
        }}
      >
        {isBot ? (
          msg.streaming && !msg.content ? (
            <TypingDots />
          ) : (
            <div dangerouslySetInnerHTML={{ __html: formatBotMessage(msg.content) }} />
          )
        ) : (
          <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
        )}
      </div>
    </div>
  );
}

// ─── Quick Chips ──────────────────────────────────────────────────────────────

const CHIPS = [
  { label: '🔍 Skill Gap Analysis', prompt: 'Analyze my skill gaps for placement' },
  { label: '🗺️ Generate Roadmap', prompt: 'Generate a personalized placement roadmap for me' },
  { label: '🎤 Mock Interview', prompt: 'Start a quick mock interview session' },
  { label: '📚 Resources', prompt: 'What are the best resources for placement preparation?' },
];

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const sessionId = useRef(crypto.randomUUID());
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const hasUserMessage = messages.some((m) => m.role === 'user');

  // Welcome message
  useEffect(() => {
    setMessages([
      {
        role: 'bot',
        content:
          "Hello! I'm your **PlaceMentor AI** 🎓\n\nI can help you with:\n- Skill gap analysis & personalized roadmaps\n- Mock interviews (Technical, DSA, HR, Behavioral)\n- Resume feedback & ATS optimization\n- Company-specific preparation strategies\n- Aptitude & core subject guidance\n\nWhat would you like to work on today?",
      },
    ]);
  }, []);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  const resizeTextarea = () => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
  };

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;
      setInput('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';

      const userMsg: Message = { role: 'user', content: trimmed };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      // Add streaming bot placeholder
      const botId = Date.now();
      setMessages((prev) => [
        ...prev,
        { role: 'bot', content: '', streaming: true },
      ]);

      let streamed = '';
      let streamFailed = false;

      await ChatAPI.streamMessage(
        trimmed,
        (chunk) => {
          streamed += chunk;
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === 'bot') copy[copy.length - 1] = { ...last, content: streamed, streaming: true };
            return copy;
          });
        },
        () => {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === 'bot') copy[copy.length - 1] = { ...last, streaming: false };
            return copy;
          });
        },
        () => { streamFailed = true; },
        sessionId.current,
      );

      if (streamFailed || !streamed) {
        try {
          const res = await ChatAPI.sendMessage(trimmed, { session_id: sessionId.current });
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === 'bot') copy[copy.length - 1] = { role: 'bot', content: res.response, streaming: false };
            return copy;
          });
        } catch {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === 'bot') copy[copy.length - 1] = { role: 'bot', content: 'Sorry, I encountered an error. Please try again.', streaming: false };
            return copy;
          });
        }
      }

      void botId;
      setIsLoading(false);
    },
    [isLoading],
  );

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 60px)',
        maxWidth: 820,
        margin: '0 auto',
        padding: '24px 16px 0',
      }}
    >
      <style>{`
        @keyframes bounce {
          0%,80%,100% { transform: translateY(0); opacity: 0.5; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
        .chat-input:focus { outline: none; border-color: #7c3aed !important; box-shadow: 0 0 0 3px rgba(124,58,237,0.2); }
        .chip-btn:hover { background: rgba(124,58,237,0.2) !important; border-color: #7c3aed !important; }
        .send-btn:hover:not(:disabled) { opacity: 0.9; transform: scale(1.05); }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 16, flexShrink: 0 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text)', margin: '0 0 4px' }}>
          🎓 AI Mentor Chat
        </h1>
        <p style={{ color: 'var(--text-2)', fontSize: 13, margin: 0 }}>
          Powered by Gemini AI · Session ID: {sessionId.current.slice(0, 8)}…
        </p>
      </div>

      {/* Quick Chips (only before first user message) */}
      {!hasUserMessage && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16, flexShrink: 0 }}>
          {CHIPS.map((chip) => (
            <button
              key={chip.label}
              onClick={() => sendMessage(chip.prompt)}
              className="chip-btn"
              style={{
                background: 'rgba(124,58,237,0.1)',
                border: '1px solid rgba(124,58,237,0.25)',
                borderRadius: 20,
                padding: '8px 14px',
                color: '#c4b5fd',
                fontSize: 13,
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'background 0.2s, border-color 0.2s',
              }}
            >
              {chip.label}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          paddingBottom: 16,
          scrollbarWidth: 'thin',
          scrollbarColor: 'var(--border2) transparent',
        }}
      >
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}
        {isLoading && messages[messages.length - 1]?.role === 'user' && (
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg,#7c3aed,#a855f7)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>🎓</div>
            <div style={{ background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: '4px 16px 16px 16px', padding: '12px 16px' }}>
              <TypingDots />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div
        style={{
          flexShrink: 0,
          padding: '12px 0 20px',
          borderTop: '1px solid var(--border)',
        }}
      >
        <div
          style={{
            display: 'flex',
            gap: 10,
            alignItems: 'flex-end',
            background: 'var(--bg2)',
            border: '1px solid var(--border2)',
            borderRadius: 14,
            padding: '10px 12px',
            transition: 'border-color 0.2s',
          }}
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => { setInput(e.target.value); resizeTextarea(); }}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything… (Enter to send, Shift+Enter for new line)"
            rows={1}
            className="chat-input"
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              resize: 'none',
              color: 'var(--text)',
              fontSize: 14,
              lineHeight: 1.5,
              maxHeight: 140,
              outline: 'none',
              fontFamily: 'inherit',
            }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={isLoading || !input.trim()}
            className="send-btn"
            style={{
              width: 38,
              height: 38,
              borderRadius: 10,
              background: input.trim() && !isLoading ? 'linear-gradient(135deg,#7c3aed,#a855f7)' : 'var(--bg3)',
              border: '1px solid var(--border2)',
              color: input.trim() && !isLoading ? '#fff' : 'var(--text-2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
              flexShrink: 0,
              transition: 'background 0.2s, color 0.2s, transform 0.15s',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <div style={{ color: 'var(--text-2)', fontSize: 11, textAlign: 'center', marginTop: 8 }}>
          AI can make mistakes. Verify important information.
        </div>
      </div>
    </div>
  );
}
