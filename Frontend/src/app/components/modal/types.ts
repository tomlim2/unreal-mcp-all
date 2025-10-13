import { ReactNode } from 'react';

// Base modal configuration
export interface BaseModalConfig {
  id?: string;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  closable?: boolean;
  backdrop?: boolean;
  onClose?: () => void;
}

// Alert modal types
export type AlertType = 'success' | 'error' | 'warning' | 'info';

export interface AlertModalConfig extends BaseModalConfig {
  type: AlertType;
  title: string;
  message: string;
  buttonText?: string;
  autoClose?: number; // milliseconds
  onConfirm?: () => void;
}

// Confirm modal types
export type ConfirmVariant = 'default' | 'danger';

export interface ConfirmModalConfig extends BaseModalConfig {
  title: string;
  message: string;
  variant?: ConfirmVariant;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
}

// Form modal types
export interface FormModalConfig<T = unknown> extends BaseModalConfig {
  title: string;
  component: ReactNode;
  onSubmit?: (data: T) => void | Promise<void>;
  submitText?: string;
  cancelText?: string;
  loading?: boolean;
}

// Image modal types
export interface ImageModalConfig extends BaseModalConfig {
  src: string;
  alt: string;
  downloadable?: boolean;
  downloadFilename?: string;
  caption?: string;
}

// Loading modal types
export interface LoadingModalConfig extends Omit<BaseModalConfig, 'closable' | 'backdrop'> {
  message: string;
  progress?: number; // 0-100
  cancellable?: boolean;
  onCancel?: () => void;
}

// Settings modal types
export interface SettingsTab {
  id: string;
  label: string;
  component: ReactNode;
}

export interface SettingsModalConfig<T = unknown> extends BaseModalConfig {
  title: string;
  tabs: SettingsTab[];
  defaultTab?: string;
  onSave?: (data: T) => void | Promise<void>;
  onReset?: () => void;
}

// Custom modal types
export interface CustomModalConfig extends BaseModalConfig {
  component: ReactNode;
  title?: string;
  footer?: ReactNode;
}

// Image Generation modal types
export interface ReferenceImageUpload {
  file: File;
  preview?: string;
}

export interface ReferenceImageData {
  data: string; // base64 data URI
  mime_type: string;
}

export interface ImageGenerationData {
  prompt: string; // Single unified prompt
  targetImageUid?: string; // Optional: use existing screenshot
  mainImageData?: ReferenceImageData; // Optional: user-uploaded main image
  referenceImageData?: ReferenceImageData[]; // Reference images for style
}

export interface ImageGenerationModalConfig extends BaseModalConfig {
  sessionId: string; // Required: must have active session
  onSubmit: (data: ImageGenerationData) => void | Promise<void>;
  onClose?: (data?: ImageGenerationData) => void;
}

// Modal state types
export type ModalType =
  | 'alert'
  | 'confirm'
  | 'form'
  | 'image'
  | 'loading'
  | 'settings'
  | 'custom'
  | 'image-generation';

export type ModalState =
  | {
      id: string;
      type: 'alert';
      config: AlertModalConfig;
      resolve?: (value: unknown) => void;
      reject?: (reason: unknown) => void;
    }
  | {
      id: string;
      type: 'confirm';
      config: ConfirmModalConfig;
      resolve?: (value: unknown) => void;
      reject?: (reason: unknown) => void;
    }
  | {
      id: string;
      type: 'form';
      config: FormModalConfig;
      resolve?: (value: unknown) => void;
      reject?: (reason: unknown) => void;
    }
  | {
      id: string;
      type: 'image';
      config: ImageModalConfig;
      resolve?: (value: unknown) => void;
      reject?: (reason: unknown) => void;
    }
  | {
      id: string;
      type: 'loading';
      config: LoadingModalConfig;
      resolve?: (value: unknown) => void;
      reject?: (reason: unknown) => void;
    }
  | {
      id: string;
      type: 'settings';
      config: SettingsModalConfig;
      resolve?: (value: unknown) => void;
      reject?: (reason: unknown) => void;
    }
  | {
      id: string;
      type: 'custom';
      config: CustomModalConfig;
      resolve?: (value: unknown) => void;
      reject?: (reason: unknown) => void;
    }
  | {
      id: string;
      type: 'image-generation';
      config: ImageGenerationModalConfig;
      resolve?: (value: unknown) => void;
      reject?: (reason: unknown) => void;
    };

// Modal context types
export interface ModalContextType {
  modals: ModalState[];
  showAlert: (config: Omit<AlertModalConfig, 'type'> & { type: AlertType }) => Promise<void>;
  showConfirm: (config: Omit<ConfirmModalConfig, 'onConfirm'> & { onConfirm?: () => void | Promise<void> }) => Promise<boolean>;
  showForm: <T = unknown>(config: FormModalConfig<T>) => Promise<T | undefined>;
  showImage: (config: ImageModalConfig) => void;
  showLoading: (config: LoadingModalConfig) => { close: () => void; updateProgress: (progress: number) => void };
  showSettings: <T = unknown>(config: SettingsModalConfig<T>) => Promise<T | undefined>;
  showModal: (config: CustomModalConfig) => void;
  showImageGeneration: (config: ImageGenerationModalConfig) => Promise<ImageGenerationData | null>;
  closeModal: (id: string) => void;
  closeAll: () => void;
}

// Modal hook return type
export type UseModalReturn = Omit<ModalContextType, 'modals'>;