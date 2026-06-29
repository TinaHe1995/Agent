import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types";
import type { QuestionStep } from "../mockAgent";

interface ChatPanelProps {
  messages: ChatMessage[];
  isAgentTyping: boolean;
  quickReplies?: string[];
  onSend: (text: string) => void;
  disabled?: boolean;
  embedded?: boolean;
}

export function ChatPanel({
  messages,
  isAgentTyping,
  quickReplies = [],
  onSend,
  disabled,
  embedded = false,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAgentTyping]);

  const handleSubmit = () => {
    if (!input.trim() || disabled) return;
    onSend(input);
    setInput("");
  };

  return (
    <div
      className={[
        "flex h-full min-h-0 flex-col",
        embedded
          ? "rounded-xl border border-slate-200 bg-slate-50/50"
          : "rounded-2xl border border-slate-200 bg-white shadow-sm",
      ].join(" ")}
    >
      {!embedded && (
        <div className="border-b border-slate-100 px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm text-white">
              AI
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-900">与 Agent 对话</div>
              <div className="text-xs text-slate-500">左侧聊天，右侧查看成果</div>
            </div>
          </div>
        </div>
      )}

      <div className={`chat-scroll flex-1 space-y-3 overflow-y-auto px-3 py-3 ${embedded ? "" : "px-4 py-4"}`}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`animate-fade-in flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={[
                "max-w-[92%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm",
                message.role === "user"
                  ? "rounded-br-md bg-indigo-600 text-white"
                  : "rounded-bl-md bg-slate-100 text-slate-800",
              ].join(" ")}
            >
              {message.content}
            </div>
          </div>
        ))}
        {isAgentTyping && (
          <div className="flex justify-start">
            <div className="animate-pulse-soft rounded-2xl rounded-bl-md bg-slate-100 px-4 py-3 text-sm text-slate-500">
              Agent 正在输入…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {quickReplies.length > 0 && (
        <div className="border-t border-slate-100 px-4 py-3">
          <div className="mb-2 text-xs font-medium text-slate-500">快捷回复</div>
          <div className="flex flex-wrap gap-2">
            {quickReplies.map((reply) => (
              <button
                key={reply}
                type="button"
                disabled={disabled}
                onClick={() => onSend(reply)}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-700 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 disabled:opacity-50"
              >
                {reply}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className={`border-t border-slate-100 ${embedded ? "p-3" : "p-4"}`}>
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            disabled={disabled}
            placeholder="说点什么…"
            className="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 disabled:bg-slate-50"
          />
          <button
            type="button"
            onClick={handleSubmit}
            disabled={disabled || !input.trim()}
            className="rounded-xl bg-indigo-600 px-3 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
}

interface DiscoveryStep {
  quickReplies?: string[];
}

export function getQuickReplies(
  stage: number,
  discoveryReady: boolean,
  requirementsComplete: boolean,
  _questionIndex: number,
  currentQuestion?: QuestionStep,
  currentDiscoveryStep?: DiscoveryStep,
): string[] {
  if (stage === 0 && !discoveryReady && currentDiscoveryStep?.quickReplies) {
    return currentDiscoveryStep.quickReplies;
  }
  if (stage === 1 && !requirementsComplete && currentQuestion?.quickReplies) {
    return currentQuestion.quickReplies;
  }
  if (stage === 2) {
    return ["按钮再大一点", "颜色更温暖一点", "整体更简洁"];
  }
  if (stage === 3) {
    return ["手机端打不开", "导出字段顺序改一下", "整体满意"];
  }
  return [];
}
