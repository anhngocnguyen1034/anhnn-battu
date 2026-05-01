/**
 * Response adapter – transforms backend API responses into frontend types.
 *
 * The backend returns flat arrays (pillars, tg_gan, wuxing, etc.)
 * while the frontend expects nested objects (BaziChart, BaziReading, etc.).
 * This module bridges the gap without changing either side.
 */

import type {
  BaziChart,
  BaziReading,
  Pillar,
  TenGod,
  DayunEntry,
  AnnualPillar,
  PillarAnnotations,
  WuxingPower,
  ElementBalance,
} from "@/types/bazi";

// ── Wuxing helpers ──────────────────────────────────────────────────────

const GAN_TO_WUXING: Record<string, string> = {
  甲: "木", 乙: "木", 丙: "火", 丁: "火", 戊: "土",
  己: "土", 庚: "金", 辛: "金", 壬: "水", 癸: "水",
};

const ZHI_TO_WUXING: Record<string, string> = {
  子: "水", 丑: "土", 寅: "木", 卯: "木", 辰: "土", 巳: "火",
  午: "火", 未: "土", 申: "金", 酉: "金", 戌: "土", 亥: "水",
};

const ZHI_HIDDEN_STEMS: Record<string, string[]> = {
  子: ["癸"], 丑: ["己", "癸", "辛"], 寅: ["甲", "丙", "戊"],
  卯: ["乙"], 辰: ["戊", "乙", "癸"], 巳: ["丙", "庚", "戊"],
  午: ["丁", "己"], 未: ["己", "丁", "乙"], 申: ["庚", "壬", "戊"],
  酉: ["辛"], 戌: ["戊", "辛", "丁"], 亥: ["壬", "甲"],
};

/**
 * Parse a two-character ganzhi string into stem + branch.
 */
function parseGanzhi(gz: string): { stem: string; branch: string } {
  return { stem: gz[0] ?? "", branch: gz[1] ?? "" };
}

/**
 * Extract the Chinese element character from a wuxing key.
 * Engine returns keys like "金(Metal)", "木(Wood)", etc.
 * This extracts just the first character: "金", "木", etc.
 */
function extractElement(key: string): string {
  return key.charAt(0);
}

// ── Main adapter ────────────────────────────────────────────────────────

interface BackendChartResponse {
  chart: {
    gender?: string;
    pillars?: string[];
    tg_gan?: string[];
    tg_zhi?: string[];
    nayin?: string[];
    shensha?: string[];
    shensha_detail?: Record<string | number, unknown>;
    wuxing?: Record<string, number>;
    dayun?: Array<{ start_age?: number; start_year?: number; ganzhi?: string }>;
    minggong?: string;
    taiyuan?: string;
    taixi?: string;
    shengong?: string;
    dishi?: string[];
    xunkong?: string[];
    xingchong?: Record<string, string[]>;
    wuxing_str?: string;
    day_master?: string;
    [key: string]: unknown;
  };
  wuxing_power?: {
    power?: Record<string, number>;
    strong?: string[];
    weak?: string[];
    balanced?: boolean;
    context?: string;
  } | null;
  geju?: Record<string, unknown> | null;
}

/**
 * Transform a backend /api/v1/chart response into a frontend BaziReading.
 */
