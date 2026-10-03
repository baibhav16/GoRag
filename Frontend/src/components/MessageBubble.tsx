import { motion } from "framer-motion";
import { User, Bot, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

export interface MessageSource {
  page: number;
  text: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: MessageSource[];
  timestamp: Date;
}

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        "flex gap-3 w-full",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center",
          isUser ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground"
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message content */}
      <div
        className={cn(
          "flex flex-col gap-2 max-w-[80%]",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div className={cn(isUser ? "chat-bubble-user" : "chat-bubble-assistant")}>
          {/* Render markdown-like content for assistant */}
          {isUser ? (
            <p className="text-sm leading-relaxed">{message.content}</p>
          ) : (
            <div className="text-sm leading-relaxed space-y-3">
              {message.content.split("\n\n").map((paragraph, i) => {
                if (paragraph.startsWith("### ")) {
                  return (
                    <h4 key={i} className="font-semibold text-foreground pt-2 first:pt-0">
                      {paragraph.replace("### ", "")}
                    </h4>
                  );
                }
                if (paragraph.startsWith("- ")) {
                  return (
                    <ul key={i} className="list-disc list-inside space-y-1 text-muted-foreground">
                      {paragraph.split("\n").map((item, j) => (
                        <li key={j}>{item.replace("- ", "")}</li>
                      ))}
                    </ul>
                  );
                }
                return (
                  <p key={i} className="text-muted-foreground">
                    {paragraph}
                  </p>
                );
              })}
            </div>
          )}
        </div>

        {/* Sources for assistant messages */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.sources.map((source, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-secondary text-xs text-muted-foreground hover:bg-secondary/80 cursor-pointer transition-colors"
              >
                <FileText className="w-3 h-3" />
                <span>Page {source.page}</span>
              </motion.div>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-xs text-muted-foreground">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </motion.div>
  );
}

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3"
    >
      <div className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center bg-secondary text-muted-foreground">
        <Bot className="w-4 h-4" />
      </div>
      <div className="chat-bubble-assistant flex items-center gap-1.5 px-5">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </motion.div>
  );
}
