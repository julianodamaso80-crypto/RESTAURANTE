"use client";

import { useState } from "react";
import Image from "next/image";
import { formatCurrency } from "@/lib/utils";
import { Plus } from "lucide-react";
import { ProductModal } from "./ProductModal";
import type { Product } from "@/types/api";

export function ProductCard({ product }: { product: Product }) {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setModalOpen(true)}
        className="w-full text-left flex items-center gap-4 p-4 rounded border border-[#3D2B1A] bg-[#1A1208] hover:bg-[#251A0E] transition-colors group"
      >
        <div className="flex-1 min-w-0">
          <h3 className="text-[#FFF7ED] font-semibold text-sm leading-snug mb-1">
            {product.name}
          </h3>
          {product.description && (
            <p className="text-[#7C5C3E] text-xs line-clamp-2 mb-2">
              {product.description}
            </p>
          )}
          <p className="font-mono font-bold text-[#FBBF24] text-sm">
            {formatCurrency(product.base_price)}
          </p>
        </div>

        <div className="relative shrink-0">
          {product.image_url ? (
            <Image
              src={product.image_url}
              alt={product.name}
              width={80}
              height={80}
              className="w-20 h-20 rounded bg-[#251A0E] border border-[#3D2B1A] object-cover"
            />
          ) : (
            <div className="w-20 h-20 rounded bg-[#251A0E] border border-[#3D2B1A] flex items-center justify-center">
              <span className="text-3xl">🍽️</span>
            </div>
          )}
          <div className="absolute -bottom-1 -right-1 w-7 h-7 bg-[#F97316] rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
            <Plus size={16} className="text-black" />
          </div>
        </div>
      </button>

      {modalOpen && (
        <ProductModal product={product} onClose={() => setModalOpen(false)} />
      )}
    </>
  );
}
