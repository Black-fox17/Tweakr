export const GA_TRACKING_ID = 'G-WP1R858VMT';

export const pageview = (url: string): void => {
  (window as any).gtag('config', GA_TRACKING_ID, {
    page_path: url,
  });
};