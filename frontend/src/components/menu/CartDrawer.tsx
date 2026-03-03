"use client";

import { X, Plus, Minus, Trash2 } from "lucide-react";
import { useCartStore } from "@/store/cart";
import { formatCurrency } from "@/lib/utils";

export function CartDrawer() {
  const items = useCartStore((s) => s.items);
  const isOpen = useCartStore((s) => s.isOpen);
  const closeCart = useCartStore((s) => s.closeCart);
  const removeItem = useCartStore((s) => s.removeItem);
  const updateQuantity = useCartStore((s) => s.updateQuantity);
  const clearCart = useCartStore((s) => s.clearCart);
  const totalPrice = useCartStore((s) => s.totalPrice);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/60" onClick={closeCart} />
      <div className="relative w-full max-w-sm bg-[#1A1208] border-l border-[#3D2B1A] h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#3D2B1A]">
          <h2 className="text-[#FFF7ED] font-semibold">Seu pedido</h2>
          <button
            onClick={closeCart}
            className="text-[#7C5C3E] hover:text-[#FFF7ED]"
          >
            <X size={20} />
          </button>
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {items.length === 0 ? (
            <p className="text-[#7C5C3E] text-sm text-center py-8">
              Carrinho vazio
            </p>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="bg-[#251A0E] border border-[#3D2B1A] rounded p-3"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-[#FFF7ED] text-sm font-semibold">
                      {item.product.name}
                    </h4>
                    {item.selectedModifiers.length > 0 && (
                      <p className="text-[#7C5C3E] text-xs mt-0.5">
                        {item.selectedModifiers
                          .map((m) => m.name)
                          .join(", ")}
                      </p>
                    )}
                    {item.notes && (
                      <p className="text-[#7C5C3E] text-xs italic mt-0.5">
                        {item.notes}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => removeItem(item.id)}
                    className="text-[#7C5C3E] hover:text-red-400 shrink-0"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() =>
                        updateQuantity(item.id, item.quantity - 1)
                      }
                      className="w-6 h-6 rounded border border-[#3D2B1A] flex items-center justify-center text-[#D6B896] hover:border-[#F97316]"
                    >
                      <Minus size={12} />
                    </button>
                    <span className="font-mono text-[#FFF7ED] text-sm w-4 text-center">
                      {item.quantity}
                    </span>
                    <button
                      onClick={() =>
                        updateQuantity(item.id, item.quantity + 1)
                      }
                      className="w-6 h-6 rounded border border-[#3D2B1A] flex items-center justify-center text-[#D6B896] hover:border-[#F97316]"
                    >
                      <Plus size={12} />
                    </button>
                  </div>
                  <span className="font-mono font-bold text-[#FBBF24] text-sm">
                    {formatCurrency(item.totalPrice)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className="border-t border-[#3D2B1A] p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[#D6B896] text-sm">Total</span>
              <span className="font-mono font-bold text-[#FBBF24] text-lg">
                {formatCurrency(totalPrice())}
              </span>
            </div>
            <button
              onClick={clearCart}
              className="w-full text-[#7C5C3E] text-xs hover:text-red-400 transition-colors"
            >
              Limpar carrinho
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
