/**
 * DayunTimeline -- ECharts horizontal bar chart showing
 * each 10-year luck pillar (大运) period on a timeline.
 * The current period is highlighted in crimson (#e94560).
 */

import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { getCharColor } from "@/lib/wuxing-colors";
import type { DayunEntry } from "@/types/bazi";

// ── Props ─────────────────────────────────────────────────────────

export interface DayunTimelineProps {
  /** Dayun luck pillar entries. */
  dayun: DayunEntry[];
  /** Chart height in pixels. */
  height?: number;
}

// ── Component ─────────────────────────────────────────────────────

export default function DayunTimeline({
  dayun,
  height = 360,
}: DayunTimelineProps) {
  const option = useMemo(() => {
    if (dayun.length === 0) {
      return {
        backgroundColor: "transparent",
        title: {
          text: "暂无大运数据",
          left: "center",
          top: "center",
          textStyle: { color: "#8b949e", fontSize: 14 },
        },
      };
    }

    // Y-axis: ganzhi labels (reversed so earliest is at top)
    const categories = [...dayun].reverse().map((d) => d.ganzhi);

    // Bar data: each entry spans start_year -> end_year
    const currentIdx = dayun.findIndex((d) => d.is_current);
    const data = [...dayun].reverse().map((d, i) => {
      const revIdx = dayun.length - 1 - i;
      const isCurrent = revIdx === currentIdx;
      return {
        value: [d.start_year, revIdx, d.end_year],
        itemStyle: {
          color: isCurrent ? "#e94560" : "#d4af37",
          borderRadius: [0, 4, 4, 0],
        },
      };
    });

    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        backgroundColor: "#161b22",
        borderColor: "#30363d",
        textStyle: { color: "#e6edf3" },
        formatter: (params: { value: number[]; dataIndex: number }) => {
          const revIdx = dayun.length - 1 - params.dataIndex;
          const d = dayun[revIdx];
          if (!d) return "";
          const current = d.is_current ? " (当前)" : "";
          const stemColor = getCharColor(d.stem);
          const branchColor = getCharColor(d.branch);
          return `
            <strong>${d.ganzhi}</strong>${current}<br/>
            <span style="color:${stemColor}">${d.stem}</span>
            <span style="color:${branchColor}">${d.branch}</span><br/>
            ${d.start_year} - ${d.end_year} 年<br/>
            ${d.start_age} - ${d.end_age} 岁
          `;
        },
      },
      grid: {
        left: 80,
        right: 40,
        top: 16,
        bottom: 32,
      },
      xAxis: {
        type: "value",
        axisLabel: { color: "#8b949e", fontSize: 11 },
        axisLine: { lineStyle: { color: "#30363d" } },
        splitLine: { lineStyle: { color: "#30363d", type: "dashed" } },
      },
      yAxis: {
        type: "category",
        data: categories,
        axisLine: { lineStyle: { color: "#30363d" } },
        axisTick: { show: false },
        axisLabel: { color: "#e6edf3", fontSize: 13, fontWeight: "bold" },
      },
      series: [
        {
          type: "custom",
          renderItem: (
            _params: { coordSys: { x: number; y: number; width: number; height: number } },
            api: {
              value: (dim: number) => number;
              coord: (val: number[]) => number[];
              size: (size: [number, number]) => number[];
              style: () => Record<string, unknown>;
            }
          ) => {
            const startVal = api.value(0);
            const catIdx = api.value(1);
            const endVal = api.value(2);
            const startCoord = api.coord([startVal, catIdx]);
            const endCoord = api.coord([endVal, catIdx]);
            const barHeight = api.size([0, 1])[1] * 0.6;
            const x = startCoord[0];
            const y = startCoord[1] - barHeight / 2;
            const width = endCoord[0] - startCoord[0];

            const style = api.style();
            return {
              type: "rect",
              shape: { x, y, width, height: barHeight, r: 4 },
              style,
            };
          },
          data,
          encode: { x: [0, 2], y: 1 },
        },
      ],
    };
  }, [dayun]);

  return (
    <ReactECharts
      option={option}
      style={{ height, width: "100%" }}
      opts={{ renderer: "canvas" }}
      notMerge
    />
  );
}
