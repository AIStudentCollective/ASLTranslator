"use client"; // Ensures it runs only on the client-side
import { useEffect, useRef, useState } from "react";
import io from "socket.io-client";

const SOCKET_URL = "http://localhost:8080"; // Change if backend runs on another port

export default function WebcamComponent() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [gesture, setGesture] = useState<string>("Loading...");
  const socket = useRef<any>(null);

  useEffect(() => {
    socket.current = io(SOCKET_URL);

    socket.current.on("prediction", (data: { gesture?: string; error?: string }) => {
      if (data.error) {
        setGesture(`Error: ${data.error}`);
      } else if (data.gesture) {
        setGesture(`Gesture: ${data.gesture}`);
      }
    });

    return () => {
      socket.current.disconnect();
    };
  }, []);

  useEffect(() => {
    const startWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, frameRate: { ideal: 10, max: 15 } },
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }

        processFrames();
      } catch (err) {
        setGesture(`Error accessing webcam: ${(err as Error).message}`);
      }
    };

    const processFrames = () => {
      if (!videoRef.current || !canvasRef.current) return;

      const canvas = canvasRef.current;
      const context = canvas.getContext("2d");
      const frameInterval = 100;
      let lastFrameTime = 0;

      const sendFrame = () => {
        const now = Date.now();
        if (now - lastFrameTime >= frameInterval) {
          if (videoRef.current?.readyState === videoRef.current?.HAVE_ENOUGH_DATA) {
            canvas.width = videoRef.current.videoWidth;
            canvas.height = videoRef.current.videoHeight;
            context?.drawImage(videoRef.current, 0, 0);

            const imageData = canvas.toDataURL("image/jpeg", 0.8).split(",")[1];
            socket.current.emit("frame", imageData);
            lastFrameTime = now;
          }
        }
        requestAnimationFrame(sendFrame);
      };

      sendFrame();
    };

    startWebcam();
  }, []);

  return (
    <div className="flex flex-col items-center">
      <h1 className="text-2xl font-bold mb-4">ASL Gesture Recognition</h1>
      <video ref={videoRef} autoPlay playsInline className="border-2 border-gray-700 w-[640px] h-[480px]" />
      <canvas ref={canvasRef} className="hidden" />
      <div className="mt-4 text-lg font-semibold bg-gray-100 p-2 rounded">{gesture}</div>
    </div>
  );
}