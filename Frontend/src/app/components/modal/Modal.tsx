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
import ReferenceImagesModal from './ReferenceImagesModal';

interface ModalProps {
  modalState: ModalState;
}

export default function Modal({ modalState }: ModalProps) {
  useEffect(() => {
    // Save current scroll position
    const scrollY = window.scrollY;

    // Prevent body scroll without causing layout shift
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
    document.body.style.overflow = 'hidden';
    document.body.style.paddingRight = `${scrollbarWidth}px`;

    return () => {
      // Restore body scroll
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';

      // Restore scroll position
      window.scrollTo(0, scrollY);
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
      case 'reference-images':
        return <ReferenceImagesModal config={modalState.config} onClose={modalState.config.onClose} />;
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