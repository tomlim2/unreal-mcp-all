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
export interface FormModalConfig extends BaseModalConfig {
  title: string;
  component: ReactNode;
  onSubmit?: (data: any) => void | Promise<void>;
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

export interface SettingsModalConfig extends BaseModalConfig {
  title: string;
  tabs: SettingsTab[];
  defaultTab?: string;
  onSave?: (data: any) => void | Promise<void>;
  onReset?: () => void;
}

// Custom modal types
export interface CustomModalConfig extends BaseModalConfig {
  component: ReactNode;
  title?: string;
  footer?: ReactNode;
}

// Reference Images modal types
export interface ReferenceImageUpload {
  file: File;
  purpose: 'style' | 'color' | 'composition'; // Legacy field, not used
  preview?: string;
}

export interface ReferenceImageData {
  data: string; // base64 data URI
  mime_type: string;
}

export interface ReferenceImagesData {
  prompt: string; // Keep for backward compatibility
  main_prompt?: string; // Optional main transformation prompt
  reference_prompts?: string[]; // Individual prompts per image
  targetImageUid: string;
  referenceImageData?: ReferenceImageData[]; // Direct image data (new approach)
}

export interface ReferenceImagesModalConfig extends BaseModalConfig {
  sessionId: string;
  onSubmit: (data: ReferenceImagesData) => void | Promise<void>;
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
  | 'reference-images';

export interface ModalState {
  id: string;
  type: ModalType;
  config: AlertModalConfig | ConfirmModalConfig | FormModalConfig | ImageModalConfig | LoadingModalConfig | SettingsModalConfig | CustomModalConfig | ReferenceImagesModalConfig;
  resolve?: (value: any) => void;
  reject?: (reason: any) => void;
}

// Modal context types
export interface ModalContextType {
  modals: ModalState[];
  showAlert: (config: Omit<AlertModalConfig, 'type'> & { type: AlertType }) => Promise<void>;
  showConfirm: (config: Omit<ConfirmModalConfig, 'onConfirm'> & { onConfirm?: () => void | Promise<void> }) => Promise<boolean>;
  showForm: (config: FormModalConfig) => Promise<any>;
  showImage: (config: ImageModalConfig) => void;
  showLoading: (config: LoadingModalConfig) => { close: () => void; updateProgress: (progress: number) => void };
  showSettings: (config: SettingsModalConfig) => Promise<any>;
  showModal: (config: CustomModalConfig) => void;
  showReferenceImages: (config: ReferenceImagesModalConfig) => Promise<ReferenceImagesData | null>;
  closeModal: (id: string) => void;
  closeAll: () => void;
}

// Modal hook return type
export type UseModalReturn = Omit<ModalContextType, 'modals'>;