'use client';

import { createPortal } from 'react-dom';
import { useEffect } from 'react';
import { ModalState } from './types';
import ModalOverlay from './ModalOverlay';
import AlertModal from './AlertModal';
import ConfirmModal from './ConfirmModal';
import FormModal from './FormModal';
import ImageModal from './ImageModal';
import LoadingModal from './LoadingModal';
import SettingsModal from './SettingsModal';
import CustomModal from './CustomModal';

interface ModalProps {
  modalState: ModalState;
}

export default function Modal({ modalState }: ModalProps) {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  const renderModalContent = () => {
    switch (modalState.type) {
      case 'alert':
        return <AlertModal config={modalState.config} />;
      case 'confirm':
        return <ConfirmModal config={modalState.config} />;
      case 'form':
        return <FormModal config={modalState.config} />;
      case 'image':
        return <ImageModal config={modalState.config} />;
      case 'loading':
        return <LoadingModal config={modalState.config} />;
      case 'settings':
        return <SettingsModal config={modalState.config} />;
      case 'custom':
        return <CustomModal config={modalState.config} />;
      default:
        return null;
    }
  };

  return createPortal(
    <ModalOverlay
      size={modalState.config.size}
      closable={modalState.config.closable}
      backdrop={modalState.config.backdrop}
      onClose={modalState.config.onClose}
    >
      {renderModalContent()}
    </ModalOverlay>,
    document.body
  );
}