export function adaptChartResponse(response: BackendChartResponse): BaziReading {
  const raw = response.chart;
  const pillars = raw.pillars ?? [];
  const tgGan = raw.tg_gan ?? [];
  const tgZhi = raw.tg_zhi ?? [];
  const nayin = raw.nayin ?? [];

  // Helper: build a Pillar from a 2-char ganzhi string.
  function buildPillar(index: number): Pillar {
    const gz = pillars[index] ?? "";
    const { stem, branch } = parseGanzhi(gz);
    return {
      stem,
      branch,
      hidden_stems: ZHI_HIDDEN_STEMS[branch] ?? [],
      element: GAN_TO_WUXING[stem] ?? "",
      nayin: nayin[index],
    };
  }

  const dayMaster = raw.day_master ?? parseGanzhi(pillars[2] ?? "").stem;
  const dayMasterElement = GAN_TO_WUXING[dayMaster] ?? "";

  const chart: BaziChart = {
    year_pillar: buildPillar(0),
    month_pillar: buildPillar(1),
    day_pillar: buildPillar(2),
    hour_pillar: buildPillar(3),
    day_master: dayMaster,
    day_master_element: dayMasterElement,
  };

  // Element balance from wuxing dict.
  // Engine returns keys like "金(Metal)" — normalize to just "金".
  const wuxingRaw = raw.wuxing ?? {};
  const wuxing: Record<string, number> = {};
  for (const [k, v] of Object.entries(wuxingRaw)) {
    wuxing[extractElement(k)] = v as number;
  }
  const element_balance: ElementBalance = {
    金: wuxing["金"] ?? 0,
    木: wuxing["木"] ?? 0,
    水: wuxing["水"] ?? 0,
    火: wuxing["火"] ?? 0,
    土: wuxing["土"] ?? 0,
  };

  // Ten gods from tg_gan and tg_zhi.
  const allChars = [
    chart.year_pillar.stem, chart.year_pillar.branch,
    chart.month_pillar.stem, chart.month_pillar.branch,
    chart.day_pillar.stem, chart.day_pillar.branch,
    chart.hour_pillar.stem, chart.hour_pillar.branch,
  ];
  const allGodNames = [
    tgGan[0], tgZhi[0],
    tgGan[1], tgZhi[1],
    tgGan[2], tgZhi[2],
    tgGan[3], tgZhi[3],
  ];

  const ten_gods: TenGod[] = [];
  const seenGods = new Set<string>();

  // Determine favorable elements from wuxing_power.
  const wp = response.wuxing_power;
  const favorableSet = new Set<string>();
  if (wp?.weak?.length) {
    // Weak day master needs support → weak elements are favorable.
    for (const el of wp.weak) favorableSet.add(el);
  }

  for (let i = 0; i < allChars.length; i++) {
    const char = allChars[i];
    const godName = allGodNames[i];
    if (char && godName) {
      const el = GAN_TO_WUXING[char] ?? ZHI_TO_WUXING[char] ?? "";
      ten_gods.push({
        name: godName,
        character: char,
        element: el,
        is_favorable: favorableSet.size === 0 ? true : favorableSet.has(el),
      });
      if (!seenGods.has(godName)) seenGods.add(godName);
    }
  }

  // Dayun (luck pillars).
  const dayun_raw = raw.dayun ?? [];
  const dayun: DayunEntry[] = dayun_raw.map((d, i) => {
    const gz = d.ganzhi ?? "";
    const { stem, branch } = parseGanzhi(gz);
    const next = dayun_raw[i + 1];
    const endAge = next?.start_age ? next.start_age - 1 : (d.start_age ?? 0) + 9;
    const endYear = next?.start_year ? next.start_year - 1 : (d.start_year ?? 0) + 9;
    return {
      stem,
      branch,
      ganzhi: gz,
      start_age: d.start_age ?? 0,
      end_age: endAge,
      start_year: d.start_year ?? 0,
      end_year: endYear,
      is_current: false, // Determined by page component based on current year.
    };
  });

  // Annual pillars: derive from dayun year ranges.
  const annual_pillars: AnnualPillar[] = [];
  const currentYear = new Date().getFullYear();
  for (const d of dayun) {
    for (let y = d.start_year; y <= d.end_year && y <= currentYear + 10; y++) {
      // Compute ganzhi for year y using the standard sexagenary cycle.
      // Reference: year 1984 = 甲子 (stem index 0, branch index 0).
      const stemIdx = ((y - 1984) % 10 + 10) % 10;
      const branchIdx = ((y - 1984) % 12 + 12) % 12;
      const stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
      const branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
      const s = stems[stemIdx];
      const b = branches[branchIdx];
      annual_pillars.push({
        year: y,
        stem: s,
        branch: b,
        element: GAN_TO_WUXING[s] ?? "",
      });
    }
  }

  // Wuxing power for charts.
  const wpower = response.wuxing_power;
  let wuxing_power: WuxingPower | undefined;
  if (wpower?.power) {
    wuxing_power = {
      金: wpower.power["金"] ?? 0,
      木: wpower.power["木"] ?? 0,
      水: wpower.power["水"] ?? 0,
      火: wpower.power["火"] ?? 0,
      土: wpower.power["土"] ?? 0,
    };
  }

  // Pillar annotations.
  const pillarAnnotations: Record<string, PillarAnnotations> = {};
  const pillarKeys = ["year", "month", "day", "hour"] as const;
  const shenshaDetail = raw.shensha_detail ?? {};
  for (let i = 0; i < 4; i++) {
    const key = pillarKeys[i];
    const shenshaForPillar = Array.isArray(shenshaDetail[i])
      ? (shenshaDetail[i] as string[])
      : Array.isArray(shenshaDetail[key])
        ? (shenshaDetail[key] as string[])
        : [];
    pillarAnnotations[key] = {
      ten_god_gan: tgGan[i] ?? "",
      ten_god_zhi: tgZhi[i] ?? "",
      nayin: nayin[i] ?? "",
      shensha: shenshaForPillar,
      dishi: raw.dishi?.[i] ?? "",
      xunkong: raw.xunkong?.[i] ?? "",
    };
  }

  // Strengths and weaknesses from wuxing_power.
  const strengths: string[] = [];
  const weaknesses: string[] = [];
  if (wpower?.strong?.length) {
    strengths.push(`五行偏强: ${wpower.strong.join("、")}`);
  }
  if (wpower?.weak?.length) {
    weaknesses.push(`五行偏弱: ${wpower.weak.join("、")}`);
  }
  if (wpower?.balanced) {
    strengths.push("五行较为平衡");
  }

  // Favorable / unfavorable elements.
  const favorable_elements: string[] = [];
  const unfavorable_elements: string[] = [];
  if (wpower?.weak?.length) {
    // Weak day master needs support → weak elements are favorable.
    favorable_elements.push(...wpower.weak);
  }
  if (wpower?.strong?.length) {
    // Strong day master needs restraint → strong elements are unfavorable.
    unfavorable_elements.push(...wpower.strong);
  }

  // Geju info as summary context.
  const geju = response.geju;
  let summary = "";
  if (geju) {
    const parts: string[] = [];
    if (geju["格局类型"]) parts.push(`格局: ${geju["格局类型"]}`);
    if (geju["格局名称"]) parts.push(`${geju["格局名称"]}`);
    if (geju["日主强弱"]) parts.push(`日主${geju["日主强弱"]}`);
    if (geju["context"]) parts.push(geju["context"] as string);
    summary = parts.join("。");
  }

  // Xingchong as string array.
  const xingchong: string[] = [];
  if (raw.xingchong) {
    for (const [key, values] of Object.entries(raw.xingchong)) {
      if (Array.isArray(values)) {
        for (const v of values) {
          xingchong.push(`${key}: ${v}`);
        }
      }
    }
  }

  // All shensha.
  const all_shensha: BaziReading["all_shensha"] = [];
  const shenshaList = raw.shensha ?? [];
  const pillarLabels = ["年柱", "月柱", "日柱", "时柱"] as const;
  for (let i = 0; i < shenshaList.length; i++) {
    all_shensha.push({
      name: shenshaList[i],
      pillar: pillarLabels[Math.min(i, 3)],
      description: "",
    });
  }

  return {
    chart,
    element_balance,
    ten_gods,
    luck_pillars: dayun.map((d) => ({
      age_range: `${d.start_age}-${d.end_age}岁`,
      stem: d.stem,
      branch: d.branch,
      element: GAN_TO_WUXING[d.stem] ?? "",
      start_year: d.start_year,
      end_year: d.end_year,
    })),
    annual_pillars,
    strengths,
    weaknesses,
    favorable_elements,
    unfavorable_elements,
    summary,
    gender: raw.gender,
    pillar_annotations: pillarAnnotations,
    wuxing_power,
    dayun,
    ming_gong: raw.minggong,
    tai_yuan: raw.taiyuan,
    shen_gong: raw.shengong,
    tai_xi: raw.taixi,
    geju: geju
      ? {
          geju_type: (geju["格局类型"] as string) ?? "",
          description: (geju["context"] as string) ?? "",
          favorable_elements: favorable_elements,
          unfavorable_elements: unfavorable_elements,
        }
      : undefined,
    xingchong,
    all_shensha,
  };
}
