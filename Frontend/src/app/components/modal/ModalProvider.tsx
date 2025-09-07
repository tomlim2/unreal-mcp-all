'use client';

import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { 
  ModalContextType, 
  ModalState, 
  AlertModalConfig, 
  ConfirmModalConfig, 
  FormModalConfig,
  ImageModalConfig,
  LoadingModalConfig,
  SettingsModalConfig,
  CustomModalConfig,
  AlertType
} from './types';
import Modal from './Modal';

// Create the modal context
const ModalContext = createContext<ModalContextType | null>(null);

// Custom hook to use modal context
export const useModalContext = () => {
  const context = useContext(ModalContext);
  if (!context) {
    throw new Error('useModalContext must be used within a ModalProvider');
  }
  return context;
};

// Modal Provider Props
interface ModalProviderProps {
  children: ReactNode;
}

// Generate unique ID for modals
const generateId = () => `modal_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export default function ModalProvider({ children }: ModalProviderProps) {
  const [modals, setModals] = useState<ModalState[]>([]);

  // Close modal by ID
  const closeModal = useCallback((id: string) => {
    setModals(prev => {
      const modal = prev.find(m => m.id === id);
      if (modal && modal.resolve) {
        // Resolve with false for confirm modals, undefined for others
        modal.resolve(modal.type === 'confirm' ? false : undefined);
      }
      return prev.filter(m => m.id !== id);
    });
  }, []);

  // Close all modals
  const closeAll = useCallback(() => {
    setModals(prev => {
      prev.forEach(modal => {
        if (modal.resolve) {
          modal.resolve(modal.type === 'confirm' ? false : undefined);
        }
      });
      return [];
    });
  }, []);

  // Show alert modal
  const showAlert = useCallback((config: Omit<AlertModalConfig, 'type'> & { type: AlertType }): Promise<void> => {
    return new Promise((resolve) => {
      const id = generateId();
      const modalState: ModalState = {
        id,
        type: 'alert',
        config: { ...config, onClose: () => closeModal(id) },
        resolve
      };
      setModals(prev => [...prev, modalState]);
    });
  }, [closeModal]);

  // Show confirm modal
  const showConfirm = useCallback((config: Omit<ConfirmModalConfig, 'onConfirm'> & { onConfirm?: () => void | Promise<void> }): Promise<boolean> => {
    return new Promise((resolve) => {
      const id = generateId();
      const modalState: ModalState = {
        id,
        type: 'confirm',
        config: {
          ...config,
          onConfirm: async () => {
            if (config.onConfirm) {
              await config.onConfirm();
            }
            resolve(true);
            closeModal(id);
          },
          onCancel: () => {
            if (config.onCancel) {
              config.onCancel();
            }
            resolve(false);
            closeModal(id);
          },
          onClose: () => {
            resolve(false);
            closeModal(id);
          }
        },
        resolve
      };
      setModals(prev => [...prev, modalState]);
    });
  }, [closeModal]);

  // Show form modal
  const showForm = useCallback((config: FormModalConfig): Promise<any> => {
    return new Promise((resolve, reject) => {
      const id = generateId();
      const modalState: ModalState = {
        id,
        type: 'form',
        config: {
          ...config,
          onSubmit: async (data: any) => {
            try {
              if (config.onSubmit) {
                await config.onSubmit(data);
              }
              resolve(data);
              closeModal(id);
            } catch (error) {
              reject(error);
            }
          },
          onClose: () => {
            resolve(undefined);
            closeModal(id);
          }
        },
        resolve,
        reject
      };
      setModals(prev => [...prev, modalState]);
    });
  }, [closeModal]);

  // Show image modal
  const showImage = useCallback((config: ImageModalConfig): void => {
    const id = generateId();
    const modalState: ModalState = {
      id,
      type: 'image',
      config: { ...config, onClose: () => closeModal(id) }
    };
    setModals(prev => [...prev, modalState]);
  }, [closeModal]);

  // Show loading modal
  const showLoading = useCallback((config: LoadingModalConfig) => {
    const id = generateId();
    const modalState: ModalState = {
      id,
      type: 'loading',
      config: {
        ...config,
        onCancel: config.cancellable ? () => {
          if (config.onCancel) {
            config.onCancel();
          }
          closeModal(id);
        } : undefined
      }
    };
    setModals(prev => [...prev, modalState]);

    return {
      close: () => closeModal(id),
      updateProgress: (progress: number) => {
        setModals(prev => prev.map(modal => 
          modal.id === id 
            ? { ...modal, config: { ...modal.config, progress } as LoadingModalConfig }
            : modal
        ));
      }
    };
  }, [closeModal]);

  // Show settings modal
  const showSettings = useCallback((config: SettingsModalConfig): Promise<any> => {
    return new Promise((resolve) => {
      const id = generateId();
      const modalState: ModalState = {
        id,
        type: 'settings',
        config: {
          ...config,
          onSave: async (data: any) => {
            if (config.onSave) {
              await config.onSave(data);
            }
            resolve(data);
            closeModal(id);
          },
          onClose: () => {
            resolve(undefined);
            closeModal(id);
          }
        },
        resolve
      };
      setModals(prev => [...prev, modalState]);
    });
  }, [closeModal]);

  // Show custom modal
  const showModal = useCallback((config: CustomModalConfig): void => {
    const id = generateId();
    const modalState: ModalState = {
      id,
      type: 'custom',
      config: { ...config, onClose: () => closeModal(id) }
    };
    setModals(prev => [...prev, modalState]);
  }, [closeModal]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && modals.length > 0) {
        const topModal = modals[modals.length - 1];
        if (topModal.config.closable !== false) {
          closeModal(topModal.id);
        }
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [modals, closeModal]);

  const contextValue: ModalContextType = {
    modals,
    showAlert,
    showConfirm,
    showForm,
    showImage,
    showLoading,
    showSettings,
    showModal,
    closeModal,
    closeAll
  };

  return (
    <ModalContext.Provider value={contextValue}>
      {children}
      {/* Render all active modals */}
      {modals.map((modal) => (
        <Modal key={modal.id} modalState={modal} />
      ))}
    </ModalContext.Provider>
  );
}