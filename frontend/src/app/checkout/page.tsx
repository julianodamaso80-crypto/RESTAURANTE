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
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4">
        <p className="text-muted">Carrinho vazio</p>
        <button
          onClick={() => router.back()}
          className="text-primary text-sm underline"
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
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="px-4 py-5 border-b border-border flex items-center gap-3">
        <button onClick={() => (step > 1 ? setStep(step - 1) : router.back())} className="text-muted hover:text-foreground">
          <ArrowLeft size={20} />
        </button>
        <h1 className="font-semibold text-lg">Checkout</h1>
        <span className="ml-auto text-muted text-xs tabular-nums">
          Etapa {step} de 3
        </span>
      </div>

      {/* Step indicators */}
      <div className="flex gap-1.5 px-4 py-3">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={cn(
              "flex-1 h-1 rounded-full",
              s <= step ? "bg-primary" : "bg-surface",
            )}
          />
        ))}
      </div>

      <div className="max-w-lg mx-auto px-4 pb-32">
        {/* Step 1: Identification */}
        {step === 1 && (
          <div className="space-y-5 py-5">
            <h2 className="text-foreground-secondary font-semibold">Identificacao</h2>

            <div>
              <label className="text-muted text-xs block mb-1.5">Nome completo *</label>
              <input
                type="text"
                value={customer.name}
                onChange={(e) => setCustomer({ ...customer, name: e.target.value })}
                className="w-full h-11 px-3.5 bg-background-secondary border border-border rounded-lg text-sm text-foreground placeholder:text-muted transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                placeholder="Seu nome"
              />
            </div>

            <div>
              <label className="text-muted text-xs block mb-1.5">Telefone / WhatsApp *</label>
              <input
                type="tel"
                value={customer.phone}
                onChange={(e) => setCustomer({ ...customer, phone: e.target.value })}
                className="w-full h-11 px-3.5 bg-background-secondary border border-border rounded-lg text-sm text-foreground placeholder:text-muted transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                placeholder="(11) 99999-9999"
              />
            </div>

            <div>
              <label className="text-muted text-xs block mb-1.5">E-mail (opcional)</label>
              <input
                type="email"
                value={customer.email}
                onChange={(e) => setCustomer({ ...customer, email: e.target.value })}
                className="w-full h-11 px-3.5 bg-background-secondary border border-border rounded-lg text-sm text-foreground placeholder:text-muted transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                placeholder="voce@email.com"
              />
            </div>

            <div>
              <label className="text-muted text-xs block mb-2">Tipo de entrega</label>
              <div className="flex gap-2">
                {([["TAKEOUT", "Retirada no local"], ["DELIVERY", "Delivery"]] as const).map(([type, label]) => (
                  <button
                    key={type}
                    onClick={() => setCustomer({ ...customer, orderType: type })}
                    className={cn(
                      "flex-1 py-3 rounded-lg border text-sm font-semibold transition-colors",
                      customer.orderType === type
                        ? "bg-primary/10 border-primary text-primary"
                        : "bg-background-secondary border-border text-muted hover:border-border-light",
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {customer.orderType === "DELIVERY" && (
              <div className="space-y-3 border border-border rounded-lg p-4">
                <h3 className="text-foreground-secondary text-xs font-semibold">Endereco de entrega</h3>
                <input
                  type="text"
                  value={customer.address.street}
                  onChange={(e) => setCustomer({ ...customer, address: { ...customer.address, street: e.target.value } })}
                  className="w-full h-10 px-3 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  placeholder="Rua"
                />
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customer.address.number}
                    onChange={(e) => setCustomer({ ...customer, address: { ...customer.address, number: e.target.value } })}
                    className="w-24 h-10 px-3 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    placeholder="N"
                  />
                  <input
                    type="text"
                    value={customer.address.complement}
                    onChange={(e) => setCustomer({ ...customer, address: { ...customer.address, complement: e.target.value } })}
                    className="flex-1 h-10 px-3 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                    placeholder="Complemento"
                  />
                </div>
                <input
                  type="text"
                  value={customer.address.neighborhood}
                  onChange={(e) => setCustomer({ ...customer, address: { ...customer.address, neighborhood: e.target.value } })}
                  className="w-full h-10 px-3 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  placeholder="Bairro"
                />
                <input
                  type="text"
                  value={customer.address.zipcode}
                  onChange={(e) => setCustomer({ ...customer, address: { ...customer.address, zipcode: e.target.value } })}
                  className="w-full h-10 px-3 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  placeholder="CEP"
                />
              </div>
            )}
          </div>
        )}

        {/* Step 2: Order Summary */}
        {step === 2 && (
          <div className="space-y-5 py-5">
            <h2 className="text-foreground-secondary font-semibold">Resumo do pedido</h2>

            <div className="space-y-2">
              {items.map((item) => (
                <div key={item.id} className="bg-background-secondary border border-border rounded-lg p-3.5">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-foreground text-sm font-semibold">
                        {item.quantity}x {item.product.name}
                      </span>
                      {item.selectedModifiers.length > 0 && (
                        <p className="text-muted text-xs mt-0.5">
                          {item.selectedModifiers.map((m) => m.name).join(", ")}
                        </p>
                      )}
                    </div>
                    <span className="tabular-nums text-primary text-sm font-semibold">
                      {formatCents(item.totalPriceCents)}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div>
              <label className="text-muted text-xs block mb-1.5">Observacao geral</label>
              <textarea
                value={orderNotes}
                onChange={(e) => setOrderNotes(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-background-secondary border border-border rounded-lg text-sm text-foreground placeholder:text-muted resize-none transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                rows={2}
                placeholder="Alguma observacao para o restaurante?"
              />
            </div>

            <div>
              <label className="text-muted text-xs block mb-1.5">Cupom de desconto</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={coupon}
                  onChange={(e) => { setCoupon(e.target.value); setCouponMsg(""); }}
                  className="flex-1 h-11 px-3.5 bg-background-secondary border border-border rounded-lg text-sm text-foreground placeholder:text-muted transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  placeholder="CODIGO"
                />
                <button
                  onClick={handleApplyCoupon}
                  className="px-4 py-2 bg-surface/50 border border-border rounded-lg text-foreground-secondary text-sm hover:border-primary transition-colors"
                >
                  Aplicar
                </button>
              </div>
              {couponMsg && <p className="text-red-400 text-xs mt-1">{couponMsg}</p>}
            </div>

            <div className="border-t border-border pt-4 space-y-1.5">
              <div className="flex justify-between text-sm">
                <span className="text-muted">Subtotal</span>
                <span className="tabular-nums text-foreground">{formatCents(subtotalCents)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted">Taxa de entrega</span>
                <span className="tabular-nums text-foreground">
                  {customer.orderType === "TAKEOUT" ? "R$ 0,00" : formatCents(deliveryFeeCents)}
                </span>
              </div>
              <div className="flex justify-between text-sm font-semibold pt-1">
                <span className="text-foreground-secondary">Total</span>
                <span className="tabular-nums text-primary text-lg">{formatCents(totalCents)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Payment */}
        {step === 3 && (
          <div className="space-y-5 py-5">
            <h2 className="text-foreground-secondary font-semibold">Pagamento</h2>

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
                    "w-full flex items-center justify-between p-4 rounded-lg border text-sm transition-colors",
                    paymentMethod === method
                      ? "bg-primary/10 border-primary text-foreground"
                      : "bg-background-secondary border-border text-foreground-secondary hover:border-border-light",
                  )}
                >
                  <span className="font-semibold">{label}</span>
                  {paymentMethod === method && (
                    <span className="w-3 h-3 rounded-full bg-primary" />
                  )}
                </button>
              ))}
            </div>

            {paymentMethod === "CASH" && (
              <div>
                <label className="text-muted text-xs block mb-1.5">Troco para quanto? (R$)</label>
                <input
                  type="number"
                  value={changeFor}
                  onChange={(e) => setChangeFor(e.target.value)}
                  className="w-full h-11 px-3.5 bg-background-secondary border border-border rounded-lg text-sm text-foreground placeholder:text-muted transition-all duration-200 hover:border-border-light focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                  placeholder="Ex: 50.00"
                  step="0.01"
                />
              </div>
            )}

            {paymentMethod === "PIX" && (
              <div className="bg-background-secondary border border-border rounded-lg p-6 text-center">
                <div className="w-40 h-40 mx-auto bg-surface/50 border border-border rounded-lg flex items-center justify-center mb-3">
                  <span className="text-muted text-xs">QR Code PIX</span>
                </div>
                <p className="text-muted text-xs">
                  O QR Code sera gerado apos confirmar o pedido.
                </p>
              </div>
            )}

            <div className="border-t border-border pt-4">
              <div className="flex justify-between font-semibold">
                <span className="text-foreground-secondary">Total a pagar</span>
                <span className="tabular-nums text-primary text-lg">{formatCents(totalCents)}</span>
              </div>
            </div>

            {error && (
              <div className="bg-red-900/30 border border-red-800 rounded-lg p-3">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom action bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-background-secondary border-t border-border p-4">
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
              className="w-full bg-primary text-white font-medium py-3 rounded-lg text-sm flex items-center justify-center gap-2 hover:bg-primary-600 transition-all duration-200 shadow-elevation-1"
            >
              Continuar <ArrowRight size={16} />
            </button>
          ) : (
            <button
              onClick={handleConfirmOrder}
              disabled={loading}
              className="w-full bg-primary text-white font-medium py-3 rounded-lg text-sm flex items-center justify-center gap-2 hover:bg-primary-600 transition-all duration-200 shadow-elevation-1 disabled:opacity-50"
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
