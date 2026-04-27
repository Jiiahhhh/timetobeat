import { Game } from "../types";

interface Props {
  game: Game;
  platformLabel: string;
  isAlternative: boolean;
  onClose: () => void;
  onOpenStore: (game: Game) => void;
  onPromoteAlternative: (game: Game) => void;
}

export default function GameModal({
  game,
  platformLabel,
  isAlternative,
  onClose,
  onOpenStore,
  onPromoteAlternative,
}: Props) {
  return (
    <div
      onClick={onClose}
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 md:p-5 backdrop-blur-sm"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-[#1b2838] border border-[#3d6a8a] rounded-md w-full max-w-[680px] max-h-[90vh] md:max-h-[85vh] overflow-y-auto shadow-2xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 md:px-6 py-3 md:py-4 border-b border-[#2a475e] sticky top-0 bg-[#1b2838] z-10">
          <h3 className="text-lg md:text-xl font-bold text-[#c6d4df] truncate pr-4">
            {game.title}
          </h3>

          <button
            onClick={onClose}
            className="bg-transparent border-none text-[#8f98a0] text-2xl cursor-pointer hover:text-white transition-colors"
          >
            ×
          </button>
        </div>

        <div className="p-4 md:p-6">
          {/* Cover + info - stacked vertically on mobile, side by side on desktop */}
          <div className="flex flex-col md:flex-row gap-4 md:gap-5 mb-6">
            {game.cover_portrait_url && (
              <img
                src={game.cover_portrait_url}
                alt={game.title}
                className="w-[100px] h-[135px] md:w-[100px] md:h-[135px] object-cover rounded-sm shrink-0 shadow-md mx-auto md:mx-0"
              />
            )}

            {/* Text centered on mobile, left aligned on desktop */}
            <div className="text-center md:text-left mt-2 md:mt-0">
              <div className="flex justify-center md:justify-start gap-1.5 flex-wrap mb-3">
                {game.genres.map((g) => (
                  <span
                    key={g}
                    className="text-[10px] md:text-[11px] text-[#8f98a0] bg-[#2a475e] border border-[#3d6a8a] rounded-sm px-2 py-0.5"
                  >
                    {g}
                  </span>
                ))}

                {game.difficulty_label && (
                  <span className="text-[10px] md:text-[11px] text-[#a4d007] bg-[#2a3d1a] border border-[#4c6b22] rounded-sm px-2 py-0.5">
                    {game.difficulty_label}
                  </span>
                )}
              </div>

              {game.rating > 0 && (
                <div className="text-xs md:text-[13px] text-[#8f98a0] mb-1.5">
                  ⭐ {game.rating}/100
                </div>
              )}

              <div className="text-xs md:text-[13px] text-[#a4d007] font-semibold mb-3">
                🕒 Main Story: ~{game.main_story}h
              </div>

              {game.short_description && (
                <p className="text-xs md:text-[13px] text-[#c6d4df] leading-relaxed opacity-90 text-left">
                  {game.short_description}
                </p>
              )}
            </div>
          </div>

          {/* Trailer section */}
          <div className="mb-5">
            <p className="text-[10px] md:text-[11px] text-[#8f98a0] uppercase tracking-wider mb-2 font-semibold">
              Trailer
            </p>

            {game.trailer_youtube_id && game.trailer_valid !== false ? (
              <div className="relative pb-[56.25%] h-0 rounded-sm overflow-hidden bg-black shadow-inner">
                <iframe
                  src={`https://www.youtube.com/embed/${game.trailer_youtube_id}`}
                  className="absolute top-0 left-0 w-full h-full border-none"
                  allowFullScreen
                />
              </div>
            ) : (
              <div className="flex items-center justify-center bg-[#2a475e] border border-[#3d6a8a] rounded-sm h-[140px] md:h-[180px]">
                <div className="text-center">
                  <p className="text-[#8f98a0] text-xs md:text-sm mb-2">
                    🎬 Trailer not available
                  </p>

                  <a
                    href={
                      game.steam_app_id
                        ? `https://store.steampowered.com/app/${game.steam_app_id}`
                        : `https://store.steampowered.com/search/?term=${encodeURIComponent(game.title)}`
                    }
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] md:text-[11px] text-[#66c0f4] hover:text-[#a4d007] transition-colors"
                  >
                    Watch on Steam store page →
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* Action buttons - stacked vertically on mobile, inline on desktop */}
          <div className="flex flex-col sm:flex-row gap-2.5 md:gap-3">
            <button
              onClick={() => onOpenStore(game)}
              className="flex-1 py-2.5 md:py-3 bg-[#4c6b22] text-[#a4d007] text-xs md:text-[13px] font-bold border-none rounded-sm cursor-pointer hover:bg-[#5a7d28] transition-colors shadow-sm"
            >
              Find on Steam →
            </button>

            {isAlternative && (
              <button
                onClick={() => onPromoteAlternative(game)}
                className="flex-1 py-2.5 md:py-3 bg-transparent border border-[#a4d007] text-[#a4d007] text-xs md:text-[13px] font-bold rounded-sm cursor-pointer hover:bg-[#2a3d1a] transition-colors"
              >
                Make this my pick →
              </button>
            )}

            <button
              onClick={onClose}
              className="py-2.5 md:py-3 px-4 md:px-6 bg-transparent border border-[#3d6a8a] text-[#8f98a0] text-xs font-semibold rounded-sm cursor-pointer hover:bg-[#2a475e] transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
