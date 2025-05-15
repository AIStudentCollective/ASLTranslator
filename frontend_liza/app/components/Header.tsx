"use client";
import Link from "next/link";
import Image from "next/image";

export default function Header() {
  return (
    <header className="w-full px-6 py-4 flex items-center justify-between bg-[#fdf9f1]">
      {/* LOGO IMAGE */}
      <div className="flex items-center">
        <Image
          src="/assets/SignBridgeLogo.png"
          alt="SignBridge logo"
          width={90}
          height={90}
          className="mr-2"
        />
      </div>

      {/* TITLE */}
      <h1 className="text-3xl font-semibold text-center text-black flex-1 -ml-8">
        SIGN BRIDGE
      </h1>

      {/* LINK */}
      <Link
        href="/how-it-works"
        className="text-sm text-black font-semibold hover:underline transition"
      >
        How it Works
      </Link>
    </header>
  );
}
