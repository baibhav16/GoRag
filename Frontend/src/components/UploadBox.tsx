import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, CheckCircle2, Loader2, Image, Table, Database } from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadPDF } from "@/lib/api";

interface UploadBoxProps {
  onUploadComplete: (fileName: string) => void;
}

type UploadStatus = "idle" | "uploading" | "parsing" | "extracting" | "indexing" | "complete";

const statusConfig = {
  idle: { message: "", icon: null },
  uploading: { message: "Uploading PDF...", icon: Loader2 },
  parsing: { message: "Parsing PDF...", icon: FileText },
  extracting: { message: "Extracting images & tables...", icon: Image },
  indexing: { message: "Indexing in vector database...", icon: Database },
  complete: { message: "Ready to chat ✅", icon: CheckCircle2 },
};

export function UploadBox({ onUploadComplete }: UploadBoxProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [fileName, setFileName] = useState<string | null>(null);

  const uploadFile = useCallback(async (file: File) => {
    setFileName(file.name);
    setProgress(0);
    setStatus("uploading");

    try {
      const result = await uploadPDF(file);
      setProgress(100);
      setStatus("complete");
      await new Promise((resolve) => setTimeout(resolve, 500));
      onUploadComplete(result.doc_id);
    } catch (error) {
      setStatus("idle");
      setProgress(0);
      window.alert(error instanceof Error ? error.message : "PDF upload failed");
    }
  }, [onUploadComplete]);
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file && file.type === "application/pdf") {
        uploadFile(file);
      }
    },
    [uploadFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        uploadFile(file);
      }
    },
    [uploadFile]
  );

  const isProcessing = status !== "idle" && status !== "complete";
  const StatusIcon = statusConfig[status].icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-2xl mx-auto"
    >
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "upload-zone cursor-pointer",
          isDragOver && "dragover",
          isProcessing && "pointer-events-none"
        )}
      >
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileInput}
          className="absolute inset-0 opacity-0 cursor-pointer"
          disabled={isProcessing}
        />

        <AnimatePresence mode="wait">
          {status === "idle" ? (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-4"
            >
              <motion.div
                animate={{ y: isDragOver ? -8 : 0 }}
                transition={{ type: "spring", stiffness: 300 }}
                className="flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10"
              >
                <Upload className="w-8 h-8 text-primary" />
              </motion.div>
              <div className="text-center">
                <h3 className="text-lg font-semibold text-foreground mb-1">
                  Drop your PDF here
                </h3>
                <p className="text-sm text-muted-foreground">
                  or click to browse • Biology books, reports, research papers
                </p>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-secondary text-muted-foreground">
                  .PDF
                </span>
                <span className="px-3 py-1 text-xs font-medium rounded-full bg-secondary text-muted-foreground">
                  Max 50MB
                </span>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="processing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-6 py-4"
            >
              {/* File name */}
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary">
                <FileText className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium text-foreground truncate max-w-[300px]">
                  {fileName}
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full max-w-md">
                <div className="progress-bar h-2">
                  <motion.div
                    className="h-full rounded-full bg-primary"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>

              {/* Status */}
              <motion.div
                key={status}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2"
              >
                {StatusIcon && (
                  <StatusIcon
                    className={cn(
                      "w-5 h-5",
                      status === "complete" ? "text-success" : "text-primary animate-spin"
                    )}
                  />
                )}
                <span
                  className={cn(
                    "text-sm font-medium",
                    status === "complete" ? "text-success" : "text-foreground"
                  )}
                >
                  {statusConfig[status].message}
                </span>
              </motion.div>

              {/* Processing steps */}
              <div className="flex items-center gap-6 mt-2">
                {[
                  { icon: FileText, label: "Parse", done: ["extracting", "indexing", "complete"].includes(status) },
                  { icon: Image, label: "Extract", done: ["indexing", "complete"].includes(status) },
                  { icon: Database, label: "Index", done: status === "complete" },
                ].map((step, i) => (
                  <div key={i} className="flex flex-col items-center gap-1">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-lg flex items-center justify-center transition-colors",
                        step.done ? "bg-success/10 text-success" : "bg-secondary text-muted-foreground"
                      )}
                    >
                      <step.icon className="w-4 h-4" />
                    </div>
                    <span className="text-xs text-muted-foreground">{step.label}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
