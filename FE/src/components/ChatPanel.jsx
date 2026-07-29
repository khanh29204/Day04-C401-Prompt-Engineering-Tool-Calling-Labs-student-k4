import { useEffect, useRef, useState } from "react";

function getMessageText(message) {
  if (typeof message === "string") return message;
  return message?.content ?? message?.text ?? message?.message ?? "";
}

function ToolActivity({ calls }) {
  if (!Array.isArray(calls) || calls.length === 0) return null;

  return (
    <ul className="mt-3 space-y-2" aria-label="Hoạt động của CGV">
      {calls.map((call, index) => {
        const status = call?.status ?? "completed";
        const isWorking = status === "running" || status === "pending";
        const label = call?.label ?? call?.name ?? call?.tool ?? "CGV tool";

        return (
          <li
            className="flex items-center gap-2 rounded-2xl bg-surface-container-low px-3 py-2 text-sm text-on-surface-variant"
            key={call?.id ?? `${label}-${index}`}
          >
            <span
              aria-hidden="true"
              className={`inline-block size-2 rounded-full ${
                isWorking ? "animate-pulse bg-primary" : "bg-tertiary"
              }`}
            />
            <span className="min-w-0 flex-1 truncate">{label}</span>
            <span className="text-xs capitalize">{isWorking ? "Đang xử lý" : "Xong"}</span>
          </li>
        );
      })}
    </ul>
  );
}

function ChatMessage({ message }) {
  const isUser = message?.role === "user";
  const text = getMessageText(message);

  return (
    <article className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[88%] rounded-[24px] px-4 py-3 text-sm leading-6 shadow-sm sm:max-w-[76%] ${
          isUser
            ? "rounded-br-md bg-primary text-on-primary"
            : "rounded-bl-md bg-surface-container text-on-surface"
        }`}
      >
        {text ? <p className="whitespace-pre-wrap break-words">{text}</p> : null}
        <ToolActivity calls={message?.toolCalls} />
      </div>
    </article>
  );
}

export default function ChatPanel({ messages = [], pending = false, onSend }) {
  const [draft, setDraft] = useState("");
  const transcriptEndRef = useRef(null);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages.length, pending]);

  function handleSubmit(event) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || pending) return;
    onSend?.(message);
    setDraft("");
  }

  return (
    <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[28px] bg-surface shadow-[0_1px_3px_rgba(0,0,0,0.16)]" aria-label="Trò chuyện với trợ lý">
      <header className="border-b border-outline-variant/40 px-5 py-4 sm:px-6">
        <p className="text-xs font-medium tracking-[0.08em] text-primary">CGV ASSISTANT</p>
        <h1 className="mt-1 text-xl font-medium text-on-surface">Trợ lý đặt vé của bạn</h1>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-6" aria-live="polite">
        <div className="space-y-4">
          {messages.length === 0 ? (
            <p className="rounded-3xl bg-surface-container-low px-4 py-3 text-sm leading-6 text-on-surface-variant">
              Hãy hỏi phim đang chiếu, rạp gần bạn, hoặc suất chiếu phù hợp.
            </p>
          ) : (
            messages.map((message, index) => <ChatMessage key={message?.id ?? index} message={message} />)
          )}
          {pending ? (
            <div className="flex items-center gap-2 text-sm text-on-surface-variant" role="status">
              <span className="inline-flex gap-1" aria-hidden="true">
                <i className="size-1.5 animate-bounce rounded-full bg-primary [animation-delay:-0.2s]" />
                <i className="size-1.5 animate-bounce rounded-full bg-primary [animation-delay:-0.1s]" />
                <i className="size-1.5 animate-bounce rounded-full bg-primary" />
              </span>
              Agent đang xử lý yêu cầu…
            </div>
          ) : null}
          <div ref={transcriptEndRef} />
        </div>
      </div>

      <form className="border-t border-outline-variant/40 p-3 sm:p-4" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="agent-message">Nhập tin nhắn cho trợ lý</label>
        <div className="flex items-end gap-2 rounded-[28px] bg-surface-container-high px-4 py-2 focus-within:ring-2 focus-within:ring-primary">
          <textarea
            className="max-h-32 min-h-10 flex-1 resize-none bg-transparent py-2 text-sm text-on-surface outline-none placeholder:text-on-surface-variant"
            disabled={pending}
            id="agent-message"
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) handleSubmit(event);
            }}
            placeholder="Nhắn cho trợ lý…"
            rows="1"
            value={draft}
          />
          <button
            aria-label="Gửi tin nhắn"
            className="grid size-10 shrink-0 place-items-center rounded-full bg-primary text-on-primary transition hover:brightness-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-40"
            disabled={pending || !draft.trim()}
            type="submit"
          >
            <span aria-hidden="true" className="text-lg leading-none">↑</span>
          </button>
        </div>
      </form>
    </section>
  );
}
