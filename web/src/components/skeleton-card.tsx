export function SkeletonCard() {
  return (
    <div className="glass shimmer h-[180px] rounded-xl2 p-5">
      <div className="mb-4 flex items-start justify-between">
        <div className="h-4 w-2/3 rounded bg-outline-variant/30" />
        <div className="h-5 w-16 rounded-full bg-outline-variant/30" />
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full rounded bg-outline-variant/20" />
        <div className="h-3 w-5/6 rounded bg-outline-variant/20" />
        <div className="h-3 w-4/6 rounded bg-outline-variant/20" />
      </div>
    </div>
  );
}
