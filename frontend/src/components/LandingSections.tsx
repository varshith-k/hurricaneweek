function StepIcon({ path }: { path: string }) {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={path} />
    </svg>
  );
}

const steps = [
  { title: "1. Start", body: "Get $400 and your student profile.", icon: "M12 2v20M2 12h20" },
  { title: "2. Make decisions", body: "Respond to real-world scenarios each day.", icon: "M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" },
  { title: "3. Face the consequences", body: "See how your choices affect safety, finances, and insurance.", icon: "M3 3v18h18M18 17V9M13 17V5M8 17v-3" },
  { title: "4. Get your report", body: "Learn what you did well and what to improve.", icon: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M9 13h6M9 17h6" },
];

const tradeoffs = [
  "Manage a limited budget",
  "Protect your transportation",
  "Keep your belongings safe",
  "Learn about insurance coverage",
  "Experience a changing storm",
];

export function LandingSections({ onStart }: { onStart: () => void }) {
  return (
    <>
      <section id="challenge" className="border-t border-border py-16 md:py-24">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 md:grid-cols-2 md:items-center">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-muted">The challenge</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-text md:text-4xl">Five days. Limited money. Real consequences.</h2>
            <p className="mt-4 max-w-lg text-muted">
              You have $400, a scooter, an apartment, classes, and work. A hurricane is approaching South Florida. Every choice you make affects your safety, finances, and future.
            </p>
          </div>
          <div className="rounded-3xl border border-border bg-surface p-5 shadow-lg shadow-black/30">
            <p className="text-xs uppercase tracking-[0.25em] text-warning">Flood warning issued</p>
            <p className="mt-2 text-lg text-text">Flooding could damage uncovered transport and valuables.</p>
            <div className="mt-4 flex flex-col gap-2">
              <div className="flex items-center justify-between rounded-xl bg-accent px-4 py-3 text-sm font-medium text-background">
                <span>Move scooter to safe storage and secure documents</span>
                <span>-$45</span>
              </div>
              <div className="flex items-center justify-between rounded-xl border border-border px-4 py-3 text-sm text-text">
                <span>Secure documents only</span>
                <span>-$15</span>
              </div>
              <div className="flex items-center justify-between rounded-xl border border-border px-4 py-3 text-sm text-text">
                <span>Do nothing</span>
                <span>$0</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="how-it-works" className="border-t border-border py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4">
          <p className="text-xs uppercase tracking-[0.3em] text-muted">How it works</p>
          <h2 className="mt-3 max-w-xl text-3xl font-semibold tracking-tight text-text md:text-4xl">A realistic simulation, not just a quiz.</h2>
          <p className="mt-4 max-w-xl text-muted">Experience a dynamic story that evolves with the storm. Your decisions change your risk, your finances, and how well you weather the week.</p>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 md:grid-cols-4">
            {steps.map((step) => (
              <div key={step.title} className="rounded-2xl border border-border bg-surface p-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-full border border-accent/40 text-accent">
                  <StepIcon path={step.icon} />
                </div>
                <p className="mt-4 font-medium text-text">{step.title}</p>
                <p className="mt-1 text-sm text-muted">{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="border-t border-border py-16 md:py-24">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 md:grid-cols-2 md:items-center">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/images/flood-street-scene.jpg" alt="Flooded street in a South Florida city during a storm" className="w-full rounded-3xl border border-border object-cover" />
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-text md:text-4xl">Real scenarios. Real tradeoffs.</h2>
            <p className="mt-4 max-w-lg text-muted">
              From stocking supplies to protecting your laptop, from evacuation decisions to insurance coverage — every choice matters.
            </p>
            <ul className="mt-6 space-y-3">
              {tradeoffs.map((item) => (
                <li key={item} className="flex items-center gap-3 text-sm text-text">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="border-t border-border py-16 md:py-24">
        <div className="mx-auto flex max-w-6xl flex-col items-start gap-4 px-4">
          <h2 className="text-2xl font-semibold text-text md:text-3xl">Make better decisions before the next storm.</h2>
          <button type="button" onClick={onStart} className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 font-medium text-background transition hover:opacity-90">
            Start the $400 Challenge
            <span aria-hidden="true">→</span>
          </button>
        </div>
      </section>
    </>
  );
}
