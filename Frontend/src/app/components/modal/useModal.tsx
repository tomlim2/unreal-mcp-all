'use client';

import { useModalContext } from './ModalProvider';
import { UseModalReturn } from './types';

export default function useModal(): UseModalReturn {
  const context = useModalContext();
  
  return {
    showAlert: context.showAlert,
    showConfirm: context.showConfirm,
    showForm: context.showForm,
    showImage: context.showImage,
    showLoading: context.showLoading,
    showSettings: context.showSettings,
    showModal: context.showModal,
    closeModal: context.closeModal,
    closeAll: context.closeAll
  };
}