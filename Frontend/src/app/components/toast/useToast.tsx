'use client';

import { useToastContext } from './ToastProvider';
import { UseToastReturn } from './types';

export default function useToast(): UseToastReturn {
  const context = useToastContext();
  
  return {
    showToast: context.showToast,
    showSuccess: context.showSuccess,
    showError: context.showError,
    showWarning: context.showWarning,
    showInfo: context.showInfo,
    dismissToast: context.dismissToast,
    dismissAll: context.dismissAll
  };
}