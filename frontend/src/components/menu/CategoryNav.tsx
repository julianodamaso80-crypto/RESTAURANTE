"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { PublicCategory } from "@/types/api";

export function CategoryNav({
  categories,
}: {
  categories: PublicCategory[];
}) {
  const [active, setActive] = useState(categories[0]?.id);

  function scrollTo(id: string) {
    setActive(id);
    document
      .getElementById(`cat-${id}`)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <nav className="sticky top-0 z-40 bg-[#0F0A06]/95 backdrop-blur border-b border-[#3D2B1A] overflow-x-auto">
      <div className="flex gap-0 px-4 min-w-max">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => scrollTo(cat.id)}
            className={cn(
              "px-4 py-3 text-sm font-mono uppercase tracking-wider transition-colors whitespace-nowrap border-b-2",
              active === cat.id
                ? "text-[#F97316] border-[#F97316]"
                : "text-[#7C5C3E] border-transparent hover:text-[#D6B896]",
            )}
          >
            {cat.name}
          </button>
        ))}
      </div>
    </nav>
  );
}
