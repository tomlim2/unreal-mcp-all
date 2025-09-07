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

// Modal state types
export type ModalType = 
  | 'alert'
  | 'confirm'
  | 'form'
  | 'image'
  | 'loading'
  | 'settings'
  | 'custom';

export interface ModalState {
  id: string;
  type: ModalType;
  config: AlertModalConfig | ConfirmModalConfig | FormModalConfig | ImageModalConfig | LoadingModalConfig | SettingsModalConfig | CustomModalConfig;
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
  closeModal: (id: string) => void;
  closeAll: () => void;
}

// Modal hook return type
export type UseModalReturn = Omit<ModalContextType, 'modals'>;