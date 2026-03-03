"use client";

import { useState } from "react";
import { formatCurrency, timeAgo } from "@/lib/utils";
import { ChevronRight } from "lucide-react";
import { OrderDetailDrawer } from "./OrderDetailDrawer";
import type { Order } from "@/types/api";

const CHANNEL_ICON: Record<string, string> = {
  OWN: "\u{1F3EA}",
  IFOOD: "\u{1F7E5}",
  "99FOOD": "\u{1F7E1}",
};

export function OrderCard({ order, onUpdate }: { order: Order; onUpdate: () => void }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="w-full text-left bg-surface border border-border rounded p-3 hover:border-muted transition-colors group"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span>{CHANNEL_ICON[order.channel] ?? "\u{1F4E6}"}</span>
            <span className="font-mono font-bold text-foreground text-sm">{order.display_id}</span>
          </div>
          <span className="text-muted text-xs font-mono">{timeAgo(order.created_at)}</span>
        </div>
        <p className="text-muted text-xs line-clamp-2 mb-2">
          {order.items?.map((i) => `${i.quantity}x ${i.name}`).join(", ")}
        </p>
        <div className="flex items-center justify-between">
          <span className="font-mono font-bold text-accent text-sm">{formatCurrency(order.total)}</span>
          <ChevronRight size={14} className="text-muted group-hover:text-foreground" />
        </div>
      </button>
      {open && (
        <OrderDetailDrawer
          order={order}
          onClose={() => setOpen(false)}
          onUpdate={() => {
            onUpdate();
            setOpen(false);
          }}
        />
      )}
    </>
  );
}
