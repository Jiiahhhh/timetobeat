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
      {game.cover_url ? (
        <img src={game.cover_url} alt={game.title} className="w-12 h-16 object-cover rounded-sm shrink-0 shadow-sm" />
      ) : (
        <div className="w-12 h-16 bg-[#1b2838] rounded-sm shrink-0 flex items-center justify-center text-lg shadow-sm">🎮</div>
      )}
      <div className="flex-1">
        <div className="text-sm font-semibold text-[#c6d4df] mb-1 group-hover:text-white transition-colors">{game.title}</div>
        <div className="text-[11px] text-[#8f98a0] mb-1.5">{game.framing}</div>
        <div className="text-xs text-[#a4d007] font-semibold">~{game.main_story}h</div>
      </div>
      <div className="text-[10px] text-[#66c0f4] self-end shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">view details →</div>
    </div>
  );
}