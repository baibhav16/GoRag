import { useState } from "react";
import { useLocation, Navigate } from "react-router-dom";
import { motion } from "framer-motion";
import { FileText, ChevronLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { ChatWindow, VisualEvidence } from "@/components/ChatWindow";
import { VisualPanel } from "@/components/VisualPanel";

export default function ChatPage() {
  const location = useLocation();
  const pdfName = location.state?.pdfName as string | undefined;
  const [visuals, setVisuals] = useState<VisualEvidence[]>([]);
  const [showPanel, setShowPanel] = useState(true);

  // Redirect if no PDF was uploaded
  if (!pdfName) {
    return <Navigate to="/" replace />;
  }

  const handleNewResponse = (newVisuals: VisualEvidence[]) => {
    setVisuals(newVisuals);
    if (newVisuals.length > 0 && !showPanel) {
      setShowPanel(true);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <Navbar pdfName={pdfName} />

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <motion.aside
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="hidden lg:flex w-64 flex-col bg-sidebar text-sidebar-foreground border-r"
        >
          <div className="p-4">
            <Link
              to="/"
              className="flex items-center gap-2 text-sm text-sidebar-foreground/70 hover:text-sidebar-foreground transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              New Upload
            </Link>
          </div>

          <div className="px-4 py-2">
            <p className="text-xs font-medium uppercase tracking-wider text-sidebar-foreground/50 mb-3">
              Current Document
            </p>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-sidebar-accent">
              <div className="w-8 h-8 rounded-md bg-sidebar-primary/20 flex items-center justify-center flex-shrink-0">
                <FileText className="w-4 h-4 text-sidebar-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-sidebar-foreground truncate">
                  {pdfName}
                </p>
                <p className="text-xs text-sidebar-foreground/50 mt-0.5">
                  Ready for questions
                </p>
              </div>
            </div>
          </div>

          <div className="mt-auto p-4 border-t border-sidebar-border">
            <div className="flex items-center gap-2 text-xs text-sidebar-foreground/50">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
              <span>AI Model Connected</span>
            </div>
          </div>
        </motion.aside>

        {/* Main chat area */}
        <main className="flex-1 flex flex-col min-w-0">
          <ChatWindow docId={pdfName} onNewResponse={handleNewResponse} />

        </main>

        {/* Visual evidence panel */}
        {showPanel && (
          <motion.aside
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="hidden md:block w-80 lg:w-96 border-l"
          >
            <VisualPanel visuals={visuals} />
          </motion.aside>
        )}
      </div>
    </div>
  );
}
