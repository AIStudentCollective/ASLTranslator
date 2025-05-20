"use client";

import Header from "./components/Header";
import LiveTranslator from "./components/LiveTranslator";

export default function Home() {
  return (
    <>
      <Header />
      <main className="min-h-screen bg-[#fdf9f1] px-4 py-10 flex flex-col items-center justify-start">
        <div className="w-full max-w-4xl flex flex-col items-center gap-6">
          
          <div className="w-full max-w-6xl h-[70vh] bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
            <LiveTranslator />
          </div>
        </div>
      </main>
    </>
  );
}
