"use client";

import { useEffect, useRef } from 'react';

interface VisualizerProps {
  isRecording: boolean;
  analyser: AnalyserNode | null;
}

export default function Visualizer({ isRecording, analyser }: VisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>(null);

  useEffect(() => {
    if (!isRecording || !analyser || !canvasRef.current) {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationFrameRef.current = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const barWidth = (canvas.width / bufferLength) * 2.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        
        // Gradient effect
        const opacity = dataArray[i] / 255;
        ctx.fillStyle = `rgba(29, 185, 84, ${opacity * 0.8})`;
        
        // Draw rounded bars
        const r = barWidth / 2;
        const y = canvas.height - barHeight;
        const w = barWidth;
        const h = barHeight;
        
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + w - r, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + r);
        ctx.lineTo(x + w, y + h);
        ctx.lineTo(x, y + h);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
        ctx.fill();

        x += barWidth + 2;
      }
    };

    draw();

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [isRecording, analyser]);

  return (
    <canvas 
      ref={canvasRef} 
      width={160} 
      height={80} 
      className={`w-full h-full transition-opacity duration-500 ${isRecording ? 'opacity-100' : 'opacity-0'}`}
    />
  );
}
