"use client";

import { useState } from "react";
import { X, Plus, Minus } from "lucide-react";
import { formatCents, cn } from "@/lib/utils";
import { useCartStore } from "@/store/cart";
import type { Product, ModifierGroup, ModifierOption } from "@/types/api";

export function ProductModal({
  product,
  catalogId,
  onClose,
}: {
  product: Product;
  catalogId: string;
  onClose: () => void;
}) {
  const [quantity, setQuantity] = useState(1);
  const [selectedModifiers, setSelectedModifiers] = useState<ModifierOption[]>(
    [],
  );
  const [notes, setNotes] = useState("");
  const addItem = useCartStore((s) => s.addItem);

  const modifierTotalCents = selectedModifiers.reduce(
    (sum, m) => sum + m.price_delta_cents,
    0,
  );
  const totalCents = (product.price_cents + modifierTotalCents) * quantity;

  function toggleModifier(option: ModifierOption, group: ModifierGroup) {
    if (selectedModifiers.find((m) => m.id === option.id)) {
      setSelectedModifiers((prev) => prev.filter((m) => m.id !== option.id));
    } else if (group.max_choices === 1) {
      const groupOptionIds = new Set(group.options.map((o) => o.id));
      setSelectedModifiers((prev) => [
        ...prev.filter((m) => !groupOptionIds.has(m.id)),
        option,
      ]);
    } else {
      const groupOptionIds = new Set(group.options.map((o) => o.id));
      const inGroup = selectedModifiers.filter((m) =>
        groupOptionIds.has(m.id),
      );
      if (inGroup.length < group.max_choices) {
        setSelectedModifiers((prev) => [...prev, option]);
      }
    }
  }

  function handleAdd() {
    addItem(product, quantity, selectedModifiers, notes, catalogId);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative w-full sm:max-w-md bg-[#1A1208] border border-[#3D2B1A] rounded-t-2xl sm:rounded-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-[#1A1208] flex items-center justify-between p-4 border-b border-[#3D2B1A]">
          <h2 className="text-[#FFF7ED] font-semibold">{product.name}</h2>
          <button
            onClick={onClose}
            className="text-[#7C5C3E] hover:text-[#FFF7ED]"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {product.description && (
            <p className="text-[#7C5C3E] text-sm">{product.description}</p>
          )}

          {/* Modifier groups */}
          {product.modifier_groups?.map((group) => (
            <div key={group.id}>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-[#D6B896] text-sm font-semibold">
                  {group.name}
                </h3>
                <span className="text-[#7C5C3E] text-xs">
                  {group.min_choices > 0 ? "Obrigatorio" : "Opcional"}
                </span>
              </div>
              <div className="space-y-1">
                {group.options.map((option) => {
                  const selected = selectedModifiers.some(
                    (m) => m.id === option.id,
                  );
                  return (
                    <button
                      key={option.id}
                      onClick={() => toggleModifier(option, group)}
                      className={cn(
                        "w-full flex items-center justify-between p-3 rounded border text-sm transition-colors",
                        selected
                          ? "bg-[#F97316]/10 border-[#F97316]/30 text-[#FFF7ED]"
                          : "bg-[#251A0E] border-[#3D2B1A] text-[#D6B896] hover:border-[#7C5C3E]",
                      )}
                    >
                      <span>{option.name}</span>
                      {option.price_delta_cents !== 0 && (
                        <span className="font-mono text-[#FBBF24] text-xs">
                          +{formatCents(option.price_delta_cents)}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Notes */}
          <div>
            <label className="text-[#7C5C3E] text-xs block mb-1">
              Observacoes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: sem cebola, ponto da carne..."
              className="w-full bg-[#251A0E] border border-[#3D2B1A] rounded p-3 text-[#FFF7ED] text-sm resize-none focus:outline-none focus:border-[#F97316] placeholder-[#7C5C3E]"
              rows={2}
            />
          </div>
        </div>

        {/* Footer: quantity + add button */}
        <div className="sticky bottom-0 bg-[#1A1208] border-t border-[#3D2B1A] p-4 flex items-center gap-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setQuantity((q) => Math.max(1, q - 1))}
              className="w-8 h-8 rounded border border-[#3D2B1A] flex items-center justify-center text-[#D6B896] hover:border-[#F97316] hover:text-[#F97316]"
            >
              <Minus size={14} />
            </button>
            <span className="font-mono font-bold text-[#FFF7ED] w-6 text-center">
              {quantity}
            </span>
            <button
              onClick={() => setQuantity((q) => q + 1)}
              className="w-8 h-8 rounded border border-[#3D2B1A] flex items-center justify-center text-[#D6B896] hover:border-[#F97316] hover:text-[#F97316]"
            >
              <Plus size={14} />
            </button>
          </div>

          <button
            onClick={handleAdd}
            className="flex-1 bg-[#F97316] text-black font-bold py-3 rounded text-sm"
          >
            Adicionar &middot; {formatCents(totalCents)}
          </button>
        </div>
      </div>
    </div>
  );
}
