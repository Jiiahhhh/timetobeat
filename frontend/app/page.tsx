"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  TIME_LABELS,
  TIME_CTX,
  MOODS,
  PLATFORMS,
  STEP_LABELS,
} from "../lib/constants";

export default function Home() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [time, setTime] = useState(60);
  const [selectedMoods, setSelectedMoods] = useState<string[]>([]);
  const [platform, setPlatform] = useState("any");
  const [loading, setLoading] = useState(false);

  const previewGames = () => {
    const all = new Set<string>();

    selectedMoods.forEach((m) =>
      MOODS.find((x) => x.id === m)?.games.forEach((g) => all.add(g)),
    );

    return [...all].slice(0, 5);
  };

  const toggleMood = (id: string) =>
    setSelectedMoods((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id],
    );

  const handleSubmit = () => {
    setLoading(true);
    const vibe = selectedMoods[0] || "surprise";
    router.push(`/results?time=${time}&vibe=${vibe}&platform=${platform}`);
  };

  return (
    <main className="min-h-screen bg-[#1b2838]">
      {/* Navbar - Responsive padding */}
      <nav className="bg-[#171a21] border-b border-[#2a475e] px-4 md:px-8 py-3 flex items-center justify-between">
        <h1 className="text-base md:text-lg font-bold text-[#c6d4df] tracking-wide">
          TimeToBeat
        </h1>

        <p className="text-[10px] md:text-xs text-[#8f98a0]">
          Stop staring at your library. Start playing.
        </p>
      </nav>

      {/* Main Container - Stack vertically on mobile, horizontal on desktop */}
      <div className="max-w-6xl mx-auto px-4 md:px-8 py-8 md:py-12 flex flex-col md:flex-row gap-8 md:gap-10 items-start">
        {/* Left Column: Form - 100% on mobile, 70% on desktop */}
        <div className="w-full md:w-[70%]">
          {/* Step indicator */}
          <div className="flex gap-2 md:gap-3 mb-8 md:mb-10">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex-1">
                <div
                  className={`h-[3px] rounded-sm mb-2 transition-all ${
                    s < step
                      ? "bg-[#4c6b22]"
                      : s === step
                        ? "bg-[#a4d007]"
                        : "bg-[#2a475e]"
                  }`}
                />

                <span
                  className={`text-[10px] md:text-xs font-medium ${
                    s === step ? "text-[#a4d007]" : "text-[#8f98a0]"
                  }`}
                >
                  {STEP_LABELS[s - 1]}
                </span>
              </div>
            ))}
          </div>

          {/* STEP 1 */}
          {step === 1 && (
            <div className="animate-in fade-in duration-300">
              <h2 className="text-xl md:text-2xl font-bold text-[#c6d4df] mb-2">
                On a typical day, how long can you game?
              </h2>

              <p className="text-xs md:text-sm text-[#8f98a0] mb-8">
                We&apos;ll estimate when you&apos;ll finish your next game.
              </p>

              <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between mb-4 gap-1">
                <span className="text-4xl md:text-5xl font-bold text-[#a4d007]">
                  {TIME_LABELS[time]}
                </span>

                <span className="text-xs md:text-sm text-[#8f98a0] italic">
                  {TIME_CTX[time]}
                </span>
              </div>

              <input
                type="range"
                min={15}
                max={480}
                step={15}
                value={time}
                onChange={(e) => setTime(parseInt(e.target.value))}
                className="w-full accent-[#a4d007] cursor-pointer mb-2"
              />

              <div className="relative text-[10px] md:text-xs text-[#8f98a0] mb-8 md:mb-10 h-4">
                {[
                  { label: "15m", value: 15 },
                  { label: "1h", value: 60 },
                  { label: "2h", value: 120 },
                  { label: "4h", value: 240 },
                  { label: "6h", value: 360 },
                  { label: "8h", value: 480 },
                ].map(({ label, value }, index, arr) => {
                  const percent = ((value - 15) / (480 - 15)) * 100;
                  const isFirst = index === 0;
                  const isLast = index === arr.length - 1;
                  return (
                    <span
                      key={value}
                      className="absolute"
                      style={{
                        left: isFirst ? "0%" : isLast ? "auto" : `${percent}%`,
                        right: isLast ? "0%" : "auto",
                        transform:
                          isFirst || isLast ? "none" : "translateX(-50%)",
                      }}
                    >
                      {label}
                    </span>
                  );
                })}
              </div>

              <button
                onClick={() => setStep(2)}
                className="w-full py-3 md:py-3.5 bg-[#4c6b22] text-[#a4d007] font-bold text-sm md:text-base rounded-sm hover:bg-[#5a7d28] transition-colors"
              >
                Next →
              </button>
            </div>
          )}

          {/* STEP 2 */}
          {step === 2 && (
            <div className="animate-in fade-in duration-300">
              <h2 className="text-xl md:text-2xl font-bold text-[#c6d4df] mb-2">
                What kind of experience?
              </h2>

              <p className="text-xs md:text-sm text-[#8f98a0] mb-6">
                Pick one or more — we&apos;ll find what fits.
              </p>

              {/* Grid: 2 columns on mobile, 3 columns on desktop */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 md:gap-3 mb-4">
                {MOODS.map((m) => (
                  <div
                    key={m.id}
                    onClick={() => toggleMood(m.id)}
                    className={`p-3 md:p-4 text-center cursor-pointer rounded border transition-all ${
                      m.wide ? "col-span-2 md:col-span-3" : ""
                    } ${
                      selectedMoods.includes(m.id)
                        ? "bg-[#2a3d1a] border-[#a4d007]"
                        : "bg-[#2a475e] border-[#3d6a8a] hover:border-[#c6d4df]"
                    }`}
                  >
                    <span className="text-xl md:text-2xl block mb-2">
                      {m.icon}
                    </span>

                    <span
                      className={`text-[10px] md:text-xs font-medium ${
                        selectedMoods.includes(m.id)
                          ? "text-[#a4d007]"
                          : "text-[#8f98a0]"
                      }`}
                    >
                      {m.label}
                    </span>
                  </div>
                ))}
              </div>

              <div className="border-t border-[#2a475e] pt-3 min-h-[52px] mb-6">
                <p className="text-[9px] md:text-[10px] text-[#8f98a0] uppercase tracking-widest mb-2">
                  Games like this
                </p>

                {previewGames().length === 0 ? (
                  <p className="text-xs md:text-sm text-[#8f98a0] italic">
                    Select a mood to see examples
                  </p>
                ) : (
                  <div className="flex gap-1.5 md:gap-2 flex-wrap">
                    {previewGames().map((g) => (
                      <div
                        key={g}
                        className="flex items-center gap-1 bg-[#2a475e] border border-[#3d6a8a] rounded-sm px-1.5 md:px-2 py-0.5 md:py-1"
                      >
                        <div className="w-1.5 h-1.5 rounded-full bg-[#a4d007] shrink-0" />

                        <span className="text-[10px] md:text-xs text-[#c6d4df]">
                          {g}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* VALIDATION: Disable Next button if nothing selected */}
              <button
                onClick={() => setStep(3)}
                disabled={selectedMoods.length === 0}
                className={`w-full py-3 md:py-3.5 font-bold text-sm md:text-base rounded-sm transition-colors mb-1 ${
                  selectedMoods.length === 0
                    ? "bg-[#2a475e] text-[#8f98a0] cursor-not-allowed opacity-60"
                    : "bg-[#4c6b22] text-[#a4d007] hover:bg-[#5a7d28] cursor-pointer"
                }`}
              >
                Next →
              </button>

              {selectedMoods.length === 0 && (
                <p className="text-center text-[10px] text-[#8f98a0] mb-3">
                  *Please select at least one vibe
                </p>
              )}

              <button
                onClick={() => setStep(1)}
                className="w-full py-2 text-[#8f98a0] text-xs md:text-sm bg-transparent border-none cursor-pointer hover:text-[#c6d4df]"
              >
                ← Back
              </button>
            </div>
          )}

          {/* STEP 3 */}
          {step === 3 && (
            <div className="animate-in fade-in duration-300">
              <h2 className="text-xl md:text-2xl font-bold text-[#c6d4df] mb-2">
                Which platform?
              </h2>

              <p className="text-xs md:text-sm text-[#8f98a0] mb-6">
                Any platform is selected by default.
              </p>

              <div
                onClick={() => setPlatform("any")}
                className={`flex items-center justify-between p-3 md:p-4 bg-[#2a475e] rounded-sm mb-3 cursor-pointer transition-all border ${
                  platform === "any" ? "border-[#a4d007]" : "border-[#3d6a8a]"
                }`}
              >
                <div>
                  <span className="inline-block text-[9px] md:text-[10px] bg-[#4c6b22] text-[#a4d007] px-1.5 py-0.5 rounded-sm font-bold mb-1">
                    default
                  </span>

                  <div
                    className={`text-sm md:text-base font-bold ${
                      platform === "any" ? "text-[#a4d007]" : "text-[#c6d4df]"
                    }`}
                  >
                    💻 Any OS / Device
                  </div>

                  <div className="text-[10px] md:text-xs text-[#8f98a0]">
                    Recommend from all platforms
                  </div>
                </div>

                {platform === "any" && (
                  <span className="text-lg md:text-xl text-[#a4d007]">✓</span>
                )}
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-8 md:mb-10">
                {PLATFORMS.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setPlatform(p.id)}
                    className={`py-2.5 md:py-3 text-xs md:text-sm font-semibold rounded-sm transition-all border cursor-pointer ${
                      platform === p.id
                        ? "bg-[#1a3a52] text-[#1a9fff] border-[#1a9fff]"
                        : "bg-[#2a475e] text-[#8f98a0] border-[#3d6a8a] hover:text-[#c6d4df]"
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>

              <button
                onClick={handleSubmit}
                disabled={loading}
                className="w-full py-3 md:py-3.5 bg-[#4c6b22] text-[#a4d007] font-bold text-sm md:text-base rounded-sm hover:bg-[#5a7d28] transition-colors mb-2 disabled:opacity-60 flex items-center justify-center"
              >
                {loading ? (
                  <svg
                    className="animate-spin h-5 w-5 text-[#a4d007]"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>

                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                ) : (
                  "Find my game tonight →"
                )}
              </button>

              <button
                onClick={() => setStep(2)}
                className="w-full py-2 text-[#8f98a0] text-xs md:text-sm bg-transparent border-none cursor-pointer hover:text-[#c6d4df]"
              >
                ← Back
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Info - Moves below on mobile, 30% on desktop */}
        <div className="w-full md:w-[30%] pt-2 md:pt-14 flex flex-col gap-4">
          <div className="bg-[#2a475e] border border-[#3d6a8a] rounded p-4 md:p-5">
            <p className="text-[9px] md:text-[10px] text-[#8f98a0] uppercase tracking-widest mb-3 md:mb-4">
              How it works
            </p>

            <div className="flex flex-col gap-3 md:gap-4">
              {[
                {
                  n: "01",
                  t: "Set your time",
                  d: "Tell us how long you can game each day on average.",
                },
                {
                  n: "02",
                  t: "Pick your vibe",
                  d: "Choose what kind of experience you're in the mood for.",
                },
                {
                  n: "03",
                  t: "Get your game",
                  d: "We'll recommend the best game that fits your schedule.",
                },
              ].map((item) => (
                <div key={item.n} className="flex gap-2.5 md:gap-3 items-start">
                  <span className="text-[10px] md:text-xs text-[#4c6b22] font-bold shrink-0 mt-0.5">
                    {item.n}
                  </span>

                  <div>
                    <p className="text-xs md:text-sm text-[#c6d4df] font-semibold mb-0.5">
                      {item.t}
                    </p>

                    <p className="text-[10px] md:text-xs text-[#8f98a0] leading-relaxed">
                      {item.d}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-[#2a475e] border border-[#3d6a8a] rounded p-4 md:p-5">
            <p className="text-[9px] md:text-[10px] text-[#8f98a0] uppercase tracking-widest mb-2 md:mb-3">
              Good to know
            </p>

            <p className="text-[10px] md:text-xs text-[#8f98a0] leading-relaxed italic">
              &ldquo;Games aren&apos;t deadlines. The finish date is just an
              estimate — play at your own pace and enjoy every hour of
              it.&rdquo;
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
