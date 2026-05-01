/**
 * PillarCard -- glassmorphism card for a single Bazi pillar.
 * Displays stem (干), branch (支), ten god annotations, hidden stems,
 * nayin, shensha badges, dishi, and xunkong labels.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { WUXING_CHAR_COLORS } from "@/lib/wuxing-colors";

// ── Props ─────────────────────────────────────────────────────────

export interface PillarCardProps {
  /** Pillar label, e.g. "年柱" */
  label: string;
  /** Sub-label describing the pillar's domain, e.g. "祖业" */
  sublabel: string;
  /** Heavenly stem character (天干) */
  stem: string;
  /** Earthly branch character (地支) */
  branch: string;
  /** Hidden stems within the branch */
  hiddenStems: string[];
  /** Ten god for the heavenly stem */
  tenGodGan?: string;
  /** Ten god for the earthly branch */
  tenGodZhi?: string;
  /** Nayin (纳音) element name */
  nayin?: string;
  /** Shensha (神煞) tags */
  shensha?: string[];
  /** Dishi (地势) label */
  dishi?: string;
  /** XunKong (旬空) label */
  xunkong?: string;
  /** Whether to show professional-only fields (dishi, xunkong) */
  isProfessional?: boolean;
}

// ── Helpers ───────────────────────────────────────────────────────

/** Return the wuxing color for a single character. */
function charColor(char: string): string {
  return WUXING_CHAR_COLORS[char] ?? "#e6edf3";
}

// ── Component ─────────────────────────────────────────────────────

export default function PillarCard({
  label,
  sublabel,
  stem,
  branch,
  hiddenStems,
  tenGodGan,
  tenGodZhi,
  nayin,
  shensha = [],
  dishi,
  xunkong,
  isProfessional = false,
}: PillarCardProps) {
  return (
    <Card className="border border-[#30363d] bg-[#161b22]/60 backdrop-blur-md text-[#e6edf3] transition-all hover:border-[#d4af37]/40 hover:shadow-[0_0_12px_rgba(212,175,55,0.15)]">
      <CardHeader className="pb-2 text-center">
        {/* Pillar label */}
        <CardTitle className="text-sm font-medium text-[#8b949e]">
          {label}
        </CardTitle>
        <p className="text-xs text-[#6e7681]">{sublabel}</p>
      </CardHeader>

      <CardContent className="flex flex-col items-center gap-2">
        {/* Ten god for stem */}
        {tenGodGan && (
          <span className="text-xs font-medium text-[#d4af37] tracking-wider">
            {tenGodGan}
          </span>
        )}

        {/* Heavenly Stem (干) -- large, wuxing-colored */}
        <span
          className="text-4xl font-bold leading-none"
          style={{ color: charColor(stem) }}
        >
          {stem}
        </span>

        {/* Ten god for branch */}
        {tenGodZhi && (
          <span className="text-xs font-medium text-[#d4af37]/80 tracking-wider">
            {tenGodZhi}
          </span>
        )}

        {/* Earthly Branch (支) -- large, wuxing-colored */}
        <span
          className="text-4xl font-bold leading-none"
          style={{ color: charColor(branch) }}
        >
          {branch}
        </span>

        {/* Nayin */}
        {nayin && (
          <span className="mt-1 text-xs font-medium text-[#d4af37]">
            {nayin}
          </span>
        )}

        {/* Hidden stems */}
        {hiddenStems.length > 0 && (
          <div className="flex items-center gap-1">
            <span className="text-[10px] text-[#6e7681]">藏干:</span>
            {hiddenStems.map((s, i) => (
              <span
                key={i}
                className="text-xs font-medium"
                style={{ color: charColor(s) }}
              >
                {s}
              </span>
            ))}
          </div>
        )}

        {/* Shensha badges */}
        {shensha.length > 0 && (
          <div className="flex flex-wrap justify-center gap-1 mt-1">
            {shensha.map((ss, i) => (
              <Badge
                key={i}
                variant="secondary"
                className="bg-[#50c878]/15 text-[#50c878] border-[#50c878]/30 text-[10px] px-1.5 py-0"
              >
                {ss}
              </Badge>
            ))}
          </div>
        )}

        {/* Professional-only: Dishi + XunKong */}
        {isProfessional && (
          <div className="mt-1 flex flex-col items-center gap-0.5">
            {dishi && (
              <span className="text-[10px] text-[#8b949e]">{dishi}</span>
            )}
            {xunkong && (
              <span className="text-[10px] text-[#6e7681]">
                旬空: {xunkong}
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
