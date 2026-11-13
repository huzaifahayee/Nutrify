import { useEffect, useRef, useState } from "react";

export default function CameraCapture({ onCapture, onClose }) {
  const video = useRef(null);
  const stream = useRef(null);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("This browser can't open the camera. Choose a photo instead.");
      return;
    }
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" }, audio: false })
      .then((s) => {
        if (cancelled) { s.getTracks().forEach((t) => t.stop()); return; }
        stream.current = s;
        video.current.srcObject = s;
        setReady(true);
      })
      .catch(() => setError("Camera access was blocked. Allow it in the browser, or choose a photo."));
    return () => {
      cancelled = true;
      stream.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const snap = () => {
    const v = video.current;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    canvas.getContext("2d").drawImage(v, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) onCapture(new File([blob], "camera.jpg", { type: "image/jpeg" }));
    }, "image/jpeg", 0.92);
  };

  return (
    <div className="photo">
      {error ? (
        <p className="cam-note">{error}</p>
      ) : (
        <video ref={video} autoPlay playsInline muted />
      )}
      <div className="photo-bar">
        <button className="btn quiet" onClick={onClose}>Cancel</button>
        {!error && <button className="btn primary" onClick={snap} disabled={!ready}>Take photo</button>}
      </div>
    </div>
  );
}
