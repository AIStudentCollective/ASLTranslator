"use client";

import { useEffect, useRef } from "react";
import useWebcam from "../hooks/usewebcam";
import { Button } from "./Button";

export default function Webcam() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const { startCamera, stopCamera, isCameraActive, toggleCamera, error } = useWebcam();

  useEffect(() => {
    if (isCameraActive && videoRef.current) {
      startCamera(videoRef.current);
    } else {
      stopCamera();
    }
    return () => stopCamera(); // Cleanup when unmounting
  }, [isCameraActive]);

  return (
    <div className="w-full h-full flex flex-col items-center justify-center bg-gray-800 rounded-lg p-4">
      {error ? (
        <p className="text-red-500 mb-4">Error: {error}</p>
      ) : (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="w-full h-full rounded-lg"
        />
      )}
      <Button onClick={() => toggleCamera(videoRef.current!)} className="mt-4">
        {isCameraActive ? "Stop Camera" : "Start Camera"}
      </Button>
    </div>
  );
}
