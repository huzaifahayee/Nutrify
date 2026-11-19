import { useRef, useState } from "react";

export default function UploadZone({ onFile, onCamera }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);

  const pick = (files) => {
    const f = files && files[0];
    if (f) onFile(f);
  };

  return (
    <div
      className={`drop${over ? " over" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); pick(e.dataTransfer.files); }}
    >
      <h2>Drop a <em>photo</em> here</h2>
      <p>Or pick one from your device. One dish in the frame works best.</p>
      <div className="actions">
        <button className="btn primary" onClick={() => input.current.click()}>Choose photo</button>
        <button className="btn" onClick={onCamera}>Use camera</button>
      </div>
      <input
        ref={input}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => { pick(e.target.files); e.target.value = ""; }}
      />
    </div>
  );
}
