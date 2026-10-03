import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles, FileText, MessageSquare, Image } from "lucide-react";

import { Navbar } from "@/components/Navbar";
import { UploadBox } from "@/components/UploadBox";

export default function UploadPage() {
  const navigate = useNavigate();

  // ✅ After upload → go to Chat page
  const handleUploadComplete = (docId: string) => {
    localStorage.setItem("doc_id", docId);
    navigate("/chat", { state: { pdfName: docId } });
  };

  const features = [
    {
      icon: FileText,
      title: "Smart Parsing",
      description: "Extracts text, images, and tables from complex PDFs",
    },
    {
      icon: MessageSquare,
      title: "Natural Chat",
      description: "Ask questions in plain language and get accurate answers",
    },
    {
      icon: Image,
      title: "Visual Evidence",
      description: "See relevant diagrams and tables alongside answers",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        {/* ✅ Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12 max-w-2xl"
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6"
          >
            <Sparkles className="w-4 h-4" />
            Multimodal RAG Pipeline
          </motion.div>

          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-4">
            Chat with your{" "}
            <span className="text-primary">PDF documents</span>
          </h1>

          <p className="text-lg text-muted-foreground max-w-xl mx-auto">
            Upload any PDF and get AI-powered answers with inline images, tables,
            and page citations.
          </p>
        </motion.div>

        {/* ✅ Upload Box */}
        <UploadBox onUploadComplete={handleUploadComplete} />

        {/* ✅ Features Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 max-w-4xl w-full"
        >
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.1 }}
              className="flex flex-col items-center text-center p-6 rounded-2xl bg-card border border-border"
            >
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                <feature.icon className="w-6 h-6 text-primary" />
              </div>

              <h3 className="font-semibold text-foreground mb-2">
                {feature.title}
              </h3>

              <p className="text-sm text-muted-foreground">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </main>

      {/* ✅ Footer */}
      <footer className="py-6 text-center text-sm text-muted-foreground border-t">
        <p>Built with Agentic Multimodal RAG • Demo Project</p>
      </footer>
    </div>
  );
}
