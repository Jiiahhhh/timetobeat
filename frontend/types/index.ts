export interface Game {
  title: string;
  cover_url: string | null;
  genres: string[];
  platforms: string[];
  rating: number;
  main_story: number;
  main_extra?: number;
  framing: string;
  steam_url?: string;
  trailer_youtube_id?: string;
  short_description?: string;
  difficulty?: number;
  difficulty_label?: string;
  trailer_valid?: boolean;
}

export interface Recommendation {
  primary: Game;
  alternatives: Game[];
  meta: {
    time_available_minutes: number;
    vibe: string;
    platform: string;
    modifier?: string;
    available_difficulties: number[];
  };
}
