/**
 * Root application component.
 * Configures React Router with lazy-loaded page components
 * and wraps everything in the AppShell layout.
 */

import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { Skeleton } from "@/components/ui/skeleton";

// ── Lazy-loaded page components ─────────────────────────────────────

const BaziCalculator = lazy(() => import("@/pages/BaziCalculator"));
const ChartVisualization = lazy(() => import("@/pages/ChartVisualization"));
const LuckPillars = lazy(() => import("@/pages/LuckPillars"));
const AnnualForecast = lazy(() => import("@/pages/AnnualForecast"));
const ElementsAnalysis = lazy(() => import("@/pages/ElementsAnalysis"));
const TenGods = lazy(() => import("@/pages/TenGods"));
const ShenSha = lazy(() => import("@/pages/ShenSha"));
const AIReading = lazy(() => import("@/pages/AIReading"));
const Chat = lazy(() => import("@/pages/Chat"));
const Settings = lazy(() => import("@/pages/Settings"));

// ── Loading fallback ────────────────────────────────────────────────

function PageSkeleton() {
  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-96" />
      <div className="grid gap-6 md:grid-cols-2 mt-8">
        <Skeleton className="h-48 rounded-lg" />
        <Skeleton className="h-48 rounded-lg" />
      </div>
    </div>
  );
}

// ── App component ───────────────────────────────────────────────────

export default function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route element={<AppShell />}>
          {/* 命理 – Bazi Core */}
          <Route path="/" element={<BaziCalculator />} />
          <Route path="/chart" element={<ChartVisualization />} />
          <Route path="/luck-pillars" element={<LuckPillars />} />
          <Route path="/annual" element={<AnnualForecast />} />

          {/* 分析 – Analysis */}
          <Route path="/elements" element={<ElementsAnalysis />} />
          <Route path="/ten-gods" element={<TenGods />} />
          <Route path="/shensha" element={<ShenSha />} />

          {/* 咨询 – AI */}
          <Route path="/ai-reading" element={<AIReading />} />
          <Route path="/chat" element={<Chat />} />

          {/* 设置 – Settings */}
          <Route path="/settings" element={<Settings />} />

          {/* 404 fallback */}
          <Route
            path="*"
            element={
              <div className="flex flex-col items-center justify-center py-24 animate-fade-in">
                <h1 className="font-heading text-4xl text-gold">404</h1>
                <p className="mt-2 text-muted-foreground">
                  此路不通 – The path does not exist.
                </p>
              </div>
            }
          />
        </Route>
      </Routes>
    </Suspense>
  );
}
