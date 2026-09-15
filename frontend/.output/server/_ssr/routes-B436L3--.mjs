import { n as __toESM } from "../_runtime.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { n as require_jsx_runtime } from "../_libs/react+tanstack__react-query.mjs";
import { a as Moon, c as CircleAlert, i as Sun, l as Check, n as Upload, o as FileText, r as Trash2, s as Download, t as Zap } from "../_libs/lucide-react.mjs";
import { t as Slot } from "../_libs/radix-ui__react-slot.mjs";
import { n as clsx, t as cva } from "../_libs/class-variance-authority+clsx.mjs";
import { t as twMerge } from "../_libs/tailwind-merge.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/routes-B436L3--.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function cn(...inputs) {
	return twMerge(clsx(inputs));
}
var buttonVariants = cva("inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0", {
	variants: {
		variant: {
			default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
			destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
			outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
			secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
			ghost: "hover:bg-accent hover:text-accent-foreground",
			link: "text-primary underline-offset-4 hover:underline"
		},
		size: {
			default: "h-9 px-4 py-2",
			sm: "h-8 rounded-md px-3 text-xs",
			lg: "h-10 rounded-md px-8",
			icon: "h-9 w-9"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});
var Button = import_react.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(asChild ? Slot : "button", {
		className: cn(buttonVariants({
			variant,
			size,
			className
		})),
		ref,
		...props
	});
});
Button.displayName = "Button";
var API_BASE = "http://localhost:8000";
function Index() {
	const [file, setFile] = (0, import_react.useState)(null);
	const [isDragging, setIsDragging] = (0, import_react.useState)(false);
	const [isProcessing, setIsProcessing] = (0, import_react.useState)(false);
	const [progress, setProgress] = (0, import_react.useState)(0);
	const [isComplete, setIsComplete] = (0, import_react.useState)(false);
	const [isNight, setIsNight] = (0, import_react.useState)(false);
	const [result, setResult] = (0, import_react.useState)(null);
	const [error, setError] = (0, import_react.useState)(null);
	const inputRef = (0, import_react.useRef)(null);
	const progressTimerRef = (0, import_react.useRef)(null);
	(0, import_react.useEffect)(() => {
		document.documentElement.classList.toggle("dark", isNight);
		return () => {
			if (progressTimerRef.current) clearInterval(progressTimerRef.current);
		};
	}, [isNight]);
	const selectFile = (selectedFile) => {
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
				body: formData
			});
			if (!response.ok) {
				const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
				throw new Error(errorData.detail ?? `Server error: ${response.status}`);
			}
			const data = await response.json();
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
		const lines = [
			`Notice Extraction`,
			`Source: ${result.document.file_name}`,
			`Pages: ${result.document.total_pages} | Lines: ${result.document.total_lines} | Confidence: ${(result.document.average_confidence * 100).toFixed(1)}%`,
			``,
			`Extracted Fields:`,
			...Object.entries(data).filter(([, v]) => v).map(([k, v]) => `  ${k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}: ${v}`)
		];
		const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
		const url = URL.createObjectURL(blob);
		const link = document.createElement("a");
		link.href = url;
		link.download = `${result.document.file_name.replace(/\.[^.]+$/, "")}_extracted.txt`;
		link.click();
		URL.revokeObjectURL(url);
	};
	const stageState = (stage) => {
		if (isComplete || progress >= stage) return "complete";
		if (isProcessing && progress + 10 >= stage) return "active";
		return "pending";
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "app-shell min-h-screen text-foreground transition-colors duration-300",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("header", {
			className: "border-b border-border bg-card/90 backdrop-blur-sm",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-3",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "grid size-10 place-items-center rounded-xl bg-primary text-primary-foreground shadow-sm",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(FileText, { className: "size-5" })
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "leading-tight",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "font-display text-lg font-semibold tracking-tight",
							children: "Notice Extractor"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-muted-foreground",
							children: "Document processing workspace"
						})]
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "outline",
					size: "icon",
					"aria-label": isNight ? "Switch to light mode" : "Switch to night mode",
					onClick: () => setIsNight((value) => !value),
					children: isNight ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Sun, {}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Moon, {})
				})]
			})
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("main", {
			className: "mx-auto max-w-6xl px-5 py-8 sm:px-8 sm:py-12",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
					className: "mb-8",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "mb-2 text-sm font-semibold text-primary",
							children: "File analysis"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
							className: "font-display text-4xl font-semibold tracking-tight text-foreground sm:text-5xl",
							children: "Notice extraction"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "mt-3 max-w-xl text-base text-muted-foreground",
							children: "Upload a document, process it, and download the extracted notices in a clean text file."
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
					className: "panel-shadow overflow-hidden rounded-2xl border border-border bg-card",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center gap-3 border-b border-border px-5 py-4 sm:px-6",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "grid size-9 place-items-center rounded-lg bg-accent text-primary",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Upload, { className: "size-4" })
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
							className: "font-display font-semibold",
							children: "Upload a file"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-muted-foreground",
							children: "PDF files up to 50 MB"
						})] })]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "p-5 sm:p-6",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: cn("rounded-xl border-2 border-dashed border-primary/25 bg-secondary/45 px-5 py-10 text-center transition-colors", isDragging && "border-primary bg-accent"),
								onDragOver: (event) => {
									event.preventDefault();
									setIsDragging(true);
								},
								onDragLeave: () => setIsDragging(false),
								onDrop: (event) => {
									event.preventDefault();
									setIsDragging(false);
									selectFile(event.dataTransfer.files[0]);
								},
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
										className: "mx-auto grid size-14 place-items-center rounded-full bg-primary/10 text-primary",
										children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Upload, { className: "size-6" })
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
										className: "mt-4 font-display text-lg font-semibold",
										children: "Drag and drop your file here"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
										className: "mt-1 text-sm text-muted-foreground",
										children: "or choose a file from your device"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
										ref: inputRef,
										type: "file",
										className: "hidden",
										accept: ".pdf,.png,.jpg,.jpeg",
										onChange: (event) => selectFile(event.target.files?.[0])
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
										className: "mt-5",
										onClick: () => inputRef.current?.click(),
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Upload, {}), " Choose file"]
									})
								]
							}),
							file && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "mt-4 flex items-center gap-3 rounded-xl border border-border bg-muted/45 p-3",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
										className: "grid size-10 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary",
										children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(FileText, { className: "size-5" })
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "min-w-0 flex-1",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
											className: "truncate text-sm font-semibold",
											children: file.name
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
											className: "text-xs text-muted-foreground",
											children: [(file.size / 1024 / 1024).toFixed(2), " MB · ready to process"]
										})]
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
										variant: "ghost",
										size: "icon",
										"aria-label": "Remove selected file",
										onClick: removeFile,
										children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trash2, {})
									})
								]
							}),
							error && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "mt-4 flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CircleAlert, { className: "mt-0.5 size-4 shrink-0" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: error })]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "flex items-center gap-2 text-sm text-muted-foreground",
									"aria-live": "polite",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: cn("size-2 rounded-full", isComplete ? "bg-emerald-500" : isProcessing ? "animate-pulse bg-primary" : error ? "bg-destructive" : "bg-border") }), isComplete ? "Processing complete" : isProcessing ? "Processing document…" : error ? "Processing failed" : file ? "Ready to process" : "No file selected"]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
									onClick: processFile,
									disabled: !file || isProcessing,
									className: "sm:min-w-40",
									children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Zap, {}),
										" ",
										isProcessing ? "Processing…" : "Process file"
									]
								})]
							}),
							(isProcessing || isComplete) && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "mt-5",
								"aria-live": "polite",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "mb-2 flex items-center justify-between text-xs font-medium text-muted-foreground",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "Processing progress" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: [progress, "%"] })]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
									className: "h-2 overflow-hidden rounded-full bg-secondary",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
										className: "h-full rounded-full bg-primary transition-all duration-500",
										style: { width: `${progress}%` }
									})
								})]
							})
						]
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
						className: "panel-shadow overflow-hidden rounded-2xl border border-border bg-card",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-center justify-between border-b border-border px-5 py-4 sm:px-6",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex items-center gap-3",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
									className: "grid size-9 place-items-center rounded-lg bg-accent text-primary",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(FileText, { className: "size-4" })
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
									className: "font-display font-semibold",
									children: "Extracted output"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-xs text-muted-foreground",
									children: "Your processed notices appear here"
								})] })]
							}), isComplete && result && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
								className: "text-sm text-muted-foreground",
								children: [Object.values(result.extracted_data).filter(Boolean).length, " fields"]
							})]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "p-5 sm:p-6",
							children: [!isComplete ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex min-h-52 flex-col items-center justify-center text-center",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
										className: "grid size-14 place-items-center rounded-full bg-secondary text-muted-foreground",
										children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(FileText, { className: "size-6" })
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
										className: "mt-4 font-semibold",
										children: "No extraction yet"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
										className: "mt-1 max-w-sm text-sm text-muted-foreground",
										children: "Upload a file and run the process to populate the extracted notices."
									})
								]
							}) : result && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-3",
								children: [result.document && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "mb-4 rounded-xl border border-border bg-muted/30 p-3 text-xs text-muted-foreground",
									children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
											className: "font-semibold text-foreground",
											children: result.document.file_name
										}),
										" · ",
										result.document.total_pages,
										" page",
										result.document.total_pages !== 1 ? "s" : "",
										" · ",
										result.document.total_lines,
										" lines",
										" · ",
										(result.document.average_confidence * 100).toFixed(1),
										"% confidence"
									]
								}), Object.entries(result.extracted_data).filter(([, v]) => v).map(([key, value]) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(OutputField, {
									label: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
									value: value ?? ""
								}, key))]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
								variant: "outline",
								className: "mt-5 w-full",
								disabled: !isComplete,
								onClick: downloadOutput,
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Download, {}), " Download output"]
							})]
						})]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("aside", {
						className: "panel-shadow rounded-2xl border border-border bg-card p-5 sm:p-6",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-center gap-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "grid size-9 place-items-center rounded-lg bg-accent text-primary",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Zap, { className: "size-4" })
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
								className: "font-display font-semibold",
								children: "Live progress"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Pipeline stages"
							})] })]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "mt-6 space-y-5",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ProgressStage, {
									label: "File received",
									detail: "Validating the upload",
									state: stageState(10)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ProgressStage, {
									label: "Reading document",
									detail: "OCR scanning pages",
									state: stageState(40)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ProgressStage, {
									label: "Extracting fields",
									detail: "AI structured extraction",
									state: stageState(70)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ProgressStage, {
									label: "Output ready",
									detail: "Available to download",
									state: stageState(100),
									last: true
								})
							]
						})]
					})]
				})
			]
		})]
	});
}
function OutputField({ label, value }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("article", {
		className: "rounded-xl border border-border bg-muted/35 p-4",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex items-start gap-3",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-emerald-500/15 text-emerald-600",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Check, { className: "size-4" })
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
				className: "text-xs font-semibold uppercase tracking-wide text-muted-foreground",
				children: label
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "mt-0.5 text-sm font-medium leading-relaxed",
				children: value
			})] })]
		})
	});
}
function ProgressStage({ label, detail, state, last = false }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "relative flex gap-3",
		children: [
			!last && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "absolute left-[11px] top-6 h-8 w-px bg-border" }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: cn("relative z-10 grid size-6 shrink-0 place-items-center rounded-full border bg-card", state === "complete" && "border-emerald-500 bg-emerald-500 text-primary-foreground", state === "active" && "border-primary text-primary", state === "pending" && "border-border text-muted-foreground"),
				children: state === "complete" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Check, { className: "size-3.5" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: cn("size-2 rounded-full", state === "active" ? "bg-primary" : "bg-border") })
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: cn("text-sm font-semibold", state === "pending" && "text-muted-foreground"),
				children: label
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs text-muted-foreground",
				children: detail
			})] })
		]
	});
}
//#endregion
export { Index as component };
