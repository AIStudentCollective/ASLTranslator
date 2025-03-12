"use client";

import { useState } from "react";
import Webcam from "@/components/Webcam";
import { translateASL } from "@/lib/translator";
import Link from "next/link";

export default function TranslatorPage() {
  const [translation, setTranslation] = useState("Waiting for input...");
  const [isScanning, setIsScanning] = useState(false);

  const handleScan = async () => {
    setIsScanning(true);
    setTranslation("Scanning...");

    setTimeout(async () => {
      const result = await translateASL(); // Fake translation logic
      setTranslation(result);
      setIsScanning(false);
    }, 2000);
  };

  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <h1 className="text-2xl font-bold mb-4">ASL Translator</h1>

      {/* Webcam Box */}
      <div className="w-[600px] h-[400px] bg-gray-800 flex items-center justify-center rounded-lg">
        <Webcam />
      </div>

      {/* Translation Output */}
      <div className="mt-4 w-[600px] p-4 bg-blue-100 rounded-lg text-center">
        <p className="text-lg font-semibold">Translation:</p>
        <p className="text-xl">{translation}</p>
      </div>

      {/* Start Scanning Button */}
      <button
        onClick={handleScan}
        disabled={isScanning}
        className={`mt-4 px-6 py-3 rounded-lg shadow-md ${
          isScanning ? "bg-gray-400 cursor-not-allowed" : "bg-blue-500 text-white"
        }`}
      >
        {isScanning ? "Scanning..." : "Start Scanning"}
      </button>

      {/* Back to Home */}
      <Link href="/" className="mt-4 text-blue-500 hover:underline">
        Back to Home
      </Link>
    </main>
  );
}
