"use client";
import Link from "next/link";

export default function Header() {
  return (
    <header className="w-full px-6 py-4 flex items-center justify-between bg-[#fdf9f1]">
      <div className="text-sm font-semibold text-black">LOGO</div>

      <h1 className="text-3xl font-semibold text-center text-black flex-1 -ml-8">
        ASL TRANSLATOR
      </h1>

      <Link
        href="/how-it-works"
        className="text-sm text-black font-semibold hover:underline transition"
      >
        How it Works
      </Link>
    </header>

  );
}
