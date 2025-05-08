import { useEffect, useRef, useState } from "react";
import io from "socket.io-client";
import type { Socket } from "socket.io-client/dist/socket";

// Define the shape of the prediction data
interface PredictionData {
  gesture: string;
  error?: string;
}

// Define the return type
interface UseWebcamSocketResult {
  socket: Socket | null;
  prediction: string;
  sendFrame: (base64Image: string) => void;
}

export default function useWebcamSocket(serverUrl: string): UseWebcamSocketResult {
  const socketRef = useRef<Socket | null>(null);
  const [prediction, setPrediction] = useState("Loading...");

  useEffect(() => {
    const socket: Socket = io(serverUrl, {
      transports: ["websocket"], // optional but useful for stability
    });

    socketRef.current = socket;

    // Listen for prediction events
    socket.on("prediction", (data: PredictionData) => {
      if (data.error) {
        setPrediction(`Error: ${data.error}`);
      } else {
        setPrediction(`Gesture: ${data.gesture}`);
      }
    });

    // Cleanup on unmount
    return () => {
      socket.disconnect();
    };
  }, [serverUrl]);

  // Frame sending function
  const sendFrame = (base64Image: string) => {
    if (socketRef.current && socketRef.current.connected) {
      socketRef.current.emit("frame", base64Image);
    }
  };

  return {
    socket: socketRef.current,
    prediction,
    sendFrame,
  };
}
