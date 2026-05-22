/**
 * Helper to track events using Umami Analytics.
 * Safely checks if window and umami tracker are available before tracking.
 */
interface CustomWindow extends Window {
  umami?: {
    track: (name: string, data?: Record<string, string>) => void;
  };
}

export const trackEvent = (name: string, data?: Record<string, string>) => {
  if (typeof window !== "undefined") {
    const customWindow = window as unknown as CustomWindow;
    customWindow.umami?.track(name, data);
  }
};

