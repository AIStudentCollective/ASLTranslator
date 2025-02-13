import WebcamComponent from "./components/Webcam";

export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-[#FFF7E6] p-6">
      <WebcamComponent />
    </main>
  );
}