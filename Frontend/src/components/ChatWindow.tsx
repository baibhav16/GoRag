import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Send, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MessageBubble, TypingIndicator, Message } from "./MessageBubble";

import { askQuestion } from "@/lib/api";

interface ChatWindowProps {
  docId: string; // ✅ now required
  onNewResponse: (visuals: VisualEvidence[]) => void;
}

/* ✅ Visual Evidence Format */
export interface VisualEvidence {
  id: string;
  type: "image" | "table";
  src?: string;
  caption?: string;
  page: number;
  tableData?: string[][];
}

export function ChatWindow({ docId, onNewResponse }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: `### ✅ Welcome to GoRag!

Ask me anything about your PDF and I will answer with supporting images + tables.`,
      timestamp: new Date(),
    },
  ]);

  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  /* ✅ Auto-scroll */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  /* ✅ Submit Question */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const question = input.trim();

    /* ✅ User Message */
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      /* ✅ Backend Call */
      const res = await askQuestion(question, docId);

      /* ✅ Assistant Message */
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: res.answer || "✅ Answer generated.",
        sources: res.citations?.map((p: number) => ({
          page: p,
          text: "",
        })),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      /* ✅ FIX: Backend already returns correct visuals */
      const visuals: VisualEvidence[] =
        res.supporting_visuals?.map((v: any, idx: number) => ({
          id: idx.toString(),
          type: v.type, // ✅ image or table
          src: v.src,   // ✅ already full URL
          caption: v.caption,
          page: v.page,
          tableData: v.tableData,
        })) || [];

      /* ✅ Update Visual Panel */
      onNewResponse(visuals);
    } catch (err) {
      console.error("❌ Ask Error:", err);

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 2).toString(),
          role: "assistant",
          content: "❌ Backend error while answering.",
          timestamp: new Date(),
        },
      ]);
    }

    setIsTyping(false);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isTyping && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t bg-background p-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your document..."
              className="w-full px-4 py-3 pr-12 rounded-xl border bg-card"
              disabled={isTyping}
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <Sparkles className="w-4 h-4 text-muted-foreground" />
            </div>
          </div>

          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="h-12 px-6 rounded-xl bg-primary"
            >
              <Send className="w-4 h-4" />
            </Button>
          </motion.div>
        </form>
      </div>
    </div>
  );
}
