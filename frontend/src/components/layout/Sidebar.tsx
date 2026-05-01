/**
 * Sidebar navigation component with mystical-themed icons.
 * Provides navigation to all 10 pages of the Bazi application.
 */

import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

/** Navigation item definition. */
interface NavItem {
  label: string;
  path: string;
  icon: string;
  description?: string;
}

/** Primary navigation sections. */
const NAV_SECTIONS: { title: string; items: NavItem[] }[] = [
  {
    title: "命理",
    items: [
      { label: "排盘", path: "/", icon: "☰", description: "Bazi Chart Calculator" },
      { label: "命盘", path: "/chart", icon: "☷", description: "Chart Visualization" },
      { label: "大运", path: "/luck-pillars", icon: "☳", description: "Luck Pillars" },
      { label: "流年", path: "/annual", icon: "☴", description: "Annual Forecast" },
    ],
  },
  {
    title: "分析",
    items: [
      { label: "五行", path: "/elements", icon: "☲", description: "Five Elements Analysis" },
      { label: "十神", path: "/ten-gods", icon: "☵", description: "Ten Gods" },
      { label: "神煞", path: "/shensha", icon: "☶", description: "Shen Sha Stars" },
    ],
  },
  {
    title: "咨询",
    items: [
      { label: "AI 解读", path: "/ai-reading", icon: "☱", description: "AI Consultation" },
      { label: "问事", path: "/chat", icon: "☰", description: "Chat with AI" },
    ],
  },
  {
    title: "设置",
    items: [
      { label: "设置", path: "/settings", icon: "⚙", description: "Settings" },
    ],
  },
];

export function Sidebar() {
  return (
    <aside
      className={cn(
        "flex h-full w-56 flex-col border-r border-border",
        "bg-sidebar text-sidebar-foreground"
      )}
    >
      {/* Logo / Brand */}
      <div className="flex items-center gap-2 px-4 py-5">
        <span className="text-2xl text-gold animate-pulse-glow">☰</span>
        <div className="flex flex-col">
          <span className="font-heading text-lg font-semibold tracking-wide text-gold">
            玄冥
          </span>
          <span className="text-xs text-muted-foreground tracking-widest uppercase">
            Ming Matrix
          </span>
        </div>
      </div>

      <Separator />

      {/* Navigation */}
      <ScrollArea className="flex-1 px-2 py-3">
        <nav className="flex flex-col gap-4">
          {NAV_SECTIONS.map((section) => (
            <div key={section.title}>
              <h3 className="mb-1 px-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {section.title}
              </h3>
              <ul className="flex flex-col gap-0.5">
                {section.items.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      end={item.path === "/"}
                      className={({ isActive }) =>
                        cn(
                          "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                          "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                          isActive
                            ? "bg-sidebar-accent text-sidebar-primary font-medium"
                            : "text-sidebar-foreground"
                        )
                      }
                      title={item.description}
                    >
                      <span className="text-base" aria-hidden="true">
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </ScrollArea>

      {/* Footer */}
      <Separator />
      <div className="px-4 py-3 text-xs text-muted-foreground">
        <p className="font-heading">玄冥 | Ming Matrix</p>
        <p className="mt-0.5">v0.1.0 &middot; Four Pillars of Destiny</p>
      </div>
    </aside>
  );
}

export default Sidebar;
