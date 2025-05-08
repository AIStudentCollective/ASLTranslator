"use client";

import Link from "next/link";

export default function HowItWorksPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-between bg-[#fdf9f1] px-6 py-10 font-poppins text-gray-800">

      {/* Header */}
      <div className="w-full flex items-center justify-between max-w-5xl mx-auto mb-8">
        <div className="text-sm font-semibold">LOGO</div>
        <h1 className="text-xl tracking-wider font-bold text-center flex-1 -ml-8">
          ASL TRANSLATOR
        </h1>
        <div className="w-14" />
      </div>

      {/* Content Box */}
      <div className="bg-white border border-gray-300 shadow-soft rounded-2xl p-10 max-w-3xl w-full text-center space-y-8">
        <h2 className="text-2xl font-semibold uppercase tracking-wide">How it Works</h2>

        <p className="text-base text-gray-700">
          Our ASL Translator uses your webcam and a real-time machine learning pipeline to translate American Sign Language (ASL) gestures into written text. Here’s what’s happening behind the curtain:
        </p>

        <div className="text-left text-base text-gray-800 space-y-4">
          <p><strong>1. Camera Access:</strong> With your permission, we securely access your webcam. No video data is stored — everything is processed live in your browser.</p>
          <p><strong>2. Frame Capture:</strong> Our app captures images from your webcam at short intervals and compresses them for efficient transmission.</p>
          <p><strong>3. Real-Time Communication:</strong> Using WebSockets (Socket.IO), frames are streamed to our backend in real time, allowing instant inference.</p>
          <p><strong>4. Gesture Prediction:</strong> A trained machine learning model (based on hand keypoint recognition) analyzes each frame and identifies the most likely ASL gesture.</p>
          <p><strong>5. Live Feedback:</strong> The prediction is returned immediately and displayed on-screen, helping users communicate effectively without speaking.</p>
        </div>

        <p className="text-sm text-gray-600">
          Our system supports the ASL alphabet and select dynamic gestures, and we’re continuously expanding support. This tool is ideal for real-time learning, communication, and accessibility.
        </p>

        <p className="text-sm text-gray-500">
          Built with privacy in mind — no data is stored, and all predictions happen in a secure, low-latency environment.
        </p>

        <Link href="/" className="inline-block">
          <button className="bg-[#cfdffb] hover:bg-[#b3cffa] transition text-black px-6 py-3 rounded-md text-base font-medium shadow-md">
            Launch Translator
          </button>
        </Link>
      </div>

      {/* Footer */}
      <footer className="mt-16 pt-10 text-xs text-gray-500 w-full max-w-xl mx-auto flex justify-between">
        <span>Privacy Policy</span>
        <span>Terms</span>
        <span>About</span>
        <span>Feedback</span>
      </footer>
    </main>
  );
}
