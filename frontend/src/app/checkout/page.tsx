"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { useCartStore } from "@/store/cart";
import { formatCents, cn } from "@/lib/utils";
import type { PaymentMethod, OrderType } from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CustomerInfo {
  name: string;
  phone: string;
  email: string;
  orderType: OrderType;
  address: {
    street: string;
    number: string;
    neighborhood: string;
    complement: string;
    zipcode: string;
  };
}

export default function CheckoutPage() {
  const router = useRouter();
  const items = useCartStore((s) => s.items);
  const catalogId = useCartStore((s) => s.catalogId);
  const totalPriceCents = useCartStore((s) => s.totalPriceCents);
  const clearCart = useCartStore((s) => s.clearCart);

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Step 1 state
  const [customer, setCustomer] = useState<CustomerInfo>({
    name: "",
    phone: "",
    email: "",
    orderType: "TAKEOUT",
    address: { street: "", number: "", neighborhood: "", complement: "", zipcode: "" },
  });

  // Step 2 state
  const [orderNotes, setOrderNotes] = useState("");
  const [coupon, setCoupon] = useState("");
  const [couponMsg, setCouponMsg] = useState("");

  // Step 3 state
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("PIX");
  const [changeFor, setChangeFor] = useState("");

  // Derived values
  const subtotalCents = totalPriceCents();
  const deliveryFeeCents = customer.orderType === "DELIVERY" ? 0 : 0; // stub
  const totalCents = subtotalCents + deliveryFeeCents;

  // Redirect if cart is empty
  if (items.length === 0 && step === 1) {
    return (
      <div className="min-h-screen bg-[#0F0A06] flex flex-col items-center justify-center gap-4">
        <p className="text-[#7C5C3E] font-mono">Carrinho vazio</p>
        <button
          onClick={() => router.back()}
          className="text-[#F97316] text-sm underline"
        >
          Voltar ao cardapio
        </button>
      </div>
    );
  }

  function validateStep1() {
    if (!customer.name.trim()) return "Nome e obrigatorio.";
    if (!customer.phone.trim()) return "Telefone e obrigatorio.";
    if (customer.orderType === "DELIVERY") {
      const a = customer.address;
      if (!a.street.trim() || !a.number.trim() || !a.neighborhood.trim() || !a.zipcode.trim()) {
        return "Preencha o endereco completo para delivery.";
      }
    }
    return null;
  }

  function handleApplyCoupon() {
    setCouponMsg("Cupom nao encontrado.");
  }

  async function handleConfirmOrder() {
    setLoading(true);
    setError("");

    const payload = {
      catalog_id: catalogId,
      customer_name: customer.name,
      customer_phone: customer.phone,
      customer_email: customer.email,
      order_type: customer.orderType,
      delivery_address: customer.orderType === "DELIVERY" ? customer.address : null,
      payment_method: paymentMethod,
      change_for_cents: paymentMethod === "CASH" && changeFor ? Math.round(parseFloat(changeFor) * 100) : null,
      notes: orderNotes,
      items: items.map((item) => ({
        name: item.product.name,
        quantity: item.quantity,
        unit_price_cents: item.unitPriceCents,
        total_cents: item.totalPriceCents,
        notes: item.notes,
        modifiers_summary: item.selectedModifiers.map((m) => m.name).join(", "),
      })),
    };

    try {
      const res = await fetch(`${BASE_URL}/api/v1/orders/public/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        const detail = errData?.detail || errData?.non_field_errors?.[0] || "Erro ao criar pedido.";
        setError(typeof detail === "string" ? detail : JSON.stringify(detail));
        setLoading(false);
        return;
      }

      const order = await res.json();
      clearCart();
      router.push(`/pedido/${order.id}`);
    } catch {
      setError("Erro de conexao. Tente novamente.");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0F0A06] text-[#FFF7ED]">
      {/* Header */}
      <div className="px-4 py-4 border-b border-[#3D2B1A] flex items-center gap-3">
        <button onClick={() => (step > 1 ? setStep(step - 1) : router.back())} className="text-[#7C5C3E] hover:text-[#FFF7ED]">
          <ArrowLeft size={20} />
        </button>
        <h1 className="font-bold text-lg">Checkout</h1>
        <span className="ml-auto text-[#7C5C3E] text-xs font-mono">
          Etapa {step} de 3
        </span>
      </div>

      {/* Step indicators */}
      <div className="flex gap-1 px-4 py-3">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={cn(
              "flex-1 h-1 rounded-full",
              s <= step ? "bg-[#F97316]" : "bg-[#3D2B1A]",
            )}
          />
        ))}
      </div>

      <div className="max-w-lg mx-auto px-4 pb-32">
        {/* Step 1: Identification */}
        {step === 1 && (
          <div className="space-y-4 py-4">
            <h2 className="text-[#D6B896] font-semibold">Identificacao</h2>

            <div>
              <label className="text-[#7C5C3E] text-xs block mb-1">Nome completo *</label>
              <input
                type="text"
                value={customer.name}
                onChange={(e) => setCustomer({ ...customer, name: e.target.value })}
                className="w-full bg-[#1A1208] border border-[#3D2B1A] rounded p-3 text-[#FFF7ED] text-sm focus:outline-none focus:border-[#F97316]"
                placeholder="Seu nome"
              />
            </div>

            <div>
              <label className="text-[#7C5C3E] text-xs block mb-1">Telefone / WhatsApp *</label>
              <input
                type="tel"
                value={customer.phone}
                onChange={(e) => setCustomer({ ...customer, phone: e.target.value })}
                className="w-full bg-[#1A1208] border border-[#3D2B1A] rounded p-3 text-[#FFF7ED] text-sm focus:outline-none focus:border-[#F97316]"
                placeholder="(11) 99999-9999"
              />
            </div>

            <div>
              <label className="text-[#7C5C3E] text-xs block mb-1">E-mail (opcional)</label>
              <input
                type="email"
                value={customer.email}
                onChange={(e) => setCustomer({ ...customer, email: e.target.value })}
                className="w-full bg-[#1A1208] border border-[#3D2B1A] rounded p-3 text-[#FFF7ED] text-sm focus:outline-none focus:border-[#F97316]"
                placeholder="voce@email.com"
              />
            </div>

            <div>
              <label className="text-[#7C5C3E] text-xs block mb-2">Tipo de entrega</label>
              <div className="flex gap-2">
                {([["TAKEOUT", "Retirada no local"], ["DELIVERY", "Delivery"]] as const).map(([type, label]) => (
                  <button
                    key={type}
                    onClick={() => setCustomer({ ...customer, orderType: type })}
                    className={cn(
                      "flex-1 py-3 rounded border text-sm font-semibold transition-colors",
                      customer.orderType === type
                        ? "bg-[#F97316]/10 border-[#F97316] text-[#F97316]"
                        : "bg-[#1A1208] border-[#3D2B1A] text-[#7C5C3E] hover:border-[#7C5C3E]",
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {customer.orderType === "DELIVERY" && (
              <div className="space-y-3 border border-[#3D2B1A] rounded p-3">
                <h3 className="text-[#D6B896] text-xs font-semibold">Endereco de entrega</h3>
                <input
                  type="text"
                  value={customer.address.street}
                  onChange={(e) => setCustomer({ ...customer, address: { ...customer.address, street: e.target.value } })}
                  className="w-full bg-[#0F0A06] border border-[#3D2B1A] rounded p-2 text-[#FFF7ED] text-sm focus:outline-none focus:border-[#F97316]"
                  placeholder="Rua"
                />
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customer.address.number}
                    onChange={(e) => setCustomer({ ...customer, address: { ...customer.address, number: e.target.value } })}
                    className="w-24 bg-[#0F0A06] border border-[#3D2B1A] rounded p-2 text-[#FFF7ED] text-sm focus:outline-none focus:border-[#F97316]"
                    placeholder="N"
                  />
                  <input
                    type="text"
                    value={customer.address.complement}
                    onChange={(e) => setCustomer({ ...customer, address: { ...customer.address, complement: e.target.value } })}
                    className="flex-1 bg-[#0F0A06] border border-[#3D2B1A] rounded p-2 text-[#FFF7ED] text-sm focus:outline-none focus:border-[#F97316]"
                    placeholder="Complemento"
                  />
                </div>
                <input
                  type="text"
                  value={customer.address.neighborhood}
                  onChange={(e) => setCustomer({ ...customer, address: { ...customer.address, neighborhood: e.target.value } })}
                  className="w-full bg-[#0F0A06] border border-[#3D2B1A] rounded p-2 text-[#FFF7ED] text-sm focus:outline-none focus:border-[#F97316]"
                  placeholder="Bairro"
                />
                <input
                  type="text"
                  value={customer.address.zipcode}
                  onChange={(e) => setCustomer({ ...customer, address: { ...customer.address, zipcode: e.target.value } })}
                  className="w-full bg-[#0F0A06] border border-[#3D2B1A] rounded p-2 text-[#FFF7ED] text-sm focus:outline-none focus:border-[#F97316]"
                  placeholder="CEP"
                />
              </div>
            )}
          </div>
        )}

        {/* Step 2: Order Summary */}
        {step === 2 && (
          <div className="space-y-4 py-4">
            <h2 className="text-[#D6B896] font-semibold">Resumo do pedido</h2>

            <div className="space-y-2">
              {items.map((item) => (
                <div key={item.id} className="bg-[#1A1208] border border-[#3D2B1A] rounded p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[#FFF7ED] text-sm font-semibold">
                        {item.quantity}x {item.product.name}
                      </span>
                      {item.selectedModifiers.length > 0 && (
                        <p className="text-[#7C5C3E] text-xs mt-0.5">
                          {item.selectedModifiers.map((m) => m.name).join(", ")}
                        </p>
                      )}
                    </div>
                    <span className="font-mono text-[#FBBF24] text-sm">
                      {formatCents(item.totalPriceCents)}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div>
              <label className="text-[#7C5C3E] text-xs block mb-1">Observacao geral</label>
              <textarea
                value={orderNotes}
                onChange={(e) => setOrderNotes(e.target.value)}
                className="w-full bg-[#1A1208] border border-[#3D2B1A] rounded p-3 text-[#FFF7ED] text-sm resize-none focus:outline-none focus:border-[#F97316]"
                rows={2}
                placeholder="Alguma observacao para o restaurante?"
              />
            </div>

            <div>
              <label className="text-[#7C5C3E] text-xs block mb-1">Cupom de desconto</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={coupon}
                  onChange={(e) => { setCoupon(e.target.value); setCouponMsg(""); }}
                  className="flex-1 bg-[#1A1208] border border-[#3D2B1A] rounded p-3 text-[#FFF7ED] text-sm focus:outline-none focus:border-[#F97316]"
                  placeholder="CODIGO"
                />
                <button
                  onClick={handleApplyCoupon}
                  className="px-4 py-2 bg-[#251A0E] border border-[#3D2B1A] rounded text-[#D6B896] text-sm hover:border-[#F97316]"
                >
                  Aplicar
                </button>
              </div>
              {couponMsg && <p className="text-red-400 text-xs mt-1">{couponMsg}</p>}
            </div>

            <div className="border-t border-[#3D2B1A] pt-3 space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-[#7C5C3E]">Subtotal</span>
                <span className="font-mono text-[#FFF7ED]">{formatCents(subtotalCents)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#7C5C3E]">Taxa de entrega</span>
                <span className="font-mono text-[#FFF7ED]">
                  {customer.orderType === "TAKEOUT" ? "R$ 0,00" : formatCents(deliveryFeeCents)}
                </span>
              </div>
              <div className="flex justify-between text-sm font-bold pt-1">
                <span className="text-[#D6B896]">Total</span>
                <span className="font-mono text-[#FBBF24] text-lg">{formatCents(totalCents)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Payment */}
        {step === 3 && (
          <div className="space-y-4 py-4">
            <h2 className="text-[#D6B896] font-semibold">Pagamento</h2>

            <div className="space-y-2">
              {([
                ["CASH", "Dinheiro"],
                ["CARD_ON_DELIVERY", "Cartao na entrega"],
                ["PIX", "PIX"],
              ] as const).map(([method, label]) => (
                <button
                  key={method}
                  onClick={() => setPaymentMethod(method)}
                  className={cn(
                    "w-full flex items-center justify-between p-4 rounded border text-sm transition-colors",
                    paymentMethod === method
                      ? "bg-[#F97316]/10 border-[#F97316] text-[#FFF7ED]"
                      : "bg-[#1A1208] border-[#3D2B1A] text-[#D6B896] hover:border-[#7C5C3E]",
                  )}
                >
                  <span className="font-semibold">{label}</span>
                  {paymentMethod === method && (
                    <span className="w-3 h-3 rounded-full bg-[#F97316]" />
                  )}
                </button>
              ))}
            </div>

            {paymentMethod === "CASH" && (
              <div>
                <label className="text-[#7C5C3E] text-xs block mb-1">Troco para quanto? (R$)</label>
                <input
                  type="number"
                  value={changeFor}
                  onChange={(e) => setChangeFor(e.target.value)}
                  className="w-full bg-[#1A1208] border border-[#3D2B1A] rounded p-3 text-[#FFF7ED] text-sm focus:outline-none focus:border-[#F97316]"
                  placeholder="Ex: 50.00"
                  step="0.01"
                />
              </div>
            )}

            {paymentMethod === "PIX" && (
              <div className="bg-[#1A1208] border border-[#3D2B1A] rounded p-6 text-center">
                <div className="w-40 h-40 mx-auto bg-[#251A0E] border border-[#3D2B1A] rounded flex items-center justify-center mb-3">
                  <span className="text-[#7C5C3E] text-xs font-mono">QR Code PIX</span>
                </div>
                <p className="text-[#7C5C3E] text-xs">
                  O QR Code sera gerado apos confirmar o pedido.
                </p>
              </div>
            )}

            <div className="border-t border-[#3D2B1A] pt-3">
              <div className="flex justify-between font-bold">
                <span className="text-[#D6B896]">Total a pagar</span>
                <span className="font-mono text-[#FBBF24] text-lg">{formatCents(totalCents)}</span>
              </div>
            </div>

            {error && (
              <div className="bg-red-900/30 border border-red-800 rounded p-3">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom action bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-[#1A1208] border-t border-[#3D2B1A] p-4">
        <div className="max-w-lg mx-auto">
          {step < 3 ? (
            <button
              onClick={() => {
                if (step === 1) {
                  const err = validateStep1();
                  if (err) { setError(err); return; }
                  setError("");
                }
                setStep(step + 1);
              }}
              className="w-full bg-[#F97316] text-black font-bold py-3 rounded text-sm flex items-center justify-center gap-2"
            >
              Continuar <ArrowRight size={16} />
            </button>
          ) : (
            <button
              onClick={handleConfirmOrder}
              disabled={loading}
              className="w-full bg-[#F97316] text-black font-bold py-3 rounded text-sm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Enviando...
                </>
              ) : (
                "Confirmar Pedido"
              )}
            </button>
          )}
          {error && step === 1 && (
            <p className="text-red-400 text-xs text-center mt-2">{error}</p>
          )}
        </div>
      </div>
    </div>
  );
}
