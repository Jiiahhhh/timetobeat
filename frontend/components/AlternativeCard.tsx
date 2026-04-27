import { Game } from "../types";

interface Props {
  game: Game;
  onClick: (game: Game) => void;
}

export default function AlternativeCard({ game, onClick }: Props) {
  return (
    <div
      onClick={() => onClick(game)}
      className="flex gap-3 bg-[#2a475e] border border-[#3d6a8a] rounded-sm p-3.5 cursor-pointer hover:border-[#a4d007] transition-colors group"
    >
      <div className="w-12 h-16 shrink-0 bg-[#1b2838] rounded-sm shadow-sm flex items-center justify-center text-lg overflow-hidden">
        {game.cover_portrait_url || game.cover_url ? (
          <img
            src={game.cover_portrait_url || game.cover_url || ""}
            alt={game.title}
            className="w-full h-full object-cover rounded-sm"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              const fallback = game.cover_url;
              if (fallback && target.src !== fallback) {
                target.src = fallback;
              } else {
                target.replaceWith(
                  Object.assign(document.createElement("span"), {
                    textContent: "🎮",
                  }),
                );
              }
            }}
          />
        ) : (
          <span>🎮</span>
        )}
      </div>
      <div className="flex-1">
        <div className="text-sm font-semibold text-[#c6d4df] mb-1 group-hover:text-white transition-colors">
          {game.title}
        </div>
        <div className="text-[11px] text-[#8f98a0] mb-1.5">{game.framing}</div>
        <div className="text-xs text-[#a4d007] font-semibold">
          ~{game.main_story}h
        </div>
      </div>
    </div>
  );
}
