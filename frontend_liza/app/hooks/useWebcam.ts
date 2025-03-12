"use client";

import { useState, useCallback } from "react";

export default function useWebcam() {
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  let stream: MediaStream | null = null;

  const startCamera = async (videoElement: HTMLVideoElement) => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoElement) {
        videoElement.srcObject = stream;
      }
      setIsCameraActive(true);
      setError(null);
    } catch (err) {
      setError("Camera access denied or unavailable.");
      console.error(err);
    }
  };

  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    setIsCameraActive(false);
  }, []);

  const toggleCamera = (videoElement: HTMLVideoElement) => {
    if (isCameraActive) {
      stopCamera();
    } else {
      startCamera(videoElement);
    }
  };

  return {
    isCameraActive,
    error,
    startCamera,
    stopCamera,
    toggleCamera,
  };
}
