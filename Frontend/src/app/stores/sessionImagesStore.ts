import { create } from 'zustand';

interface SessionImageInfo {
  uid: string;
  url: string;
  thumbnail_url: string;
  filename: string;
  timestamp: string;
  command: string;
}

interface LatestImageInfo {
  uid: string | null;
  filename: string | null;
  thumbnail_url: string | null;
  available: boolean;
}

interface SessionImagesState {
  // Cache for session images by sessionId
  sessionImagesCache: Record<string, SessionImageInfo[]>;
  latestImageCache: Record<string, LatestImageInfo>;

  // Actions
  setSessionImages: (sessionId: string, images: SessionImageInfo[]) => void;
  setLatestImage: (sessionId: string, image: LatestImageInfo) => void;
  getSessionImages: (sessionId: string) => SessionImageInfo[] | undefined;
  getLatestImage: (sessionId: string) => LatestImageInfo | undefined;
  invalidateSession: (sessionId: string) => void;
  clearAll: () => void;
}

export const useSessionImagesStore = create<SessionImagesState>((set, get) => ({
  sessionImagesCache: {},
  latestImageCache: {},

  setSessionImages: (sessionId, images) =>
    set((state) => ({
      sessionImagesCache: {
        ...state.sessionImagesCache,
        [sessionId]: images,
      },
    })),

  setLatestImage: (sessionId, image) =>
    set((state) => ({
      latestImageCache: {
        ...state.latestImageCache,
        [sessionId]: image,
      },
    })),

  getSessionImages: (sessionId) => get().sessionImagesCache[sessionId],

  getLatestImage: (sessionId) => get().latestImageCache[sessionId],

  invalidateSession: (sessionId) =>
    set((state) => {
      const { [sessionId]: _, ...restImages } = state.sessionImagesCache;
      const { [sessionId]: __, ...restLatest } = state.latestImageCache;
      return {
        sessionImagesCache: restImages,
        latestImageCache: restLatest,
      };
    }),

  clearAll: () =>
    set({
      sessionImagesCache: {},
      latestImageCache: {},
    }),
}));
