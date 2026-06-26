export function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="glass rounded-xl px-5 py-4">
      <div className="text-[11px] font-medium uppercase tracking-wider text-white/40">
        {label}
      </div>
      <div className="mt-1 text-2xl font-bold text-white">{value}</div>
    </div>
  );
}
