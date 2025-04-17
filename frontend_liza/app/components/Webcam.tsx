"use client";

import { useEffect, useRef, useState } from "react";
import io from "socket.io-client"; // 👈 Default import

export default function Webcam() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [socket, setSocket] = useState<any>(null);
  const [prediction, setPrediction] = useState("Loading...");

  // Connect to Socket.IO server
  useEffect(() => {
    const socketInstance = io("http://localhost:3000"); // Change to your backend URL
    setSocket(socketInstance);

    socketInstance.on("prediction", (data: any) => {
      if (data.error) {
        setPrediction(`Error: ${data.error}`);
      } else {
        setPrediction(`Gesture: ${data.gesture}`);
      }
    });

    return () => 
      socketInstance.disconnect();
  }, []);

  // Access webcam
  useEffect(() => {
    const setupWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            frameRate: { ideal: 10, max: 15 },
          },
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Error accessing webcam:", err);
        setPrediction("Error accessing webcam");
      }
    };

    setupWebcam();
  }, []);

  // Send frames
  useEffect(() => {
    const sendFrame = () => {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      if (
        canvas &&
        video &&
        socket &&
        video.readyState === video.HAVE_ENOUGH_DATA
      ) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        ctx?.drawImage(video, 0, 0);

        const base64 = canvas.toDataURL("image/jpeg", 0.8).split(",")[1];
        socket.emit("frame", base64);
      }
      requestAnimationFrame(sendFrame);
    };

    requestAnimationFrame(sendFrame);
  }, [socket]);

  return (
    <div className="w-full h-full bg-black flex flex-col items-center justify-center relative text-white rounded-2xl overflow-hidden">

      {/* REC label */}
      <div className="absolute top-4 left-4 flex items-center gap-2">
        <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
        <span className="text-sm font-medium">REC</span>
      </div>

      {/* Battery icon */}
      <div className="absolute top-4 right-4 flex items-center gap-1">
        <div className="w-6 h-3 border border-white relative">
          <div className="w-[80%] h-full bg-white" />
        </div>
        <div className="w-1 h-1.5 bg-white" />
      </div>

      {/* Center crosshair */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-6 h-0.5 bg-white" />
        <div className="h-6 w-0.5 bg-white absolute" />
      </div>

      {/* Video feed */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        className="absolute top-0 left-0 w-full h-full object-cover opacity-60"
      />
      <canvas ref={canvasRef} className="hidden" />

      {/* Prediction overlay */}
      <div className="absolute bottom-20 left-1/2 -translate-x-1/2 text-lg font-bold bg-black/60 px-4 py-2 rounded-md">
        {prediction}
      </div>

      {/* Footer info (timestamp + specs) */}
      <div className="absolute bottom-4 w-full px-6 flex justify-between text-xs font-mono text-gray-300">
        <span>00:02:18</span>
        <span>1080p</span>
        <span>FPS: 30</span>
        <span>ISO: 200</span>
        <span>f/2</span>
      </div>
    </div>
  );
}
