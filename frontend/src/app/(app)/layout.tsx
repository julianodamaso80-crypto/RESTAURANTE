"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { Sidebar } from "@/components/layout/Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.access_token);
  const [sidebarWidth, setSidebarWidth] = useState("ml-60");

  useEffect(() => {
    if (!accessToken) {
      router.replace("/login");
    }
  }, [accessToken, router]);

  // Observe sidebar collapsed state
  useEffect(() => {
    const observer = new MutationObserver(() => {
      const aside = document.querySelector("aside");
      if (aside) {
        setSidebarWidth(aside.dataset.collapsed === "true" ? "ml-16" : "ml-60");
      }
    });

    const aside = document.querySelector("aside");
    if (aside) {
      setSidebarWidth(aside.dataset.collapsed === "true" ? "ml-16" : "ml-60");
      observer.observe(aside, { attributes: true, attributeFilter: ["data-collapsed"] });
    }

    return () => observer.disconnect();
  }, [accessToken]);

  if (!accessToken) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className={`${sidebarWidth} transition-all duration-300 min-h-screen`}>
        {children}
      </main>
    </div>
  );
}
