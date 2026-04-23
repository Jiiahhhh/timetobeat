export const TIME_LABELS: Record<number, string> = {
  15: "15 min",
  30: "30 min",
  45: "45 min",
  60: "1 hour",
  75: "1h 15m",
  90: "1h 30m",
  105: "1h 45m",
  120: "2 hours",
  135: "2h 15m",
  150: "2h 30m",
  165: "2h 45m",
  180: "3 hours",
  195: "3h 15m",
  210: "3h 30m",
  225: "3h 45m",
  240: "4 hours",
};

export const TIME_CTX: Record<number, string> = {
  15: "perfect for a micro session",
  30: "a quick wind-down",
  45: "short but satisfying",
  60: "a solid session",
  90: "enough for real progress",
  120: "a proper evening",
  150: "getting serious",
  180: "deep dive territory",
  210: "you're committed",
  240: "marathon mode",
};

export const MOODS = [
  {
    id: "relaxed",
    icon: "😌",
    label: "Relaxed",
    games: ["Stardew Valley", "Journey", "Firewatch"],
  },
  {
    id: "action",
    icon: "⚡",
    label: "Action",
    games: ["Hades", "Doom Eternal", "Devil May Cry 5"],
  },
  {
    id: "story",
    icon: "📖",
    label: "Story",
    games: ["The Witcher 3", "Disco Elysium", "Celeste"],
  },
  {
    id: "puzzle",
    icon: "🧩",
    label: "Puzzle",
    games: ["Portal 2", "Baba Is You", "The Witness"],
  },
  {
    id: "rpg",
    icon: "⚔️",
    label: "RPG",
    games: ["Elden Ring", "Baldur's Gate 3", "Hollow Knight"],
  },
  {
    id: "classic",
    icon: "👾",
    label: "Classic",
    games: ["Hollow Knight", "Celeste", "Dead Cells"],
  },
  {
    id: "surprise",
    icon: "🎲",
    label: "Surprise me — anything great",
    games: ["Outer Wilds", "Disco Elysium", "Undertale"],
    wide: true,
  },
];

export const PLATFORMS = [
  { id: "Windows", label: "🪟 Windows" },
  { id: "Mac", label: "🍎 Mac" },
  { id: "Linux", label: "🐧 Linux" },
  { id: "Steam Deck", label: "🕹️ Steam Deck" },
];

export const STEP_LABELS = ["How long?", "What vibe?", "Platform?"];

export const DIFFICULTY_OPTIONS = [
  { val: 1, label: "☁️ Basically a nap" },
  { val: 2, label: "🌿 Chill vibes only" },
  { val: 3, label: "⚔️ Fair fight" },
  { val: 4, label: "💀 Prepare to suffer" },
  { val: 5, label: "🔥 Pure masochism" },
];
