import { FileText, Sparkles } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";

interface NavbarProps {
  pdfName?: string;
}

export function Navbar({ pdfName }: NavbarProps) {
  const location = useLocation();
  const isChat = location.pathname === "/chat";

  return (
    <header className="navbar">
      <Link to="/" className="flex items-center gap-3">
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary text-primary-foreground"
        >
          <Sparkles className="w-5 h-5" />
        </motion.div>
        <div className="flex flex-col">
          <span className="text-lg font-semibold tracking-tight text-foreground">
            GoRag
          </span>
          <span className="text-xs text-muted-foreground">
            Multimodal PDF Assistant
          </span>
        </div>
      </Link>

      {isChat && pdfName && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary"
        >
          <FileText className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground max-w-[200px] truncate">
            {pdfName}
          </span>
        </motion.div>
      )}

      <nav className="flex items-center gap-4">
        <a
          href="#"
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Docs
        </a>
        <a
          href="#"
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          GitHub
        </a>
      </nav>
    </header>
  );
}
