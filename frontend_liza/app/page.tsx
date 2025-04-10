"use client";

import { useRef, useEffect } from "react";
import Header from "./components/Header";

export default function Home() {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Camera error:", err);
      }
    };

    startCamera();

    return () => {
      if (videoRef.current?.srcObject) {
        (videoRef.current.srcObject as MediaStream)
          .getTracks()
          .forEach((track) => track.stop());
      }
    };
  }, []);

  return (
    <>
      <Header />
      <main className="min-h-screen bg-[#fdf9f1] text-black p-8 flex flex-col items-center">
        <div className="flex gap-8 w-full max-w-5xl">
          <div className="flex-1 bg-gray-800 rounded-lg p-2">
            <video ref={videoRef} autoPlay playsInline className="w-full h-full rounded-lg" />
          </div>
          <div className="flex flex-col items-center gap-4 justify-center">
            <button className="bg-blue-200 text-black font-medium py-2 px-4 rounded-md shadow hover:bg-blue-300 transition">
              Launch Translator
            </button>
            <p className="text-sm text-center text-gray-700">
              Position your hands within the camera frame for translation
            </p>
          </div>
        </div>
      </main>
    </>
  );
}
