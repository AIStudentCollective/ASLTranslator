"use client";
import Link from "next/link";

export default function Header() {
  return (
    <header className="w-full px-6 py-4 flex items-center justify-between bg-[#fdf9f1]">
      <div className="text-sm font-medium">LOGO</div>

      <h1 className="text-lg font-semibold text-center flex-1 -ml-8">
        ASL TRANSLATOR
      </h1>

      <Link
        href="/how-it-works"
        className="text-sm text-gray-700 hover:underline transition"
      >
        How it Works
      </Link>
    </header>
  );
}
