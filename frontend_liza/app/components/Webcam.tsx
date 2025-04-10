export default function Webcam() {
  return (
    <div className="w-full aspect-video bg-gray-700 flex flex-col items-center justify-center rounded-lg relative">
      <p className="text-white absolute top-4 text-sm">Scanning ASL gestures...</p>
      
      <div className="w-12 h-12 rounded-full border-4 border-white bg-gray-700 flex items-center justify-center mt-4">
        <div className="w-4 h-4 rounded-full bg-white"></div>
      </div>
    </div>
  );
}
