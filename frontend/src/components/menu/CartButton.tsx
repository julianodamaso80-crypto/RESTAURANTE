"use client";

import { ShoppingBag } from "lucide-react";
import { useCartStore } from "@/store/cart";
import { formatCents } from "@/lib/utils";

export function CartButton() {
  const openCart = useCartStore((s) => s.openCart);
  const totalItems = useCartStore((s) => s.totalItems);
  const totalPriceCents = useCartStore((s) => s.totalPriceCents);

  const count = totalItems();
  if (count === 0) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40">
      <button
        onClick={openCart}
        className="flex items-center gap-3 bg-[#F97316] text-black rounded-full px-6 py-3 shadow-2xl font-bold text-sm"
      >
        <div className="relative">
          <ShoppingBag size={18} />
          <span className="absolute -top-2 -right-2 w-4 h-4 bg-black text-white rounded-full text-[10px] flex items-center justify-center font-mono">
            {count}
          </span>
        </div>
        <span>Ver carrinho</span>
        <span className="font-mono">{formatCents(totalPriceCents())}</span>
      </button>
    </div>
  );
}
