/**
 * ToolCallStatus – collapsible panel showing tool call information.
 *
 * Displays tool name with icon, execution status (calling/done),
 * and an expandable area for arguments and results.
 */

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { ToolCallInfo } from "@/types/bazi";

// ── Helpers ────────────────────────────────────────────────────────────

/** Map tool names to friendly Chinese labels and icons. */
const TOOL_META: Record<string, { label: string; icon: string }> = {
  get_bazi_chart: { label: "排盘", icon: "☰" },
  analyze_elements: { label: "五行分析", icon: "☲" },
  analyze_ten_gods: { label: "十神分析", icon: "☵" },
  analyze_shensha: { label: "神煞分析", icon: "☶" },
  analyze_dayun: { label: "大运分析", icon: "☳" },
  search_knowledge: { label: "知识检索", icon: "☴" },
  web_search: { label: "联网搜索", icon: "☷" },
};

function getToolMeta(name: string) {
  return TOOL_META[name] ?? { label: name, icon: "⚙" };
}

/** Format JSON string for display, with fallback. */
function tryFormatJSON(raw: string): string {
  try {
    return JSON.stringify(JSON.parse(raw), null, 2);
  } catch {
    return raw;
  }
}

// ── Component ──────────────────────────────────────────────────────────

interface ToolCallStatusProps {
  toolCall: ToolCallInfo;
  className?: string;
}

export function ToolCallStatus({ toolCall, className }: ToolCallStatusProps) {
  const [expanded, setExpanded] = useState(false);
  const { label, icon } = getToolMeta(toolCall.name);

  const isRunning = toolCall.status === "calling";
  const isError = toolCall.status === "error";

  return (
    <div
      className={cn(
        "rounded-lg border border-[#30363d] bg-[#161b22] transition-all",
        isError && "border-[#e94560]/40",
        className
      )}
    >
      {/* Header – always visible */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className={cn(
          "flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors",
          "hover:bg-[#1c2128] rounded-lg cursor-pointer select-none"
        )}
      >
        {/* Status indicator */}
        {isRunning ? (
          <span className="relative flex h-4 w-4 shrink-0">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#d4af37] opacity-60" />
            <span className="relative inline-flex h-4 w-4 rounded-full bg-[#d4af37]/80" />
          </span>
        ) : isError ? (
          <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-[#e94560]/80 text-[10px] text-white">
            !
          </span>
        ) : (
          <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-[#50c878]/80 text-[10px] text-[#0d1117]">
            ✓
          </span>
        )}

        {/* Icon + label */}
        <span aria-hidden="true" className="text-base">
          {icon}
        </span>
        <span className="font-medium text-[#e6edf3]">{label}</span>

        {/* Status text */}
        <span
          className={cn(
            "ml-auto text-xs",
            isRunning
              ? "text-[#d4af37]"
              : isError
                ? "text-[#e94560]"
                : "text-[#8b949e]"
          )}
        >
          {isRunning ? "调用中..." : isError ? "调用失败" : "已完成"}
        </span>

        {/* Expand chevron */}
        <span
          className={cn(
            "ml-1 text-[#8b949e] transition-transform",
            expanded && "rotate-180"
          )}
        >
          ▾
        </span>
      </button>

      {/* Expandable body */}
      {expanded && (
        <div className="border-t border-[#30363d] px-3 py-2 space-y-2">
          {/* Arguments */}
          {toolCall.arguments && (
            <div>
              <h4 className="text-xs font-medium text-[#8b949e] mb-1">
                参数
              </h4>
              <pre className="overflow-x-auto rounded bg-[#0d1117] p-2 text-xs text-[#e6edf3] whitespace-pre-wrap break-all">
                {tryFormatJSON(toolCall.arguments)}
              </pre>
            </div>
          )}

          {/* Result */}
          {toolCall.result !== null && (
            <div>
              <h4 className="text-xs font-medium text-[#8b949e] mb-1">
                结果
              </h4>
              <pre className="overflow-x-auto rounded bg-[#0d1117] p-2 text-xs text-[#e6edf3] whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
                {tryFormatJSON(toolCall.result)}
              </pre>
            </div>
          )}

          {/* Running indicator */}
          {isRunning && !toolCall.result && (
            <p className="text-xs text-[#8b949e] italic">
              正在获取结果...
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default ToolCallStatus;
