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
        className="w-full text-left bg-background-secondary border border-border rounded-lg p-3.5 hover:border-border-light hover:shadow-elevation-1 transition-all duration-200 group"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-sm">{CHANNEL_ICON[order.channel] ?? "\u{1F4E6}"}</span>
            <span className="font-semibold text-foreground text-sm">{order.display_id}</span>
          </div>
          <span className="text-muted text-xs">{timeAgo(order.created_at)}</span>
        </div>
        <p className="text-muted text-xs line-clamp-2 mb-2.5 leading-relaxed">
          {order.items?.map((i) => `${i.quantity}x ${i.name}`).join(", ")}
        </p>
        <div className="flex items-center justify-between">
          <span className="font-semibold text-primary text-sm tabular-nums">{formatCurrency(order.total)}</span>
          <ChevronRight size={14} className="text-muted group-hover:text-foreground transition-colors" />
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
