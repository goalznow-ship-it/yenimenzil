"use client";

import * as React from "react";
import type { Property } from "@yenimenzil/types";
import { Calculator } from "lucide-react";
import { formatPrice } from "@/lib/format";

const MONTHLY_RATES: Record<string, number> = {
  "1 il": 0.13,
  "5 il": 0.115,
  "10 il": 0.105,
  "15 il": 0.10,
  "20 il": 0.095,
  "25 il": 0.09,
  "30 il": 0.085
};

export function MortgageCalculator({ property }: { property: Property }) {
  const [initial, setInitial] = React.useState<number>(0.2);
  const [months, setMonths] = React.useState(240);
  const [rate, setRate] = React.useState(0.10);

  const principal = property.price * (1 - initial);
  const monthlyRate = rate / 12;
  const monthly =
    monthlyRate === 0
      ? principal / months
      : (principal * monthlyRate * Math.pow(1 + monthlyRate, months)) /
        (Math.pow(1 + monthlyRate, months) - 1);
  const totalPayment = monthly * months;
  const totalInterest = totalPayment - principal;

  const initialSlider = (
    <input
      type="range"
      min={10}
      max={80}
      step={5}
      value={Math.round(initial * 100)}
      onChange={(e) => setInitial(Number(e.target.value) / 100)}
      aria-label="İlkin ödəniş faizi"
      className="w-full accent-brand"
    />
  );

  const monthsSlider = (
    <input
      type="range"
      min={12}
      max={360}
      step={12}
      value={months}
      onChange={(e) => setMonths(Number(e.target.value))}
      aria-label="Müddət (ay)"
      className="w-full accent-brand"
    />
  );

  const rateButtons = (
    <div className="flex flex-wrap gap-1.5">
      {Object.entries(MONTHLY_RATES).map(([label, value]) => (
        <button
          key={label}
          type="button"
          aria-pressed={Math.abs(rate - value) < 0.001}
          onClick={() => setRate(value)}
          className={
            "rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors " +
            (Math.abs(rate - value) < 0.001
              ? "border-brand bg-brand text-white"
              : "border-border bg-surface text-foreground/70 hover:border-foreground/25")
          }
        >
          {label} · {Math.round(value * 100)}%
        </button>
      ))}
    </div>
  );

  return (
    <div className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70">
      <div className="flex items-center gap-2">
        <Calculator className="h-4.5 w-4.5 text-brand" />
        <h2 className="text-[15px] font-semibold">İpoteka kalkulyatoru</h2>
      </div>

      <div className="mt-4 space-y-4">
        <div>
          <div className="mb-1.5 flex items-center justify-between text-[13px]">
            <span className="text-foreground/70">İlkin ödəniş</span>
            <span className="font-semibold tabular-nums">
              {formatPrice(property.price * initial)}
            </span>
          </div>
          {initialSlider}
          <p className="mt-1 text-[11.5px] text-muted-foreground">
            {Math.round(initial * 100)}% · {formatPrice(property.price * initial)} ₼
          </p>
        </div>

        <div>
          <div className="mb-1.5 flex items-center justify-between text-[13px]">
            <span className="text-foreground/70">Müddət</span>
            <span className="font-semibold tabular-nums">
              {months >= 12 ? `${months / 12} il` : `${months} ay`}
            </span>
          </div>
          {monthsSlider}
        </div>

        <div>
          <span className="mb-1.5 block text-[13px] text-foreground/70">Faiz dərəcəsi</span>
          {rateButtons}
        </div>

        <div className="rounded-xl bg-brand-soft/60 p-4">
          <p className="text-[13px] text-brand">Aylıq ödəniş</p>
          <p className="mt-1 text-[26px] font-semibold tabular-nums tracking-tight text-brand">
            {Number.isFinite(monthly) ? formatPrice(monthly) : "—"} ₼
          </p>
          <p className="mt-1 text-[12px] text-muted-foreground">
            Faizlər üzrə cəmi: {Number.isFinite(totalInterest) ? formatPrice(totalInterest) : "—"} ₼ ·
            Ümumi: {Number.isFinite(totalPayment) ? formatPrice(totalPayment) : "—"} ₼
          </p>
        </div>

        <p className="text-[11.5px] leading-relaxed text-muted-foreground">
          Bu hesablama təxminidir və bank tərəfindən təsdiqlənmiş dəqiq şərtləri
          əks etdirmir.
        </p>
      </div>
    </div>
  );
}
