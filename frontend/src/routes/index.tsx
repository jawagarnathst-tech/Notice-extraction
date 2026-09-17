import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import {
  Check,
  Download,
  FileText,
  Moon,
  Sun,
  Trash2,
  Upload,
  Zap,
  AlertCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const API_BASE = import.meta.env.VITE_API_BASE || (typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : 'http://localhost:8000');

interface ExtractedData {
  account?: string | null;
  country?: string | null;
  agency?: string | null;
  agency_type?: string | null;
  department?: string | null;
  classification?: string | null;
  notice_type?: string | null;
  tax_period?: string | null;
  tax_year?: string | null;
  agency_id_to_use?: string | null;
  notice_manager?: string | null;
  amount_type?: string | null;
  issue_date?: string | null;
  credit_amount?: number | null;
  tax_amount?: number | null;
  penalty_amount?: number | null;
  interest_amount?: number | null;
  total_amount?: number | null;
  [key: string]: string | number | null | undefined;
}

interface ExtractionResult {
  status: string;
  document: {
    file_name: string;
    total_pages: number;
    total_lines: number;
    average_confidence: number;
  };
  extracted_data: ExtractedData;
}

export const Route = createFileRoute("/")(({
  head: () => ({
    meta: [
      { title: "Notice Extraction Workspace" },
      { name: "description", content: "Upload a document, process it, and download a clean notice extraction." },
      { property: "og:title", content: "Notice Extraction Workspace" },
      { property: "og:description", content: "Upload a document, process it, and download a clean notice extraction." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
}));

function Index() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [isNight, setIsNight] = useState(false);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isNight);
    return () => {
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
    };
  }, [isNight]);

  const selectFile = (selectedFile: File | undefined) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    setIsComplete(false);
    setProgress(0);
    setResult(null);
    setError(null);
  };

  const processFile = async () => {
    if (!file || isProcessing) return;
    setIsProcessing(true);
    setIsComplete(false);
    setResult(null);
    setError(null);
    setProgress(10);

    // Animate progress while waiting for the API
    let currentProgress = 10;
    progressTimerRef.current = setInterval(() => {
      currentProgress = Math.min(currentProgress + 5, 85);
      setProgress(currentProgress);
    }, 600);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE}/api/extract`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail ?? `Server error: ${response.status}`);
      }

      const data: ExtractionResult = await response.json();
      setResult(data);
      setProgress(100);
      setIsComplete(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process file");
    } finally {
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
      setIsProcessing(false);
    }
  };

  const removeFile = () => {
    setFile(null);
    setIsComplete(false);
    setProgress(0);
    setResult(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const downloadOutput = () => {
    if (!isComplete || !result) return;
    const data = result.extracted_data;
    const jsonString = JSON.stringify(data, null, 2);
    
    const blob = new Blob([jsonString], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${result.document.file_name.replace(/\.[^.]+$/, "")}_extracted.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const stageState = (stage: number) => {
    if (isComplete || progress >= stage) return "complete";
    if (isProcessing && progress + 10 >= stage) return "active";
    return "pending";
  };

  return (
    <div className="app-shell min-h-screen text-foreground transition-colors duration-300">
      <header className="border-b border-border bg-card/90 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <FileText className="size-5" />
            </div>
            <div className="leading-tight">
              <p className="font-display text-lg font-semibold tracking-tight">Notice Extractor</p>
              <p className="text-xs text-muted-foreground">Document processing workspace</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="icon"
            aria-label={isNight ? "Switch to light mode" : "Switch to night mode"}
            onClick={() => setIsNight((value) => !value)}
          >
            {isNight ? <Sun /> : <Moon />}
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8 sm:py-12">
        <section className="mb-8">
          <p className="mb-2 text-sm font-semibold text-primary">File analysis</p>
          <h1 className="font-display text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Notice extraction
          </h1>
          <p className="mt-3 max-w-xl text-base text-muted-foreground">
            Upload a document, process it, and download the extracted notices in a clean text file.
          </p>
        </section>

        <section className="panel-shadow overflow-hidden rounded-2xl border border-border bg-card">
          <div className="flex items-center gap-3 border-b border-border px-5 py-4 sm:px-6">
            <div className="grid size-9 place-items-center rounded-lg bg-accent text-primary">
              <Upload className="size-4" />
            </div>
            <div>
              <h2 className="font-display font-semibold">Upload a file</h2>
              <p className="text-xs text-muted-foreground">PDF files up to 50 MB</p>
            </div>
          </div>
          <div className="p-5 sm:p-6">
            <div
              className={cn(
                "rounded-xl border-2 border-dashed border-primary/25 bg-secondary/45 px-5 py-10 text-center transition-colors",
                isDragging && "border-primary bg-accent",
              )}
              onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(event) => { event.preventDefault(); setIsDragging(false); selectFile(event.dataTransfer.files[0]); }}
            >
              <div className="mx-auto grid size-14 place-items-center rounded-full bg-primary/10 text-primary">
                <Upload className="size-6" />
              </div>
              <p className="mt-4 font-display text-lg font-semibold">Drag and drop your file here</p>
              <p className="mt-1 text-sm text-muted-foreground">or choose a file from your device</p>
              <input
                ref={inputRef}
                type="file"
                className="hidden"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(event) => selectFile(event.target.files?.[0])}
              />
              <Button className="mt-5" onClick={() => inputRef.current?.click()}>
                <Upload /> Choose file
              </Button>
            </div>

            {file && (
              <div className="mt-4 flex items-center gap-3 rounded-xl border border-border bg-muted/45 p-3">
                <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
                  <FileText className="size-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB · ready to process
                  </p>
                </div>
                <Button variant="ghost" size="icon" aria-label="Remove selected file" onClick={removeFile}>
                  <Trash2 />
                </Button>
              </div>
            )}

            {error && (
              <div className="mt-4 flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2 text-sm text-muted-foreground" aria-live="polite">
                <span
                  className={cn(
                    "size-2 rounded-full",
                    isComplete ? "bg-emerald-500" : isProcessing ? "animate-pulse bg-primary" : error ? "bg-destructive" : "bg-border",
                  )}
                />
                {isComplete
                  ? "Processing complete"
                  : isProcessing
                    ? "Processing document…"
                    : error
                      ? "Processing failed"
                      : file
                        ? "Ready to process"
                        : "No file selected"}
              </div>
              <Button
                onClick={processFile}
                disabled={!file || isProcessing}
                className="sm:min-w-40"
              >
                <Zap /> {isProcessing ? "Processing…" : "Process file"}
              </Button>
            </div>

            {(isProcessing || isComplete) && (
              <div className="mt-5" aria-live="polite">
                <div className="mb-2 flex items-center justify-between text-xs font-medium text-muted-foreground">
                  <span>Processing progress</span>
                  <span>{progress}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full bg-primary transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </section>

        <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
          <section className="panel-shadow overflow-hidden rounded-2xl border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border px-5 py-4 sm:px-6">
              <div className="flex items-center gap-3">
                <div className="grid size-9 place-items-center rounded-lg bg-accent text-primary">
                  <FileText className="size-4" />
                </div>
                <div>
                  <h2 className="font-display font-semibold">Extracted output</h2>
                  <p className="text-xs text-muted-foreground">Your processed notices appear here</p>
                </div>
              </div>
              {isComplete && result && (
                <span className="text-sm text-muted-foreground">
                  {Object.values(result.extracted_data).filter(Boolean).length} fields
                </span>
              )}
            </div>
            <div className="p-5 sm:p-6">
              {!isComplete ? (
                <div className="flex min-h-52 flex-col items-center justify-center text-center">
                  <div className="grid size-14 place-items-center rounded-full bg-secondary text-muted-foreground">
                    <FileText className="size-6" />
                  </div>
                  <p className="mt-4 font-semibold">No extraction yet</p>
                  <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                    Upload a file and run the process to populate the extracted notices.
                  </p>
                </div>
              ) : (
                result && (
                  <div className="space-y-3">
                    {result.document && (
                      <div className="mb-4 rounded-xl border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
                        <span className="font-semibold text-foreground">{result.document.file_name}</span>
                        {" · "}
                        {result.document.total_pages} page{result.document.total_pages !== 1 ? "s" : ""}
                        {" · "}
                        {result.document.total_lines} lines
                        {" · "}
                        {(result.document.average_confidence * 100).toFixed(1)}% confidence
                      </div>
                    )}
                    <div className="rounded-xl border border-border bg-muted/20 p-4 overflow-auto max-h-[500px]">
                      <pre className="text-sm text-foreground/80 font-mono whitespace-pre-wrap">
                        {JSON.stringify(result.extracted_data, null, 2)}
                      </pre>
                    </div>
                  </div>
                )
              )}
              <Button
                variant="outline"
                className="mt-5 w-full"
                disabled={!isComplete}
                onClick={downloadOutput}
              >
                <Download /> Download output
              </Button>
            </div>
          </section>

          <aside className="panel-shadow rounded-2xl border border-border bg-card p-5 sm:p-6">
            <div className="flex items-center gap-3">
              <div className="grid size-9 place-items-center rounded-lg bg-accent text-primary">
                <Zap className="size-4" />
              </div>
              <div>
                <h2 className="font-display font-semibold">Live progress</h2>
                <p className="text-xs text-muted-foreground">Pipeline stages</p>
              </div>
            </div>
            <div className="mt-6 space-y-5">
              <ProgressStage label="File received" detail="Validating the upload" state={stageState(10)} />
              <ProgressStage label="Reading document" detail="OCR scanning pages" state={stageState(40)} />
              <ProgressStage label="Extracting fields" detail="AI structured extraction" state={stageState(70)} />
              <ProgressStage label="Output ready" detail="Available to download" state={stageState(100)} last />
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}



function ProgressStage({
  label,
  detail,
  state,
  last = false,
}: {
  label: string;
  detail: string;
  state: "complete" | "active" | "pending";
  last?: boolean;
}) {
  return (
    <div className="relative flex gap-3">
      {!last && <span className="absolute left-[11px] top-6 h-8 w-px bg-border" />}
      <div
        className={cn(
          "relative z-10 grid size-6 shrink-0 place-items-center rounded-full border bg-card",
          state === "complete" && "border-emerald-500 bg-emerald-500 text-primary-foreground",
          state === "active" && "border-primary text-primary",
          state === "pending" && "border-border text-muted-foreground",
        )}
      >
        {state === "complete" ? (
          <Check className="size-3.5" />
        ) : (
          <span className={cn("size-2 rounded-full", state === "active" ? "bg-primary" : "bg-border")} />
        )}
      </div>
      <div>
        <p className={cn("text-sm font-semibold", state === "pending" && "text-muted-foreground")}>{label}</p>
        <p className="text-xs text-muted-foreground">{detail}</p>
      </div>
    </div>
  );
}
