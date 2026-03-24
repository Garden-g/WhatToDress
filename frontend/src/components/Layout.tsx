import { History, MessageSquareText, Shirt, Sparkles } from "lucide-react";
import { startTransition, type ReactNode } from "react";

import type { TabKey } from "../types";

interface LayoutProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  children: ReactNode;
}

interface NavItemProps {
  icon: ReactNode;
  label: string;
  isActive: boolean;
  onClick: () => void;
}

function NavItem({ icon, label, isActive, onClick }: NavItemProps) {
  return (
    <button
      onClick={() => startTransition(onClick)}
      className={`flex md:w-full items-center gap-3 px-4 py-3 md:py-3.5 rounded-2xl md:rounded-xl transition-all font-medium text-sm md:mb-2 ${
        isActive
          ? "bg-[color:rgba(44,36,29,0.95)] text-white shadow-md"
          : "text-[color:var(--muted)] hover:bg-[color:rgba(157,111,61,0.08)] hover:text-[color:var(--ink)]"
      }`}
    >
      {icon}
      <span className="hidden md:inline">{label}</span>
    </button>
  );
}

export function Layout({ activeTab, onTabChange, children }: LayoutProps) {
  return (
    <div className="page-shell min-h-screen text-[color:var(--ink)]">
      <nav className="fixed bottom-0 w-full md:top-0 md:bottom-auto md:w-72 md:h-screen bg-[rgba(252,248,242,0.96)] backdrop-blur border-t md:border-r border-[color:var(--line)] z-50 flex md:flex-col justify-around md:justify-start md:px-6 md:py-8 shadow-[0_-4px_20px_-15px_rgba(44,36,29,0.2)] md:shadow-none">
        <div className="hidden md:block mb-10">
          <h1 className="display-title text-4xl font-bold tracking-tight flex items-center gap-2 text-[color:var(--ink)]">
            <span className="bg-[color:rgba(44,36,29,0.95)] text-white p-1.5 rounded-lg">
              <Sparkles className="w-5 h-5" />
            </span>
            Closet OS
          </h1>
          <p className="text-sm text-[color:var(--muted)] mt-3 font-medium">
            不是更会买衣服，而是更会重新穿回你已经拥有的衣服。
          </p>
        </div>

        <div className="flex md:flex-col w-full">
          <NavItem
            icon={<Sparkles className="w-5 h-5" />}
            label="智能穿搭"
            isActive={activeTab === "recommend"}
            onClick={() => onTabChange("recommend")}
          />
          <NavItem
            icon={<MessageSquareText className="w-5 h-5" />}
            label="对话问衣"
            isActive={activeTab === "chat"}
            onClick={() => onTabChange("chat")}
          />
          <NavItem
            icon={<Shirt className="w-5 h-5" />}
            label="我的衣柜"
            isActive={activeTab === "wardrobe"}
            onClick={() => onTabChange("wardrobe")}
          />
          <NavItem
            icon={<History className="w-5 h-5" />}
            label="穿搭历史"
            isActive={activeTab === "history"}
            onClick={() => onTabChange("history")}
          />
        </div>
      </nav>

      <main className="md:ml-72 p-4 md:p-8 max-w-7xl mx-auto min-h-screen pb-24 md:pb-10">
        {children}
      </main>
    </div>
  );
}
