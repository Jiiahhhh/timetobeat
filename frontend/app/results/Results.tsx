"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Game, Recommendation } from "../../types";
import { DIFFICULTY_OPTIONS } from "../../lib/constants";
import AlternativeCard from "../../components/AlternativeCard";
import GameModal from "../../components/GameModal";

export default function Results() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [data, setData] = useState<Recommendation | null>(null);
  const [modalGame, setModalGame] = useState<Game | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showShorterSlider, setShowShorterSlider] = useState(false);
  const [shorterHours, setShorterHours] = useState(1);
  const [showIntensePanel, setShowIntensePanel] = useState(false);
  const [selectedDifficulty, setSelectedDifficulty] = useState<number | null>(
    null,
  );

  const initTime = parseInt(searchParams.get("time") || "60");
  const initVibe = searchParams.get("vibe") || "surprise";
  const initPlatform = searchParams.get("platform") || "any";

  const fetchRecommend = async (opts: {
    modifier?: string;
    overrideMinutes?: number;
    maxDifficulty?: number;
    exclude?: string[];
  }) => {
    setLoading(true);
    setError("");
    try {
      const timeToSend =
        opts.overrideMinutes ??
        (data?.meta?.time_available_minutes || initTime);
      const excludeList =
        opts.exclude ??
        (data
          ? [data.primary.title, ...data.alternatives.map((g) => g.title)]
          : []);
      const vibeToSend = data?.meta?.vibe || initVibe;
      const platformToSend = data?.meta?.platform || initPlatform;

      const res = await fetch(
        "https://timetobeat-production.up.railway.app/api/recommend",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            time_available: timeToSend,
            vibe: vibeToSend,
            platform: platformToSend,
            modifier: opts.modifier || null,
            max_difficulty: opts.maxDifficulty || null,
            exclude_titles: excludeList,
          }),
        },
      );

      if (!res.ok) throw new Error("Failed to retrieve data from server");
      const newData = await res.json();

      newData.meta.time_available_minutes = timeToSend;
      setData(newData);
      setShowShorterSlider(false);
      setShowIntensePanel(false);
      setSelectedDifficulty(null);
    } catch (err) {
      console.error(err);
      setError("Oops, the server failed to respond.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommend({ overrideMinutes: initTime, exclude: [] });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (data)
      setShorterHours(
        Math.round((data.meta.time_available_minutes / 60) * 10) / 10,
      );
  }, [data]);

  if (loading && !data)
    return (
      <main className="min-h-screen bg-[#1b2838] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <svg
            className="animate-spin h-8 w-8 text-[#a4d007]"
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
          <p className="text-[#8f98a0]">Analyzing library...</p>
        </div>
      </main>
    );

  if (error)
    return (
      <main className="min-h-screen bg-[#1b2838] flex flex-col items-center justify-center gap-4">
        <p className="text-red-400">{error}</p>
        <button
          onClick={() => router.push("/")}
          className="px-4 py-2 border border-[#3d6a8a] text-[#8f98a0] rounded-sm hover:text-[#c6d4df]"
        >
          Back
        </button>
      </main>
    );

  if (!data || !data.primary) return null;

  const timeHours =
    data.meta.time_available_minutes > 0
      ? data.meta.time_available_minutes / 60
      : 1;
  const daysToFinish = Math.ceil(data.primary.main_story / timeHours);
  const finishDate = new Date();
  finishDate.setDate(finishDate.getDate() + daysToFinish);
  const finishLabel = finishDate.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
  const platformLabel =
    data.meta.platform === "any"
      ? "Steam"
      : data.meta.platform.charAt(0).toUpperCase() +
        data.meta.platform.slice(1);

  const openStore = (game: Game) =>
    window.open(
      game.steam_url ||
        `https://store.steampowered.com/search/?term=${encodeURIComponent(game.title)}`,
      "_blank",
    );

  const promoteAlternative = (game: Game) => {
    const newAlts = [
      data.primary,
      ...data.alternatives.filter((g) => g.title !== game.title),
    ];
    setData({ ...data, primary: game, alternatives: newAlts.slice(0, 2) });
    setModalGame(null);
  };

  return (
    <main className="min-h-screen bg-[#1b2838]">
      {/* Navbar */}
      <div className="bg-[#171a21] border-b border-[#2a475e] px-8 py-3 flex items-center justify-between">
        <h1 className="text-lg font-bold text-[#c6d4df] tracking-wide">
          TimeToBeat
        </h1>
        <button
          onClick={() => router.push("/")}
          className="bg-transparent border border-[#3d6a8a] text-[#8f98a0] text-xs cursor-pointer px-3 py-1.5 rounded-sm hover:text-[#c6d4df] transition-colors"
        >
          ← New search
        </button>
      </div>

      <div className="max-w-5xl mx-auto px-8 py-8">
        {/* Primary card */}
        <div className="grid grid-cols-[auto_1fr_auto] gap-7 bg-[#2a475e] border border-[#a4d007] rounded-sm p-7 mb-6 items-start relative">
          {loading && (
            <div className="absolute inset-0 bg-[#2a475e]/80 flex items-center justify-center z-10 rounded-sm">
              <svg
                className="animate-spin h-6 w-6 text-[#a4d007]"
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
            </div>
          )}

          {data.primary.cover_url ? (
            <img
              src={data.primary.cover_url}
              alt={data.primary.title}
              className="w-[120px] h-[160px] object-cover rounded-sm shadow-md"
            />
          ) : (
            <div className="w-[120px] h-[160px] bg-[#1b2838] rounded-sm flex items-center justify-center text-3xl shadow-md">
              🎮
            </div>
          )}

          {/* Info */}
          <div>
            <div className="inline-block text-[10px] bg-[#4c6b22] text-[#a4d007] px-2 py-0.5 rounded-sm font-bold mb-2.5 tracking-wider">
              TOP PICK
            </div>
            <h2
              onClick={() => setModalGame(data.primary)}
              className="text-3xl font-bold text-[#c6d4df] mb-2.5 cursor-pointer leading-tight hover:text-[#a4d007] transition-colors"
            >
              {data.primary.title}
            </h2>
            <div className="flex gap-1.5 flex-wrap mb-2">
              {data.primary.genres.map((g) => (
                <span
                  key={g}
                  className="text-[11px] text-[#8f98a0] bg-[#1b2838] border border-[#3d6a8a] rounded-sm px-2 py-0.5"
                >
                  {g}
                </span>
              ))}
              {data.primary.difficulty_label && (
                <span className="text-[11px] text-[#8f98a0] bg-[#1b2838] border border-[#3d6a8a] rounded-sm px-2 py-0.5">
                  {data.primary.difficulty_label}
                </span>
              )}
            </div>
            <div className="flex gap-5 text-[13px] text-[#8f98a0] mb-3.5">
              <span>⭐ {data.primary.rating}/100</span>
              <span>🕒 ~{data.primary.main_story}h main story</span>
            </div>
            <div className="bg-[#1b2838] border border-[#2a475e] rounded-sm px-3.5 py-3 max-w-[420px]">
              <div className="text-[13px] text-[#a4d007] font-semibold mb-1">
                At {Math.round(timeHours * 10) / 10}h/day → finish around{" "}
                <span className="text-[#c6d4df]">{finishLabel}</span> (
                {daysToFinish} days)
              </div>
              <div className="text-[11px] text-[#4c6b22] italic">
                Games aren&apos;t deadlines — enjoy every hour of it.
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2 min-w-[200px]">
            <button
              onClick={() => openStore(data.primary)}
              className="py-2.5 px-4 bg-[#4c6b22] text-[#a4d007] text-[13px] font-bold border-none rounded-sm cursor-pointer hover:bg-[#5a7d28] transition-colors"
            >
              Find on {platformLabel} →
            </button>
            <button
              onClick={() => setModalGame(data.primary)}
              className="py-2 px-4 bg-transparent border border-[#3d6a8a] text-[#c6d4df] text-xs rounded-sm cursor-pointer hover:bg-[#1b2838] transition-colors"
            >
              View details
            </button>
            <button
              onClick={() => fetchRecommend({})}
              disabled={loading}
              className="py-2 px-4 bg-transparent border border-[#3d6a8a] text-[#8f98a0] text-xs rounded-sm cursor-pointer hover:bg-[#1b2838] disabled:opacity-60 transition-colors"
            >
              Not this one
            </button>

            {/* Fine tune row */}
            <div className="flex gap-1 mt-1">
              <button
                onClick={() => {
                  setShowShorterSlider(!showShorterSlider);
                  setShowIntensePanel(false);
                }}
                className={`flex-1 py-1.5 px-1 text-[10px] rounded-sm cursor-pointer border transition-colors ${showShorterSlider ? "bg-[#2a3d1a] border-[#a4d007] text-[#a4d007]" : "bg-[#1b2838] border-[#3d6a8a] text-[#8f98a0] hover:text-[#c6d4df]"}`}
              >
                ⏱ Shorter
              </button>
              <button
                onClick={() => {
                  setShowIntensePanel(!showIntensePanel);
                  setShowShorterSlider(false);
                }}
                className={`flex-1 py-1.5 px-1 text-[10px] rounded-sm cursor-pointer border transition-colors ${showIntensePanel ? "bg-[#2a3d1a] border-[#a4d007] text-[#a4d007]" : "bg-[#1b2838] border-[#3d6a8a] text-[#8f98a0] hover:text-[#c6d4df]"}`}
              >
                🎯 Intensity
              </button>
              <button
                onClick={() => fetchRecommend({ modifier: "coop" })}
                disabled={loading}
                className="flex-1 py-1.5 px-1 text-[10px] rounded-sm cursor-pointer border bg-[#1b2838] border-[#3d6a8a] text-[#8f98a0] hover:text-[#c6d4df] transition-colors"
              >
                👥 Co-op
              </button>
            </div>

            {/* Shorter panel */}
            {showShorterSlider && (
              <div className="bg-[#1b2838] border border-[#3d6a8a] rounded-sm p-3 mt-1 shadow-inner">
                <div className="flex justify-between mb-2">
                  <span className="text-[11px] text-[#8f98a0]">
                    Hours per day
                  </span>
                  <span className="text-[13px] font-bold text-[#a4d007]">
                    {shorterHours}h
                  </span>
                </div>
                <input
                  type="range"
                  min={0.5}
                  max={8}
                  step={0.5}
                  value={shorterHours}
                  onChange={(e) => setShorterHours(parseFloat(e.target.value))}
                  className="w-full accent-[#a4d007] mb-1.5 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-[#8f98a0] mb-2.5">
                  <span>30m</span>
                  <span>2h</span>
                  <span>4h</span>
                  <span>6h</span>
                  <span>8h</span>
                </div>
                <button
                  onClick={() =>
                    fetchRecommend({
                      overrideMinutes: Math.round(shorterHours * 60),
                    })
                  }
                  disabled={loading}
                  className="w-full py-2 bg-[#4c6b22] text-[#a4d007] text-xs font-bold border-none rounded-sm cursor-pointer hover:bg-[#5a7d28] transition-colors"
                >
                  Update Time →
                </button>
              </div>
            )}

            {/* Intensity panel */}
            {showIntensePanel && (
              <div className="bg-[#1b2838] border border-[#3d6a8a] rounded-sm p-3 mt-1 shadow-inner">
                <div className="mb-2.5 p-2 bg-[#2a475e] rounded-sm border border-[#3d6a8a]">
                  <span className="text-[10px] text-[#8f98a0] block mb-1">
                    This game is:
                  </span>
                  <span className="text-[13px] text-[#c6d4df] font-semibold">
                    {data.primary.difficulty_label || "⚔️ Fair fight"}
                  </span>
                </div>
                <p className="text-[11px] text-[#8f98a0] mb-2">
                  I want something:
                </p>

                {DIFFICULTY_OPTIONS.map((opt) => {
                  const isAvailable =
                    data.meta.available_difficulties?.includes(opt.val) ?? true;
                  return (
                    <label
                      key={opt.val}
                      className={`flex items-center gap-2 p-1.5 rounded-sm transition-colors ${!isAvailable ? "opacity-40 cursor-not-allowed" : selectedDifficulty === opt.val ? "bg-[#2a3d1a] cursor-pointer" : "bg-transparent cursor-pointer hover:bg-[#2a475e]"}`}
                    >
                      <input
                        type="radio"
                        name="difficulty"
                        value={opt.val}
                        checked={selectedDifficulty === opt.val}
                        onChange={() => setSelectedDifficulty(opt.val)}
                        disabled={!isAvailable}
                        className="accent-[#a4d007] cursor-inherit"
                      />
                      <span
                        className={`text-xs ${!isAvailable ? "text-[#8f98a0]" : selectedDifficulty === opt.val ? "text-[#a4d007]" : "text-[#c6d4df]"}`}
                      >
                        {opt.label}{" "}
                        {!isAvailable && (
                          <span className="italic ml-1 text-[10px]">(N/A)</span>
                        )}
                      </span>
                    </label>
                  );
                })}

                <button
                  onClick={() =>
                    selectedDifficulty &&
                    fetchRecommend({
                      modifier: "intensity",
                      maxDifficulty: selectedDifficulty,
                    })
                  }
                  disabled={!selectedDifficulty || loading}
                  className={`w-full py-2 text-xs font-bold border-none rounded-sm mt-2 transition-colors ${selectedDifficulty ? "bg-[#4c6b22] text-[#a4d007] cursor-pointer hover:bg-[#5a7d28]" : "bg-[#2a475e] text-[#8f98a0] cursor-default opacity-60"}`}
                >
                  Find intensity →
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Alternatives */}
        <p className="text-[11px] text-[#8f98a0] uppercase tracking-wider mb-2.5 font-semibold">
          Alternatives
        </p>
        <div className="grid grid-cols-2 gap-3 mb-6">
          {data.alternatives.map((game) => (
            <AlternativeCard
              key={game.title}
              game={game}
              onClick={setModalGame}
            />
          ))}
        </div>

        <button
          onClick={() => router.push("/")}
          className="py-2.5 px-5 bg-transparent border border-[#2a475e] text-[#8f98a0] text-xs rounded-sm cursor-pointer hover:text-[#c6d4df] hover:border-[#3d6a8a] transition-colors"
        >
          ← Try with different settings
        </button>
      </div>

      {/* Modal Details Component */}
      {modalGame && (
        <GameModal
          game={modalGame}
          platformLabel={platformLabel}
          isAlternative={data.alternatives.some(
            (g) => g.title === modalGame.title,
          )}
          onClose={() => setModalGame(null)}
          onOpenStore={openStore}
          onPromoteAlternative={promoteAlternative}
        />
      )}
    </main>
  );
}
