"use client";

import React, { useState, useEffect, useRef } from 'react';
// Use type import for Socket and alias it to avoid potential conflicts
import { io, type Socket as SocketIOClientSocket } from 'socket.io-client';

const LiveTranslator: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [prediction, setPrediction] = useState<string>('Loading...');
  const [error, setError] = useState<string | null>(null);
  // Use the aliased type for the socket ref
  const socketRef = useRef<SocketIOClientSocket | null>(null);
  // Add new state for the letter buffer
  const [letterBuffer, setLetterBuffer] = useState<string>('');
  const lastFrameTimeRef = useRef<number>(0);
  const lastGestureRef = useRef<string>('');
  const lastUpdateTimeRef = useRef<number>(0);
  const lastBufferedLetterRef = useRef<string>('');
  const lastBufferAppendTimeRef = useRef<number>(0);

  const frameInterval = 100; // 10 FPS
  const BUFFER_APPEND_COOLDOWN = 700; // Milliseconds (0.7 seconds)

  // Function to reset the letter buffer
  const handleResetBuffer = () => {
    setLetterBuffer('');
  };

  // Function to add a space to the letter buffer
  const handleAddSpace = () => {
    setLetterBuffer(prevBuffer => prevBuffer + ' ');
  };

  useEffect(() => {
    // Initialize Socket.IO connection
    // Make sure your Flask server is running and accessible at this URL
    socketRef.current = io('http://localhost:8000');

    socketRef.current.on('connect', () => {
      console.log('Socket connected');
      setError(null);
    });

    socketRef.current.on('disconnect', () => {
      console.log('Socket disconnected');
      // Optionally, you could try to reconnect or notify the user
    });

    // Define an interface for the prediction data for clarity
    interface PredictionData {
      gesture?: string;
      error?: string;
      timestamp?: number; // Assuming timestamp is also sent
    }

    socketRef.current.on('prediction', (data: PredictionData) => {
      if (data.error) {
        console.error('Backend error:', data.error);
        setError(data.error);
      } else if (data.gesture) {
        const currentTime = Date.now();

        // Logic for updating the main prediction display (current sign)
        if (data.gesture !== lastGestureRef.current || currentTime - lastUpdateTimeRef.current > 500) {
          setPrediction(`Gesture: ${data.gesture}`);
          lastGestureRef.current = data.gesture;
          lastUpdateTimeRef.current = currentTime;
        }

        // Logic for appending to the letterBuffer
        // Append only if:
        // 1. It's a single uppercase letter
        // 2. It's different from the last letter *actually buffered*
        // 3. Enough time has passed since the last buffer append
        if (
          data.gesture.match(/^[A-Z]$/) &&
          data.gesture !== lastBufferedLetterRef.current &&
          currentTime - lastBufferAppendTimeRef.current > BUFFER_APPEND_COOLDOWN
        ) {
          setLetterBuffer(prevBuffer => prevBuffer + data.gesture);
          lastBufferedLetterRef.current = data.gesture;
          lastBufferAppendTimeRef.current = currentTime;
        }
        
        setError(null);
      }
    });

    // Request webcam access
    navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        frameRate: { ideal: 10, max: 15 }
      }
    }).then(stream => {
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch((playError: Error) => console.error("Error playing video:", playError));
        setError(null);
      }
    }).catch((err: Error) => {
      console.error('Error accessing webcam:', err);
      setError('Error accessing webcam: ' + err.message);
      setPrediction(''); // Clear prediction as webcam is not available
    });

    // Cleanup on component unmount
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Frame processing logic
  useEffect(() => {
    const processFrame = () => {
      if (!videoRef.current || !canvasRef.current || !socketRef.current || !socketRef.current.connected) {
        requestAnimationFrame(processFrame);
        return;
      }

      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');

      if (!context) {
        requestAnimationFrame(processFrame);
        return;
      }

      const now = Date.now();
      if (now - lastFrameTimeRef.current >= frameInterval) {
        if (video.readyState === video.HAVE_ENOUGH_DATA && video.videoWidth > 0) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          context.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);

          try {
            const imageData = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
            socketRef.current.emit('frame', imageData);
            lastFrameTimeRef.current = now;
          } catch (e) {
            console.error("Error converting canvas to DataURL:", e);
            // Potentially set an error state here if this happens frequently
          }
        }
      }
      requestAnimationFrame(processFrame);
    };

    const animationFrameId = requestAnimationFrame(processFrame);
    return () => cancelAnimationFrame(animationFrameId);
  }, [frameInterval]); // Rerun if frameInterval changes, though it's constant here

  return (
    // Apply styles from Webcam.tsx
    <div className="w-full h-full bg-black flex flex-col items-center justify-center relative text-white rounded-2xl overflow-hidden">
      {/* REC label from Webcam.tsx */}
      <div className="absolute top-4 left-4 flex items-center gap-2">
        <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
        <span className="text-sm font-medium">REC</span>
      </div>

      {/* Battery icon from Webcam.tsx - Placeholder, functionality can be added if needed */}
      <div className="absolute top-4 right-4 flex items-center gap-1">
        <div className="w-6 h-3 border border-white relative">
          <div className="w-[80%] h-full bg-white" /> 
        </div>
        <div className="w-1 h-1.5 bg-white" />
      </div>

      {/* Center crosshair from Webcam.tsx */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-6 h-0.5 bg-white opacity-50" />
        <div className="h-6 w-0.5 bg-white absolute opacity-50" />
      </div>

      {/* Video feed - styled as in Webcam.tsx */}
      <video
        ref={videoRef}
        className="absolute top-0 left-0 w-full h-full object-cover opacity-80" // Slightly increased opacity from Webcam.tsx for better visibility
        playsInline
        muted
        autoPlay // Ensure autoplay is present
      />
      {/* Hidden canvas for processing frames */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* New Recognition Buffer Display */}
      <div className="absolute bottom-32 left-1/2 -translate-x-1/2 w-auto max-w-[85%] bg-black/70 p-3 px-5 rounded-lg text-white text-2xl font-semibold tracking-wider min-h-[2.5em] flex items-center justify-center text-center">
        {letterBuffer || " "} {/* Show a space for min-height or style with min-height class */}
      </div>

      {/* Prediction overlay - styled as in Webcam.tsx */}
      <div className="absolute bottom-20 left-1/2 -translate-x-1/2 text-lg font-bold bg-black/60 px-4 py-2 rounded-md">
        {error ? `Error: ${error}` : prediction}
      </div>

      {/* Buttons for Reset and Space */}
      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex gap-4">
        <button 
          onClick={handleAddSpace}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg shadow-md transition-colors duration-150 ease-in-out"
        >
          Space
        </button>
        <button 
          onClick={handleResetBuffer}
          className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg shadow-md transition-colors duration-150 ease-in-out"
        >
          Reset
        </button>
      </div>

      {/* Footer info from Webcam.tsx - Placeholder, functionality can be added if needed */}
      <div className="absolute bottom-4 w-full px-6 flex justify-between text-xs font-mono text-gray-300">
        <span>{/* Placeholder for timestamp, e.g., stream duration */}</span>
        <span>{/* Placeholder for resolution, e.g., 640p */}</span>
        <span>FPS: {1000 / frameInterval}</span>
        <span>{/* Placeholder for ISO */}</span>
        <span>{/* Placeholder for f-stop */}</span>
      </div>
    </div>
  );
};

export default LiveTranslator; 