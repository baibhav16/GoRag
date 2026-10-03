import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Image, Table, FileText, Eye } from "lucide-react";
import type { VisualEvidence } from "./ChatWindow";
import { API_BASE_URL } from "@/lib/api";

function getVisualUrl(src?: string) {
  if (!src) return undefined;
  if (/^https?:\/\//i.test(src)) return src;
  return `${API_BASE_URL}/${src.replace(/^\/+/, "")}`;
}

function VisualImage({ src, caption }: { src?: string; caption?: string }) {
  const [error, setError] = useState(false);
  const url = getVisualUrl(src);

  if (!url || error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4 text-center bg-secondary/50 text-xs text-muted-foreground">
        <Image className="w-6 h-6 mb-1 opacity-40" />
        <span>Figure referenced in page</span>
        <span className="text-[10px] opacity-75">(Image preview unavailable)</span>
      </div>
    );
  }

  return (
    <img
      src={url}
      alt={caption || "Visual evidence"}
      className="w-full h-full object-cover"
      onError={() => setError(true)}
    />
  );
}

interface VisualPanelProps {
  visuals: VisualEvidence[];
}

export function VisualPanel({ visuals }: VisualPanelProps) {
  return (
    <div className="h-full flex flex-col bg-panel-bg">
      {/* ✅ Header */}
      <div className="flex items-center gap-2 px-5 py-4 border-b bg-background">
        <Eye className="w-4 h-4 text-primary" />
        <h2 className="text-sm font-semibold text-foreground">
          Supporting Visuals
        </h2>

        {visuals.length > 0 && (
          <span className="ml-auto px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
            {visuals.length}
          </span>
        )}
      </div>

      {/* ✅ Visual List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
        <AnimatePresence mode="popLayout">
          {/* ✅ No Visuals */}
          {visuals.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center h-full text-center px-6 py-12"
            >
              <div className="w-16 h-16 rounded-2xl bg-secondary flex items-center justify-center mb-4">
                <Image className="w-8 h-8 text-muted-foreground" />
              </div>

              <h3 className="text-sm font-medium text-foreground mb-1">
                No visuals yet
              </h3>

              <p className="text-xs text-muted-foreground max-w-[220px]">
                Ask a question and relevant images, diagrams, and tables will
                appear here.
              </p>
            </motion.div>
          ) : (
            visuals.map((visual, index) => (
              <motion.div
                key={visual.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: index * 0.05 }}
                className="visual-card rounded-xl border bg-card overflow-hidden shadow-sm"
              >
                {/* ✅ IMAGE VISUAL */}
                {visual.type === "image" && (
                  <>
                    {/* Image Preview */}
                    <div className="relative aspect-video bg-secondary overflow-hidden">
                      <VisualImage src={visual.src} caption={visual.caption} />

                      {/* Badge */}
                      <div className="absolute top-2 left-2 flex items-center gap-1 px-2 py-1 rounded-md bg-background/90 backdrop-blur-sm">
                        <Image className="w-3 h-3 text-primary" />
                        <span className="text-xs font-medium text-foreground">
                          Image
                        </span>
                      </div>
                    </div>

                    {/* Caption */}
                    <div className="p-3 space-y-1">
                      {visual.caption && (
                        <p className="text-xs font-medium text-foreground line-clamp-2">
                          {visual.caption}
                        </p>
                      )}

                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <FileText className="w-3 h-3" />
                        <span>Page {visual.page}</span>
                      </div>
                    </div>
                  </>
                )}

                {/* ✅ TABLE VISUAL */}
                {visual.type === "table" && (
                  <>
                    {/* Table Header */}
                    <div className="p-3 border-b flex items-center gap-2">
                      <Table className="w-4 h-4 text-primary" />
                      <span className="text-xs font-semibold text-foreground">
                        Table
                      </span>

                      <div className="ml-auto flex items-center gap-1 text-xs text-muted-foreground">
                        <FileText className="w-3 h-3" />
                        <span>Page {visual.page}</span>
                      </div>
                    </div>

                    {/* Caption */}
                    {visual.caption && (
                      <div className="px-3 py-2 border-b bg-secondary/30">
                        <p className="text-xs text-muted-foreground">
                          {visual.caption}
                        </p>
                      </div>
                    )}

                    {/* Table Data */}
                    {visual.tableData ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="bg-secondary">
                              {visual.tableData[0].map((header, i) => (
                                <th
                                  key={i}
                                  className="px-3 py-2 text-left font-semibold text-foreground border-r last:border-r-0"
                                >
                                  {header}
                                </th>
                              ))}
                            </tr>
                          </thead>

                          <tbody>
                            {visual.tableData
                              .slice(1)
                              .map((row, rowIndex) => (
                                <tr
                                  key={rowIndex}
                                  className="border-t hover:bg-secondary/20 transition-colors"
                                >
                                  {row.map((cell, cellIndex) => (
                                    <td
                                      key={cellIndex}
                                      className="px-3 py-2 text-muted-foreground border-r last:border-r-0"
                                    >
                                      {cell}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="p-3 text-xs text-muted-foreground">
                        Table data not available.
                      </p>
                    )}
                  </>
                )}
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
