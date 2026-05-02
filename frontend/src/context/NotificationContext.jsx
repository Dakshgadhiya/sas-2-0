import React, { createContext, useState, useCallback } from 'react';

export const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  const addNotification = useCallback(
    (message, type = 'info', duration = 3000) => {
      const id = Date.now();
      const notification = {
        id,
        message,
        type, // 'success', 'error', 'info', 'warning'
        duration
      };

      setNotifications((prev) => [...prev, notification]);

      // Auto-remove notification after duration
      if (duration > 0) {
        setTimeout(() => {
          removeNotification(id);
        }, duration);
      }

      return id;
    },
    []
  );

  const removeNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((notif) => notif.id !== id));
  }, []);

  const showSuccess = useCallback(
    (message, duration = 3000) => addNotification(message, 'success', duration),
    [addNotification]
  );

  const showError = useCallback(
    (message, duration = 4000) => addNotification(message, 'error', duration),
    [addNotification]
  );

  const showInfo = useCallback(
    (message, duration = 3000) => addNotification(message, 'info', duration),
    [addNotification]
  );

  const showWarning = useCallback(
    (message, duration = 3500) => addNotification(message, 'warning', duration),
    [addNotification]
  );

  const value = {
    notifications,
    addNotification,
    removeNotification,
    showSuccess,
    showError,
    showInfo,
    showWarning
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
