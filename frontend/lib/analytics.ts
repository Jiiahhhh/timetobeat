/**
 * Extended window interface containing optional Umami analytics tracker.
 */
interface CustomWindow extends Window {
  umami?: {
    track: (name: string, data?: Record<string, string>) => void;
  };
}

/**
 * Tracks custom events using Umami Analytics.
 * Safely checks if window and umami tracking object are loaded before calling track.
 * 
 * @param name The name of the event to track.
 * @param data Optional event properties.
 */
export const trackEvent = (name: string, data?: Record<string, string>) => {
  if (typeof window !== "undefined") {
    const customWindow = window as unknown as CustomWindow;
    customWindow.umami?.track(name, data);
  }
};


