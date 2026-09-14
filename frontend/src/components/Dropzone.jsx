import { useRef, useState } from "react";
import "./Dropzone.css";

export default function Dropzone({ file, onFileSelected }) {
  const inputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);

  function handleFiles(fileList) {
    const picked = fileList?.[0];
    if (picked) onFileSelected(picked);
  }

  return (
    <div
      className={`dropzone ${dragActive ? "dropzone--active" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragActive(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        className="dropzone__input"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {file ? (
        <div className="dropzone__file">
          <span className="dropzone__file-name">{file.name}</span>
          <span className="dropzone__file-hint">
            Archivo cargado. La extracción automática del texto aún no está disponible: pega el
            contenido en el campo de abajo.
          </span>
        </div>
      ) : (
        <>
          <p className="dropzone__title">Arrastra un archivo aquí o haz clic para buscarlo</p>
          <p className="dropzone__hint">PDF, DOC, DOCX o TXT</p>
        </>
      )}
    </div>
  );
}
